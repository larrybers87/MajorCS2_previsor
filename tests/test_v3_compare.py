"""Comparação retrospectiva B0 x B1 (dados sintéticos)."""

import math

import numpy as np
import pandas as pd
import pytest

from backtest.v3_compare import (
    B1_BETAS,
    b1_ratings_before_each_round,
    column,
    compare,
    comparison_lines,
    match_scores,
)
from models.ratings import EloConfig
from sim.format_config import DEFAULT_FORMAT
from sim.results import ResultRow, build_state
from sim.singapore2026 import ENTRANTS, ROSTERS
from sim.stages import entrants_by_seed
from swiss import apply_results, current_round, pair_round, records, best_of

CONFIG = EloConfig(s=0.5, k=20, half_life=None, provisional=2)
VARIANTS = [{"w": 0.0, "beta": 0.15}, {"w": 1.0, "beta": 0.23}]


def seeds():
    return pd.DataFrame(
        {
            "name": [e.name for e in ENTRANTS],
            "vrs_name": [e.vrs_name for e in ENTRANTS],
            "vrs_points": [2000 - 20 * i for i in range(32)],
            "pre_event_seed": range(1, 33),
            "stage": [e.stage for e in sorted(ENTRANTS, key=lambda e: e.stage)],
        }
    ).assign(stage=[e.stage for e in ENTRANTS])


def history():
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-10-01", periods=3),
            "team_a": "BC.Game",
            "team_b": "Ninjas in Pyjamas",
            "roster_a": ", ".join(ROSTERS["GOSH"]),
            "roster_b": ", ".join(ROSTERS["NiP"]),
            "points_a": pd.array([1300] * 3, dtype="Int64"),
            "points_b": pd.array([1500] * 3, dtype="Int64"),
            "team_a_won": True,
        }
    )


def stage1():
    """Stage completo em que vence sempre o primeiro do par da engine."""
    base = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds(), 1))
    state = base
    while current_round(state) is not None:
        state = apply_results(state, [(p.team_a, p.team_b) for p in pair_round(state)])
    rows = []
    for i, m in enumerate(state.matches, start=2):
        wins, losses = records(state.before_round(m.round))[m.team_a]
        fmt = best_of(wins, losses)
        score = (2, 0) if fmt == 3 else (13, 7)
        a, b = score if m.winner == m.team_a else score[::-1]
        rows.append(ResultRow(m.round, m.team_a, m.team_b, a, b, fmt, i))
    return base, build_state(base, rows), rows


def test_ratings_never_see_the_current_or_later_rounds():
    _, _, rows = stage1()
    ratings = b1_ratings_before_each_round(history(), seeds(), CONFIG, rows)
    flipped = [
        r if r.round < 3 else ResultRow(r.round, r.team_a, r.team_b, r.score_b, r.score_a,
                                        r.best_of, r.line)
        for r in rows
    ]  # fmt: skip
    changed = b1_ratings_before_each_round(history(), seeds(), CONFIG, flipped)
    for number in (1, 2, 3):
        assert changed[number] == ratings[number], number
    assert changed[4] != ratings[4]
    # Antes da rodada 1 nada do Major entrou; depois dela, quem venceu subiu.
    winner = next(r.winner for r in rows if r.round == 1)
    assert ratings[2][winner] > ratings[1][winner]


def test_match_scores_values_and_paired_difference():
    table = pd.DataFrame(
        {"time_a": ["A", "C"], "vencedor": ["A", "D"]}
        | {column("B0", v): [0.5, 0.5] for v in ("w=0", "w=1", "média")}
        | {column("B1", v): [0.8, 0.2] for v in ("w=0", "w=1", "média")}
    )
    scores = match_scores(table)
    b1 = next(m for m in scores["modelos"] if m["modelo"] == "B1")
    assert b1["log_loss"] == pytest.approx(-math.log(0.8))
    assert b1["log_loss_ep"] == pytest.approx(0.0)
    assert b1["brier"] == pytest.approx(0.04)
    assert b1["favoritos_que_venceram"] == 2
    assert scores["b1_menos_b0"][0]["log_loss"] == pytest.approx(-math.log(0.8) - math.log(2))


def test_compare_full_stage():
    base, state, rows = stage1()
    table, scores = compare(
        base, state, rows, seeds(), VARIANTS, "points", history(), CONFIG, 2000, 1, True
    )
    assert len(table) == 33
    for model in ("B0", "B1"):
        np.testing.assert_allclose(
            table[column(model, "média")],
            (table[column(model, "w=0")] + table[column(model, "w=1")]) / 2,
        )
    assert len(scores["carteis"]) == 6
    assert set(B1_BETAS) == {0.0, 1.0}
    assert "RETROSPECTIVO" in "\n".join(comparison_lines(table, scores))
