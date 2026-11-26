"""Calibração e avaliação walk-forward do B0.

Uso::

    python -m backtest.b0_calibration

Lê ``data/processed/matches.parquet``; grava ``data/processed/b0_params.json`` e o
relatório ``docs/b0_calibracao.md``.

Protocolo (definido antes de ver qualquer resultado do Stage 1):
- dados de 2025-06-01 até antes de 2026-11-23 (datas do VRS, fuso do Pacífico), só
  partidas com rating dos dois lados;
- rating = último snapshot VRS estritamente anterior à data da partida;
- walk-forward mensal: o mês M é previsto com beta ajustado nas partidas anteriores a M;
- população-alvo da avaliação: os dois times no top 100 do snapshot anterior;
- população de treino (todas | top 100): a de menor log loss walk-forward no alvo;
- transformação (pontos | log): a de maior verossimilhança no treino completo.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ingest.vrs import PROJECT_ROOT
from ingest.vrs_matches import MATCHES_PATH, WINDOW_START
from models.b0 import TRANSFORMS, features, fit_beta, negative_log_likelihood, series_win_probability
from sim.singapore2026 import DATA_CUTOFF, PINNED_VRS_COMMIT

from .metrics import brier_each, cluster_bootstrap_ci, log_loss_each

PARAMS_PATH = PROJECT_ROOT / "data" / "processed" / "b0_params.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "b0_calibracao.md"
FIRST_TEST_MONTH = date(2025, 9, 1)
TARGET_MAX_RANK = 100
POPULATIONS = ("todas", "top100")
ASSUMED_BEST_OF = 3  # hipótese H10
RNG_SEED = 20261126


def rated_matches(table: pd.DataFrame) -> pd.DataFrame:
    """Partidas utilizáveis na janela, com verificação de que o rating é anterior."""
    data = table.dropna(subset=["points_a", "points_b", "rating_snapshot"])
    data = data[
        (data["date"] >= pd.Timestamp(WINDOW_START)) & (data["date"] < pd.Timestamp(DATA_CUTOFF))
    ]
    if not (data["rating_snapshot"] < data["date"]).all():
        raise ValueError("há rating de snapshot não anterior à data da partida (vazamento)")
    return data.sort_values("date", kind="stable").reset_index(drop=True)


def in_population(data: pd.DataFrame, population: str) -> np.ndarray:
    if population == "todas":
        return np.ones(len(data), dtype=bool)
    top = (data["rank_a"] <= TARGET_MAX_RANK) & (data["rank_b"] <= TARGET_MAX_RANK)
    return top.to_numpy(dtype=bool)


def _x(data: pd.DataFrame, transform: str) -> np.ndarray:
    return features(
        data["points_a"].to_numpy(float), data["points_b"].to_numpy(float), transform
    )


def walk_forward(
    data: pd.DataFrame, transform: str, population: str, best_of: int = ASSUMED_BEST_OF
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Previsões mensais fora da amostra.

    Retorna (p do B0, p da regra "favorito com taxa constante", máscara das partidas
    previstas). Tudo é ajustado só com partidas anteriores ao início do mês.
    """
    x = _x(data, transform)
    won = data["team_a_won"].to_numpy(bool)
    trainable = in_population(data, population)
    month = data["date"].dt.to_period("M")
    favorite = np.sign(data["points_a"].to_numpy(float) - data["points_b"].to_numpy(float))
    p = np.full(len(data), np.nan)
    p_favorite = np.full(len(data), np.nan)
    for current in month[data["date"] >= pd.Timestamp(FIRST_TEST_MONTH)].unique():
        train = (data["date"] < current.start_time).to_numpy()
        test = (month == current).to_numpy()
        beta = fit_beta(x[train & trainable], won[train & trainable], best_of)
        p[test] = series_win_probability(beta, x[test], best_of)
        decided = train & trainable & (favorite != 0)
        rate = np.mean(won[decided] == (favorite[decided] > 0))
        p_favorite[test] = 0.5 + favorite[test] * (rate - 0.5)
    return p, p_favorite, ~np.isnan(p)


def _summary(p, won, days, rng) -> dict:
    ll, brier = log_loss_each(p, won), brier_each(p, won)
    return {
        "log_loss": float(ll.mean()),
        "log_loss_ci": cluster_bootstrap_ci(ll, days, rng),
        "brier": float(brier.mean()),
        "brier_ci": cluster_bootstrap_ci(brier, days, rng),
    }


