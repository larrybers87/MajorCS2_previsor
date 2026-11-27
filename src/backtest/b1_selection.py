"""Seleção e avaliação do B1 contra o B0 (protocolo pré-registrado).

Uso::

    python -m backtest.b1_selection

Grava ``data/processed/b1_params.json`` e ``docs/b1_avaliacao.md``. Hiperparâmetros são
escolhidos só no desenvolvimento; o teste é calculado depois, só para o escolhido.
"""

from __future__ import annotations

import itertools
import json
from dataclasses import asdict

import numpy as np
import pandas as pd

from ingest.vrs import PROJECT_ROOT
from ingest.vrs_matches import MATCHES_PATH, WINDOW_START
from models.b0 import features, fit_beta, series_win_probability
from models.ratings import (
    EloConfig,
    Game,
    GlickoConfig,
    Side,
    TeamRegistry,
    build_system,
)
from sim.singapore2026 import DATA_CUTOFF

from .b0_calibration import in_population, rated_matches
from .h10_format import select_b0
from .protocol import (
    favorite_calibration,
    paired_difference,
    period_mask,
    summarize,
    walk_forward,
)

PARAMS_PATH = PROJECT_ROOT / "data" / "processed" / "b1_params.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "b1_avaliacao.md"
RNG_SEED = 20261127


def grid() -> list[EloConfig | GlickoConfig]:
    elo = [
        EloConfig(s, k, h, m)
        for s, k, h, m in itertools.product(
            (0.0, 0.25, 0.5, 0.75), (10, 20, 30, 40, 60), (60, 90, 180, None), (1, 2)
        )
    ]
    glicko = [
        GlickoConfig(rd0, c, s)
        for rd0, c, s in itertools.product((200, 350), (10, 20, 40), (0.0, 0.5))
    ]
    return [*elo, *glicko]


def prepare(table: pd.DataFrame) -> tuple[pd.DataFrame, list, TeamRegistry]:
    """Todas as partidas antes do corte, em ordem, com os times identificados por elenco.

    Retorna a tabela ordenada, a lista ``[(dia, índices, partidas)]`` e o registro.
    """
    data = table[table["date"] < pd.Timestamp(DATA_CUTOFF)]
    data = data.sort_values(
        ["date", "team_a", "team_b", "roster_a", "roster_b"], kind="stable"
    ).reset_index(drop=True)
    registry = TeamRegistry()
    days = []
    for day, chunk in data.groupby("date", sort=True):
        games = []
        for row in chunk.itertuples():
            sides = []
            for name, roster, points in (
                (row.team_a, row.roster_a, row.points_a),
                (row.team_b, row.roster_b, row.points_b),
            ):
                players = frozenset(p.strip().casefold() for p in roster.split(",") if p.strip())
                team = registry.resolve(name, players)
                sides.append(Side(team, None if pd.isna(points) else float(points)))
            games.append(Game(sides[0], sides[1], bool(row.team_a_won)))
        days.append((day.date(), chunk.index.to_numpy(), games))
    return data, days, registry


def rating_differences(config, days: list, n: int):
    """``rating_a - rating_b`` antes do dia de cada partida; devolve também o sistema."""
    system = build_system(config)
    differences = np.empty(n)
    for day, index, games in days:
        differences[index] = system.process_day(day, games)
    return differences, system


def evaluation_mask(data: pd.DataFrame) -> np.ndarray:
    """Alvo: os dois times com pontos VRS e no top 100, dentro da janela."""
    ranked = _ranked(data)
    top = np.zeros(len(data), dtype=bool)
    top[ranked] = in_population(data[ranked], "top100")
    return top


def _ranked(data: pd.DataFrame) -> np.ndarray:
    """Partidas com rating VRS anterior dos dois lados, dentro da janela."""
    inside = (data["date"] >= pd.Timestamp(WINDOW_START)) & (
        data["date"] < pd.Timestamp(DATA_CUTOFF)
    )
    return (inside & data["points_a"].notna() & data["points_b"].notna()).to_numpy(bool)


def calibrated_walk_forward(
    data: pd.DataFrame, differences: np.ndarray, target: np.ndarray, period: str
) -> tuple[np.ndarray, list[float]]:
    """Probabilidade de série (forma Bo3) com beta ajustado em partidas anteriores."""
    x = differences / 100.0
    won = data["team_a_won"].to_numpy(bool)
    betas: list[float] = []

    def fit(train):
        betas.append(fit_beta(x[train], won[train], 3))
        return betas[-1]

    p = walk_forward(
        data["date"], period, target, fit,
        predict=lambda beta, test: series_win_probability(beta, x[test], 3),
    )  # fmt: skip
    return p, betas


def log_loss(p: np.ndarray, won: np.ndarray) -> float:
    q = np.clip(p, 1e-12, 1 - 1e-12)
    return float(-np.where(won, np.log(q), np.log1p(-q)).mean())


