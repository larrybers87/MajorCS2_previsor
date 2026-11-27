"""B0 e B1 lado a lado no Stage 1 (RETROSPECTIVO; usado por ``sim.v3_stage1``).

Nada é ajustado: betas do B0 vêm da regra de formato (H10), betas do B1 do pré-registro
do Stage 3, e a configuração do B1 é a congelada. Em cada rodada o B1 usa só as rodadas
anteriores (D33). Para os cartéis, os ratings são os de antes do evento, fixos no stage.

A média 50/50 de B0 e B1 **não** é calculada: ela é a métrica da checagem de desastre do
Stage 3, com data marcada no pré-registro.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from sim.b1_ratings import b1_prob_fn, major_ratings
from sim.common import b0_from, markdown_table, percent
from sim.results import ResultRow
from swiss import ProbFn, StageState, best_of, records, simulate_stage
from swiss.rules import FINAL_RECORD_LABELS

from .metrics import brier_each, log_loss_each
from .v3_evaluation import team_metrics

# docs/preregistro_stage3.md (calculados só com dados até 01/11/2026).
B1_BETAS = {0.0: 0.350419, 1.0: 0.532006}
MODELS = ("B0", "B1")
VARIANTS = ("w=0", "w=1", "média")


def column(model: str, variant: str) -> str:
    return f"p_{model} {variant}"


def b1_ratings_before_each_round(
    matches: pd.DataFrame, seeds: pd.DataFrame, config, rows: Sequence[ResultRow]
) -> dict[int, dict[str, float]]:
    """``{rodada: {time: rating}}`` só com as rodadas anteriores a ela."""
    out = {}
    for number in sorted({r.round for r in rows}):
        previous = [r for r in rows if r.round < number]
        table = major_ratings(matches, seeds, config, {1: previous}).set_index("time")
        source = "b1_atual" if previous else "b1_pre_evento"
        out[number] = table[source].to_dict()
    return out


def match_probabilities(
    state: StageState,
    rows: Sequence[ResultRow],
    b0_fns: Mapping[float, ProbFn],
    b1_by_round: Mapping[int, Mapping[str, float]],
) -> pd.DataFrame:
    out = []
    for row in sorted((r for r in rows if r.winner is not None), key=lambda r: r.round):
        current = records(state.before_round(row.round))
        fmt = row.best_of or best_of(*current[row.team_a], state.all_best_of_three)
        a, b = row.team_a, row.team_b
        entry = {
            "rodada": row.round, "time_a": a, "time_b": b, "best_of": fmt,
            "vencedor": row.winner,
        }  # fmt: skip
        families = {
            "B0": b0_fns,
            "B1": {w: b1_prob_fn(b1_by_round[row.round], beta) for w, beta in B1_BETAS.items()},
        }
        for model, fns in families.items():
            p0, p1 = fns[0.0](a, b, fmt), fns[1.0](a, b, fmt)
            for variant, p in zip(VARIANTS, (p0, p1, (p0 + p1) / 2)):
                entry[column(model, variant)] = float(p)
        out.append(entry)
    return pd.DataFrame(out)


def _mean_and_error(values: np.ndarray) -> tuple[float, float]:
    error = values.std(ddof=1) / np.sqrt(len(values)) if len(values) > 1 else np.nan
    return float(values.mean()), float(error)


def match_scores(table: pd.DataFrame) -> dict:
    """Métricas por modelo e variante, e diferenças pareadas B1 - B0."""
    won = (table["vencedor"] == table["time_a"]).to_numpy()
    models, differences = [], []
    for variant in VARIANTS:
        each = {}
        for model in MODELS:
            p = table[column(model, variant)].to_numpy(float)
            each[model] = (log_loss_each(p, won), brier_each(p, won))
            ll, ll_error = _mean_and_error(each[model][0])
            brier, brier_error = _mean_and_error(each[model][1])
            models.append(
                {
                    "modelo": model, "variante": variant, "n": len(table),
                    "log_loss": ll, "log_loss_ep": ll_error,
                    "brier": brier, "brier_ep": brier_error,
                    "favoritos_que_venceram": int(((p > 0.5) == won).sum()),
                }  # fmt: skip
            )
        ll, ll_error = _mean_and_error(each["B1"][0] - each["B0"][0])
        brier, brier_error = _mean_and_error(each["B1"][1] - each["B0"][1])
        differences.append(
            {
                "variante": variant, "log_loss": ll, "log_loss_ep": ll_error,
                "brier": brier, "brier_ep": brier_error,
            }  # fmt: skip
        )
    return {"modelos": models, "b1_menos_b0": differences}


def record_scores(
    base: StageState,
    final: StageState,
    families: Mapping[str, Mapping[float, ProbFn]],
    n_sims: int,
    seed: int,
) -> list[dict]:
    """Cartéis previstos antes da rodada 1 contra os observados (stage encerrado)."""
    out = []
    for model, fns in families.items():
        distributions = []
        for w in (0.0, 1.0):
            result = simulate_stage(fns[w], base, n_sims, np.random.default_rng(seed))
            distributions.append(result.record_counts / n_sims)
        distributions.append(np.mean(distributions, axis=0))
        for variant, probs in zip(VARIANTS, distributions):
            predicted = pd.DataFrame(probs, columns=[f"P({k})" for k in FINAL_RECORD_LABELS])
            predicted.insert(0, "seed", range(1, 17))
            predicted.insert(1, "time", list(base.names))
            predicted["P(avançar)"] = probs[:, :3].sum(axis=1)
            _, summary = team_metrics(predicted, final)
            out.append({"modelo": model, "variante": variant} | summary)
    return out


def compare(
    base: StageState,
    state: StageState,
    rows: Sequence[ResultRow],
    seeds: pd.DataFrame,
    b0_variants: Sequence[Mapping],
    transform: str,
    matches: pd.DataFrame,
    b1_config,
    n_sims: int,
    seed: int,
    stage_complete: bool,
) -> tuple[pd.DataFrame, dict]:
    b0_fns = {float(v["w"]): b0_from(seeds, v["beta"], transform).prob_fn() for v in b0_variants}
    if set(b0_fns) != {0.0, 1.0}:
        raise ValueError("a comparação exige as variantes w=0 e w=1 do B0")
    by_round = b1_ratings_before_each_round(matches, seeds, b1_config, rows)
    table = match_probabilities(state, rows, b0_fns, by_round)
    scores = {"partidas": match_scores(table), "betas_b1": B1_BETAS}
    scores["por_formato"] = {
        f"Bo{fmt}": match_scores(group) for fmt, group in table.groupby("best_of")
    }
    if stage_complete:
        before = major_ratings(matches, seeds, b1_config, {}).set_index("time")
        ratings = before["b1_pre_evento"].to_dict()
        families = {"B0": b0_fns, "B1": {w: b1_prob_fn(ratings, b) for w, b in B1_BETAS.items()}}
        scores["carteis"] = record_scores(base, state, families, n_sims, seed)
    return table, scores


def comparison_lines(table: pd.DataFrame, scores: dict) -> list[str]:
    """Seção do relatório em markdown."""

    def metric(value: float, error: float, sign: str = "") -> str:
        return f"{value:{sign}.4f} (EP {error:.4f})"

    lines = [
        "## B0 e B1 lado a lado (RETROSPECTIVO)",
        "",
        "B0: logística na diferença de pontos VRS de 02/11. B1: Elo congelado "
        "(s=0,5, K=20, sem decaimento, m=2), atualizado só com rodadas anteriores. "
        "`média` = média das probabilidades de w=0 e w=1. EP = erro padrão entre partidas, "
        "que as trata como independentes (não são). A média B0/B1 não é calculada aqui.",
        "",
        *markdown_table(
            ["Modelo", "Variante", "n", "log loss", "Brier", "Favorito venceu"],
            [
                [
                    m["modelo"], m["variante"], m["n"],
                    metric(m["log_loss"], m["log_loss_ep"]), metric(m["brier"], m["brier_ep"]),
                    f"{m['favoritos_que_venceram']}/{m['n']}",
                ]
                for m in scores["partidas"]["modelos"]
            ],  # fmt: skip
        ),
        "",
        "Referência 50%: log loss 0,6931, Brier 0,2500.",
        "",
        "Diferença pareada B1 - B0 (negativo favorece o B1):",
        "",
        *markdown_table(
            ["Variante", "log loss", "Brier"],
            [
                [
                    d["variante"], metric(d["log_loss"], d["log_loss_ep"], "+"),
                    metric(d["brier"], d["brier_ep"], "+"),
                ]
                for d in scores["partidas"]["b1_menos_b0"]
            ],  # fmt: skip
        ),
        "",
        "Por formato (variante `média`):",
        "",
        *markdown_table(
            ["Formato", "Modelo", "n", "log loss", "Brier"],
            [
                [
                    fmt, m["modelo"], m["n"], metric(m["log_loss"], m["log_loss_ep"]),
                    metric(m["brier"], m["brier_ep"]),
                ]
                for fmt, group in scores["por_formato"].items()
                for m in group["modelos"]
                if m["variante"] == "média"
            ],  # fmt: skip
        ),
        "",
    ]
    if "carteis" in scores:
        lines += [
            "Cartéis finais previstos antes da rodada 1 (ratings fixos no stage; sem erro "
            "padrão, porque os times são dependentes):",
            "",
            *markdown_table(
                ["Modelo", "Variante", "Classificados", "Brier de avançar",
                 "log score (soma)", "sem informação"],  # fmt: skip
                [
                    [
                        r["modelo"], r["variante"],
                        f"{r['classificados_acertados']}/{r['classificados_total']}",
                        f"{r['brier_avanco']:.4f}", f"{r['log_score_cartel_soma']:.3f}",
                        f"{r['log_score_sem_informacao_soma']:.3f}",
                    ]
                    for r in scores["carteis"]
                ],  # fmt: skip
            ),
            "",
        ]
    lines += [
        "Probabilidade de `time_a` por partida (variante `média`):",
        "",
        *markdown_table(
            ["R", "Time A", "Time B", "Bo", "B0", "B1", "Vencedor"],
            [
                [
                    r["rodada"], r["time_a"], r["time_b"], r["best_of"],
                    percent(r[column("B0", "média")]), percent(r[column("B1", "média")]),
                    r["vencedor"],
                ]
                for r in table.to_dict("records")
            ],  # fmt: skip
        ),
        "",
    ]
    return lines