def _difference(p, reference, won, days, rng) -> dict:
    """B0 menos referência, pareado (negativo = B0 melhor)."""
    out = {}
    for name, each in (("log_loss", log_loss_each), ("brier", brier_each)):
        delta = each(p, won) - each(reference, won)
        out[name] = float(delta.mean())
        out[f"{name}_ci"] = cluster_bootstrap_ci(delta, days, rng)
    return out


def reliability(p: np.ndarray, won: np.ndarray, edges=np.arange(0.5, 1.01, 0.1)) -> list[dict]:
    """Calibração do ponto de vista do favorito do modelo."""
    favorite_p = np.maximum(p, 1 - p)
    favorite_won = np.where(p >= 0.5, won, ~won)
    rows = []
    for low, high in zip(edges[:-1], edges[1:]):
        inside = (favorite_p >= low) & (favorite_p < high + (1e-9 if high >= 1 else 0))
        if inside.any():
            rows.append(
                {
                    "faixa": f"{low:.0%}-{high:.0%}",
                    "n": int(inside.sum()),
                    "previsto": float(favorite_p[inside].mean()),
                    "observado": float(favorite_won[inside].mean()),
                }
            )
    return rows


def calibrate(data: pd.DataFrame, seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    won = data["team_a_won"].to_numpy(bool)
    days = data["date"].to_numpy()
    target = in_population(data, "top100")

    runs = {}
    for population in POPULATIONS:
        for transform in TRANSFORMS:
            p, p_favorite, tested = walk_forward(data, transform, population)
            mask = tested & target
            runs[(population, transform)] = (p, p_favorite, mask)
    walk_ll = {k: log_loss_each(p[m], won[m]).mean() for k, (p, _, m) in runs.items()}
    population = min(walk_ll, key=walk_ll.get)[0]

    train = in_population(data, population)
    fits = {}
    for transform in TRANSFORMS:
        x = _x(data, transform)[train]
        beta = fit_beta(x, won[train], ASSUMED_BEST_OF)
        nll = negative_log_likelihood(beta, x, won[train], ASSUMED_BEST_OF)
        fits[transform] = {"beta": beta, "log_likelihood": -nll}
    transform = max(fits, key=lambda t: fits[t]["log_likelihood"])

    p, p_favorite, mask = runs[(population, transform)]
    w, d = won[mask], days[mask]
    coin = np.full(mask.sum(), 0.5)
    difference = np.sign(
        data["points_a"].to_numpy(float) - data["points_b"].to_numpy(float)
    )[mask]
    hard = 0.5 + 0.5 * difference
    evaluation = {
        "n": int(mask.sum()),
        "first": str(data["date"][mask].min().date()),
        "last": str(data["date"][mask].max().date()),
        "b0": _summary(p[mask], w, d, rng),
        "moeda_50": _summary(coin, w, d, rng),
        "favorito_taxa_constante": _summary(p_favorite[mask], w, d, rng),
        "maior_vrs_vence": {
            "brier": float(brier_each(hard, w).mean()),
            "brier_ci": cluster_bootstrap_ci(brier_each(hard, w), d, rng),
            "acerto": float(np.mean((difference > 0)[difference != 0] == w[difference != 0])),
        },
        "b0_menos_moeda": _difference(p[mask], coin, w, d, rng),
        "b0_menos_favorito": _difference(p[mask], p_favorite[mask], w, d, rng),
        "calibracao": reliability(p[mask], w),
    }

    # Incerteza de beta (bootstrap por dia) e sensibilidade à hipótese H10.
    x = _x(data, transform)[train]
    y, train_days = won[train], days[train]
    _, index = np.unique(train_days, return_inverse=True)
    groups = np.split(np.argsort(index, kind="stable"), np.cumsum(np.bincount(index))[:-1])
    boot = []
    for _ in range(200):
        sample = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        boot.append(fit_beta(x[sample], y[sample], ASSUMED_BEST_OF, tolerance=1e-5))
    p_bo1, _, mask_bo1 = walk_forward(data, transform, population, best_of=1)
    mask_bo1 &= target

    return {
        "data_cutoff_exclusive": str(DATA_CUTOFF),
        "vrs_commit": PINNED_VRS_COMMIT,
        "transform": transform,
        "population": population,
        "assumed_best_of": ASSUMED_BEST_OF,
        "beta": fits[transform]["beta"],
        "beta_ci": [float(v) for v in np.quantile(boot, [0.025, 0.975])],
        "n_train": int(train.sum()),
        "train_first": str(data["date"][train].min().date()),
        "train_last": str(data["date"][train].max().date()),
        "fits": fits,
        "walk_forward_log_loss": {f"{k[0]}/{k[1]}": float(v) for k, v in walk_ll.items()},
        "evaluation": evaluation,
        "sensitivity_bo1": {
            "beta": fit_beta(x, y, 1),
            "walk_forward_log_loss": float(log_loss_each(p_bo1[mask_bo1], won[mask_bo1]).mean()),
        },
    }


def _ci(values) -> str:
    return f"[{values[0]:.4f}; {values[1]:.4f}]"


def render_report(result: dict, n_rated: int) -> str:
    e = result["evaluation"]
    lines = [
        "# Calibração do B0",
        "",
        "Gerado por `python -m backtest.b0_calibration` (não editar à mão).",
        "",
        f"- Partidas com rating na janela: {n_rated}; treino final: {result['n_train']} "
        f"({result['train_first']} a {result['train_last']}), população "
        f"**{result['population']}**.",
        f"- Transformação escolhida: **{result['transform']}**; "
        f"**beta = {result['beta']:.4f}**, IC 95% {_ci(result['beta_ci'])}.",
        f"- **Hipótese H10 (não verificada):** toda partida histórica tratada como "
        f"Bo{result['assumed_best_of']}.",
        "",
        "## Escolha do modelo",
        "",
        "| Transformação | beta | log-verossimilhança no treino final |",
        "|---|---:|---:|",
    ]
    for name, fit in result["fits"].items():
        lines.append(f"| {name} | {fit['beta']:.4f} | {fit['log_likelihood']:.1f} |")
    lines += ["", "| Treino / transformação | log loss walk-forward no alvo |", "|---|---:|"]
    for name, value in result["walk_forward_log_loss"].items():
        lines.append(f"| {name} | {value:.4f} |")
    lines += [
        "",
        "A escolha usa os mesmos dados da avaliação abaixo (4 combinações), o que traz um "
        "otimismo pequeno.",
        "",
        f"## Avaliação walk-forward ({e['n']} partidas, {e['first']} a {e['last']}, "
        "ambos no top 100)",
        "",
        "IC 95% por bootstrap reamostrando dias.",
        "",
        "| Previsor | log loss | IC 95% | Brier | IC 95% |",
        "|---|---:|---|---:|---|",
    ]
    for key, label in (
        ("b0", "B0"),
        ("favorito_taxa_constante", "Maior VRS vence, com a taxa histórica"),
        ("moeda_50", "50% fixo"),
    ):
        s = e[key]
        lines.append(
            f"| {label} | {s['log_loss']:.4f} | {_ci(s['log_loss_ci'])} | {s['brier']:.4f} | "
            f"{_ci(s['brier_ci'])} |"
        )
    hard = e["maior_vrs_vence"]
    lines.append(
        f"| Maior VRS vence (0 ou 100%) | infinito | - | {hard['brier']:.4f} | "
        f"{_ci(hard['brier_ci'])} |"
    )
    lines += [
        "",
        f"Acerto da regra \"maior VRS vence\": {hard['acerto']:.1%}.",
        "",
        "| Diferença pareada (negativo = B0 melhor) | log loss | IC 95% | Brier | IC 95% |",
        "|---|---:|---|---:|---|",
    ]
    for key, label in (("b0_menos_moeda", "B0 - 50%"), ("b0_menos_favorito", "B0 - taxa fixa")):
        s = e[key]
        lines.append(
            f"| {label} | {s['log_loss']:+.4f} | {_ci(s['log_loss_ci'])} | {s['brier']:+.4f} | "
            f"{_ci(s['brier_ci'])} |"
        )
    lines += [
        "",
        "## Calibração (favorito do modelo)",
        "",
        "| Faixa | n | previsto | observado |",
        "|---|---:|---:|---:|",
    ]
    for row in e["calibracao"]:
        lines.append(
            f"| {row['faixa']} | {row['n']} | {row['previsto']:.1%} | {row['observado']:.1%} |"
        )
    sens = result["sensitivity_bo1"]
    lines += [
        "",
        "## Sensibilidade a H10",
        "",
        f"Se as partidas fossem todas Bo1: beta por mapa = {sens['beta']:.4f} (contra "
        f"{result['beta']:.4f}), log loss walk-forward {sens['walk_forward_log_loss']:.4f}. "
        "O log loss quase não distingue as duas leituras, mas o beta por mapa muda, e com ele "
        "as probabilidades de Bo1. O valor verdadeiro (mistura de formatos) deve ficar entre "
        "os dois.",
        "",
    ]
    return "\n".join(lines)


def main(matches_path: Path = MATCHES_PATH) -> int:
    if not matches_path.exists():
        print(f"{matches_path} não existe; rode: python -m ingest.vrs_matches")
        return 1
    data = rated_matches(pd.read_parquet(matches_path))
    result = calibrate(data)
    PARAMS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = render_report(result, len(data))
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