def analyze(table: pd.DataFrame, configs=None, seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    data, days, _ = prepare(table)
    target = evaluation_mask(data)
    won = data["team_a_won"].to_numpy(bool)
    dates = data["date"].to_numpy()
    dev = period_mask(data["date"], "dev") & target

    dev_scores = []
    for config in configs or grid():
        differences, _ = rating_differences(config, days, len(data))
        p, _ = calibrated_walk_forward(data, differences, target, "dev")
        dev_scores.append((log_loss(p[dev], won[dev]), config))
    dev_scores.sort(key=lambda item: item[0])
    best_dev, best = dev_scores[0]

    # B0: configuração escolhida no mesmo desenvolvimento.
    b0_config, _ = select_b0(rated_matches(data))
    train_b0 = np.zeros(len(data), dtype=bool)
    ranked = _ranked(data)
    train_b0[ranked] = in_population(data[ranked], b0_config["population"])
    x0 = np.zeros(len(data))
    x0[ranked] = features(
        data.loc[ranked, "points_a"].to_numpy(float),
        data.loc[ranked, "points_b"].to_numpy(float),
        b0_config["transform"],
    )

    def b0_walk(period):
        return walk_forward(
            data["date"], period, train_b0,
            fit=lambda train: fit_beta(x0[train], won[train], 3),
            predict=lambda beta, test: series_win_probability(beta, x0[test], 3),
        )  # fmt: skip

    # A partir daqui o teste é calculado, só para os modelos escolhidos.
    differences, _ = rating_differences(best, days, len(data))
    p1_test, monthly_betas = calibrated_walk_forward(data, differences, target, "test")
    p0_test = b0_walk("test")
    test = period_mask(data["date"], "test") & target
    p0_dev = b0_walk("dev")

    result = {
        "chosen": {"kind": type(best).__name__, **asdict(best)},
        "chosen_label": best.label,
        "dev": {
            "n": int(dev.sum()),
            "b1_log_loss": best_dev,
            "b0_log_loss": log_loss(p0_dev[dev], won[dev]),
            "top": [{"config": c.label, "log_loss": v} for v, c in dev_scores[:10]],
            "n_configs": len(dev_scores),
        },
        "b0_config": b0_config,
        "n_matches_history": int(len(data)),
        "test": {
            "first": str(data["date"][test].min().date()),
            "last": str(data["date"][test].max().date()),
            "b0": summarize(p0_test[test], won[test], dates[test], rng),
            "b1": summarize(p1_test[test], won[test], dates[test], rng),
            "b1_minus_b0": paired_difference(
                p1_test[test], p0_test[test], won[test], dates[test], rng
            ),
            "b1_calibration": favorite_calibration(p1_test[test], won[test]),
            "monthly_betas": monthly_betas,
        },
        # Calibração final (todas as partidas do alvo antes do corte), para uso no Major.
        "final_beta": fit_beta(differences[target] / 100.0, won[target], 3),
        "train_last": str(data["date"].max().date()),
    }
    upper = result["test"]["b1_minus_b0"]["log_loss_ci"][1]
    result["meets_statistical_criterion"] = bool(upper < 0)
    return result


def _ci(values) -> str:
    return f"[{values[0]:.4f}; {values[1]:.4f}]"


def render_report(r: dict) -> str:
    t = r["test"]
    d = t["b1_minus_b0"]
    lines = [
        "# B1 (Elo/Glicko) contra o B0",
        "",
        "Gerado por `python -m backtest.b1_selection` (não editar à mão). Protocolo em "
        "[protocolo_sessao_03.md](protocolo_sessao_03.md).",
        "",
        f"Histórico: {r['n_matches_history']} partidas até {r['train_last']}.",
        "",
        f"## Desenvolvimento ({r['dev']['n']} partidas, {r['dev']['n_configs']} configurações)",
        "",
        f"B0 ({r['b0_config']['population']}/{r['b0_config']['transform']}): log loss "
        f"{r['dev']['b0_log_loss']:.4f}. Dez melhores do B1:",
        "",
        "| Configuração | log loss |",
        "|---|---:|",
        *[f"| {row['config']} | {row['log_loss']:.4f} |" for row in r["dev"]["top"]],
        "",
        f"Escolhido: **{r['chosen_label']}**.",
        "",
        f"## Teste ({t['b1']['n']} partidas, {t['first']} a {t['last']})",
        "",
        "| Modelo | log loss | IC 95% | Brier | IC 95% |",
        "|---|---:|---|---:|---|",
    ]
    for key, label in (("b0", "B0"), ("b1", "B1")):
        s = t[key]
        lines.append(
            f"| {label} | {s['log_loss']:.4f} | {_ci(s['log_loss_ci'])} | {s['brier']:.4f} | "
            f"{_ci(s['brier_ci'])} |"
        )
    verdict = "inteiramente abaixo de zero" if r["meets_statistical_criterion"] else (
        "NÃO inteiramente abaixo de zero"
    )
    lines += [
        "",
        f"**B1 - B0, log loss: {d['log_loss']:+.4f} {_ci(d['log_loss_ci'])}** ({verdict}). "
        f"Brier: {d['brier']:+.4f} {_ci(d['brier_ci'])}.",
        "",
        "## Calibração do favorito no teste (B1)",
        "",
        "| Faixa | n | previsto | observado | IC 95% (Wilson) |",
        "|---|---:|---:|---:|---|",
    ]
    for row in t["b1_calibration"]:
        if row["n"]:
            lines.append(
                f"| {row['faixa']} | {row['n']} | {row['previsto']:.1%} | "
                f"{row['observado']:.1%} | [{row['ic'][0]:.1%}; {row['ic'][1]:.1%}] |"
            )
    lines += [
        "",
        "A decisão de adoção também exige revisão do `leakage-reviewer` até 27/11 18:00 BRT; "
        "ver o relatório da sessão.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if not MATCHES_PATH.exists():
        print(f"{MATCHES_PATH} não existe; rode: python -m ingest.vrs_matches")
        return 1
    result = analyze(pd.read_parquet(MATCHES_PATH))
    PARAMS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = render_report(result)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
