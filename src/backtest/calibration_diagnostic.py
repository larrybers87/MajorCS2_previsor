"""Diagnóstico de calibração do B0 por faixas no período de teste (não ajusta nada).

Uso::

    python -m backtest.calibration_diagnostic

Grava ``docs/calibracao_teste_b0.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ingest.vrs import PROJECT_ROOT
from ingest.vrs_matches import MATCHES_PATH
from models.b0 import features

from .b0_calibration import in_population, rated_matches
from .h10_format import fit_beta_given_w, mixture_probability, select_b0
from .metrics import cluster_bootstrap_ci
from .protocol import period_mask, walk_forward, wilson_interval

REPORT_PATH = PROJECT_ROOT / "docs" / "calibracao_teste_b0.md"
BANDS = (("50-60%", 0.5, 0.6), ("60-70%", 0.6, 0.7), ("70-80%", 0.7, 0.8), ("80%+", 0.8, 1.01))
MAIN = "média de w=0 e w=1"
RNG_SEED = 20261127


def band_table(p: np.ndarray, won: np.ndarray, days: np.ndarray, rng) -> list[dict]:
    """Por faixa de probabilidade do favorito: n, previsto, observado e intervalos."""
    favorite_p = np.maximum(p, 1 - p)
    favorite_won = np.where(p >= 0.5, won, ~won).astype(float)
    rows = []
    for label, low, high in BANDS:
        inside = (favorite_p >= low) & (favorite_p < high)
        n = int(inside.sum())
        row: dict = {"faixa": label, "n": n}
        if n:
            gap = favorite_won[inside] - favorite_p[inside]
            row |= {
                "previsto": float(favorite_p[inside].mean()),
                "observado": float(favorite_won[inside].mean()),
                "wilson": wilson_interval(int(favorite_won[inside].sum()), n),
                "bootstrap": cluster_bootstrap_ci(
                    favorite_won[inside], days[inside], rng, n_boot=10_000
                ),
                "diferenca": float(gap.mean()),
                "diferenca_ic": cluster_bootstrap_ci(gap, days[inside], rng, n_boot=10_000),
            }
        rows.append(row)
    return rows


def predictions(data: pd.DataFrame) -> tuple[dict[str, np.ndarray], np.ndarray, dict]:
    """Walk-forward mensal no teste para w=0, w=1 e a média (modelo do Stage 2)."""
    config, _ = select_b0(data)
    x = features(
        data["points_a"].to_numpy(float), data["points_b"].to_numpy(float), config["transform"]
    )
    won = data["team_a_won"].to_numpy(bool)
    train = in_population(data, config["population"])
    out = {}
    for w in (0.0, 1.0):
        out[f"w={w:g}"] = walk_forward(
            data["date"], "test", train,
            fit=lambda m, w=w: fit_beta_given_w(w, x[m], won[m], np.ones(m.sum()))[0],
            predict=lambda beta, m, w=w: mixture_probability(w, beta, x[m]),
        )  # fmt: skip
    out = {MAIN: (out["w=0"] + out["w=1"]) / 2, **out}
    test = period_mask(data["date"], "test") & in_population(data, "top100")
    return out, test, config


def render(data: pd.DataFrame, seed: int = RNG_SEED) -> str:
    rng = np.random.default_rng(seed)
    models, test, config = predictions(data)
    won = data["team_a_won"].to_numpy(bool)[test]
    days = data["date"].to_numpy()[test]
    dates = data["date"][test]
    lines = [
        "# Calibração do B0 por faixas no teste (diagnóstico)",
        "",
        "Gerado por `python -m backtest.calibration_diagnostic`. **Só diagnóstico:** nada "
        "é ajustado a partir desta tabela. O teste já tinha sido visto (sessão 03).",
        "",
        f"{int(test.sum())} partidas, {dates.min():%Y-%m-%d} a {dates.max():%Y-%m-%d}, ambos no "
        f"top 100; walk-forward mensal; B0 {config['population']}/{config['transform']}. "
        "Faixa = probabilidade do favorito do modelo.",
        "",
        "Dois intervalos de 95% para o observado: Wilson (supõe partidas independentes) e "
        "bootstrap por dias. **Diferença** = observado menos previsto (negativa = excesso de "
        "confiança), com bootstrap por dias.",
    ]
    for name, p in models.items():
        title = f"## {name}" + (" (modelo da manchete do Stage 2)" if name == MAIN else "")
        lines += [
            "",
            title,
            "",
            "| Faixa | n | previsto | observado | Wilson | bootstrap | diferença |",
            "|---|---:|---:|---:|---|---|---|",
        ]
        for row in band_table(p[test], won, days, rng):
            if not row["n"]:
                lines.append(f"| {row['faixa']} | 0 | - | - | - | - | - |")
                continue
            w_low, w_high = row["wilson"]
            b_low, b_high = row["bootstrap"]
            d_low, d_high = row["diferenca_ic"]
            lines.append(
                f"| {row['faixa']} | {row['n']} | {row['previsto']:.1%} | "
                f"{row['observado']:.1%} | [{w_low:.1%}; {w_high:.1%}] | "
                f"[{b_low:.1%}; {b_high:.1%}] | {100 * row['diferenca']:+.1f} pp "
                f"[{100 * d_low:+.1f}; {100 * d_high:+.1f}] |"
            )
    lines += [
        "",
        "## Leitura",
        "- São quatro faixas e três versões do modelo: algum intervalo pode excluir o "
        "previsto por acaso (sem correção para comparações múltiplas).",
        "- A faixa 80%+ tem poucas partidas; o bootstrap com poucos dias é instável.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if not MATCHES_PATH.exists():
        print(f"{MATCHES_PATH} não existe; rode: python -m ingest.vrs_matches")
        return 1
    report = render(rated_matches(pd.read_parquet(MATCHES_PATH)))
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
