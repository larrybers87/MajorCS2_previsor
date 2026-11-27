"""Log loss das variantes do B1 na seleção pré-registrada (só desenvolvimento).

Uso::

    python -m backtest.b1_decay_report

A seleção gravou só as dez melhores; aqui as mesmas 172 configurações são recalculadas,
com o mesmo código e os mesmos dados de **desenvolvimento** (2025-09 a 2026-05), e o
valor da escolhida é conferido contra ``data/processed/b1_params.json``. Informativo:
não grava parâmetros, não calcula o teste, não usa partidas do Major e **não muda o
modelo congelado**.
"""

from __future__ import annotations

import json

import pandas as pd

from ingest.vrs import PROJECT_ROOT
from ingest.vrs_matches import MATCHES_PATH
from models.ratings import EloConfig, GlickoConfig
from sim.common import markdown_table, write_text

from .b1_selection import (
    PARAMS_PATH,
    calibrated_walk_forward,
    evaluation_mask,
    grid,
    log_loss,
    prepare,
    rating_differences,
)
from .protocol import period_mask

REPORT_PATH = PROJECT_ROOT / "docs" / "b1_decaimento_desenvolvimento.md"
HALF_LIVES = (60, 90, 180, None)


def dev_scores(table: pd.DataFrame, configs=None) -> tuple[list[tuple[float, object]], int]:
    """``[(log loss, configuração)]`` em ordem crescente e o número de partidas."""
    data, days, _ = prepare(table)
    target = evaluation_mask(data)
    won = data["team_a_won"].to_numpy(bool)
    dev = period_mask(data["date"], "dev") & target
    scores = []
    for config in configs or grid():
        differences, _ = rating_differences(config, days, len(data))
        p, _ = calibrated_walk_forward(data, differences, target, "dev")
        scores.append((log_loss(p[dev], won[dev]), config))
    scores.sort(key=lambda item: item[0])
    return scores, int(dev.sum())


def _h(value) -> str:
    return "sem decaimento" if value is None else f"{value:g} dias"


def report(scores, n: int, chosen: EloConfig) -> str:
    by_config = {config: value for value, config in scores}
    best = by_config[chosen]
    same_rest = [
        (h, by_config[EloConfig(chosen.s, chosen.k, h, chosen.provisional)]) for h in HALF_LIVES
    ]
    best_per_h = [
        next((v, c) for v, c in scores if isinstance(c, EloConfig) and c.half_life == h)
        for h in HALF_LIVES
    ]
    glicko = [(v, c) for v, c in scores if isinstance(c, GlickoConfig)]
    return "\n".join(
        [
            "# B1: variantes de decaimento na seleção (desenvolvimento)",
            "",
            "Gerado por `python -m backtest.b1_decay_report` (não editar à mão). "
            f"{n} partidas, 2025-09 a 2026-05, {len(scores)} configurações, walk-forward "
            "mensal. Log loss menor é melhor.",
            "",
            "**Só informação.** O modelo segue congelado em "
            f"**{chosen.label}**; nada daqui usa o teste ou o Major. As diferenças abaixo não "
            "têm intervalo de confiança e não sustentam trocar o modelo.",
            "",
            f"## Mesma configuração (s={chosen.s:g}, K={chosen.k:g}, m={chosen.provisional:g}), "
            "variando a meia-vida",
            "",
            *markdown_table(
                ["Meia-vida", "log loss", "diferença para a escolhida"],
                [[_h(h), f"{v:.6f}", f"{v - best:+.6f}"] for h, v in same_rest],
            ),
            "",
            "## Melhor Elo de cada meia-vida",
            "",
            *markdown_table(
                ["Meia-vida", "Configuração", "log loss", "diferença"],
                [
                    [_h(c.half_life), c.label, f"{v:.6f}", f"{v - best:+.6f}"]
                    for v, c in best_per_h
                ],
            ),
            "",
            "## Glicko-1 (o RD cresce `c` por raiz de dia)",
            "",
            *markdown_table(
                ["Configuração", "log loss", "diferença"],
                [[c.label, f"{v:.6f}", f"{v - best:+.6f}"] for v, c in glicko],
            ),
            "",
            "## Todas as configurações",
            "",
            *markdown_table(
                ["#", "Configuração", "log loss"],
                [[i, c.label, f"{v:.6f}"] for i, (v, c) in enumerate(scores, start=1)],
            ),
            "",
        ]
    )


def main() -> int:
    if not (MATCHES_PATH.exists() and PARAMS_PATH.exists()):
        print(f"ERRO: faltam {MATCHES_PATH} ou {PARAMS_PATH}")
        return 1
    stored = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    chosen = EloConfig(**{k: v for k, v in stored["chosen"].items() if k != "kind"})
    scores, n = dev_scores(pd.read_parquet(MATCHES_PATH))
    reproduced = dict((c, v) for v, c in scores)[chosen]
    expected = stored["dev"]["b1_log_loss"]
    if abs(reproduced - expected) > 1e-9 or scores[0][1] != chosen or n != stored["dev"]["n"]:
        print(
            "ERRO: a seleção não foi reproduzida "
            f"({reproduced!r} x {expected!r}, melhor {scores[0][1].label}, n={n})"
        )
        return 1
    write_text(REPORT_PATH, report(scores, n, chosen))
    print("\n".join(report(scores, n, chosen).splitlines()[:30]))
    print(f"Reproduzido: {reproduced:.12f}. Gravado em {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
