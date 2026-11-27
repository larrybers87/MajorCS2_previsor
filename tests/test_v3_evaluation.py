"""Avaliação do Stage 1 e dados do site (dados sintéticos)."""

import math

import numpy as np
import pandas as pd
import pytest

from backtest.v3_evaluation import match_metrics, summarize_matches, team_metrics
from sim.export_site import final_table, round_matches
from sim.results import ResultRow
from swiss import advancing_teams, records
from swiss.rules import FINAL_RECORD_LABELS

from conftest import NAMES, random_stage


def prediction(a, b, p, number=1, fmt=1):
    return pd.DataFrame(
        [{"rodada": number, "time_a": a, "time_b": b, "best_of": fmt, "P(time_a vence)": p}]
    )


def result(a, b, score_a, score_b, number=1, fmt=1):
    return ResultRow(number, a, b, score_a, score_b, fmt, 2)


def test_match_metrics_uses_the_winner_probability_in_either_order():
    rows = [result("B", "A", 13, 5)]  # CSV na ordem inversa da previsão; B venceu
    table = match_metrics(prediction("A", "B", 0.8), rows)
    assert table.loc[0, "p_vencedor"] == pytest.approx(0.2)
    assert table.loc[0, "log_loss"] == pytest.approx(-math.log(0.2))
    assert table.loc[0, "brier"] == pytest.approx(0.64)
    assert not table.loc[0, "acertou"]
    summary = summarize_matches(table)
    assert summary["n"] == 1 and summary["log_loss_erro_padrao"] is None


def test_match_metrics_rejects_missing_result_and_wrong_format():
    with pytest.raises(ValueError, match="sem resultado"):
        match_metrics(prediction("A", "C", 0.5), [result("A", "B", 13, 5)])
    with pytest.raises(ValueError, match="formato"):
        match_metrics(prediction("A", "B", 0.5, fmt=3), [result("A", "B", 13, 5)])


def uniform_predictions(p_advance):
    baseline = np.array([2, 3, 3, 3, 3, 2]) / 16
    return pd.DataFrame(
        [
            {"seed": seed, "time": name, "P(avançar)": p_advance[seed - 1]}
            | {f"P({k})": v for k, v in zip(FINAL_RECORD_LABELS, baseline)}
            for seed, name in enumerate(NAMES, start=1)
        ]
    )


def test_team_metrics_counts_hits_and_matches_the_baseline():
    final = random_stage(np.random.default_rng(3))
    advanced = set(advancing_teams(final))
    perfect = [0.9 if name in advanced else 0.1 for name in NAMES]
    table, summary = team_metrics(uniform_predictions(perfect), final)
    assert summary["classificados_acertados"] == 8
    assert summary["brier_avanco"] == pytest.approx(0.01)
    # Distribuições iguais à referência: os dois log scores têm de coincidir.
    assert summary["log_score_cartel_soma"] == pytest.approx(
        summary["log_score_sem_informacao_soma"]
    )
    observed = records(final)
    assert all(table.set_index("time").loc[n, "cartel"] == "{}-{}".format(*observed[n])
               for n in NAMES)  # fmt: skip


def test_team_metrics_requires_a_finished_stage():
    from swiss import StageState

    with pytest.raises(ValueError, match="encerrado"):
        team_metrics(uniform_predictions([0.5] * 16), StageState.new(NAMES))


def test_final_table_gives_next_stage_seeds_only_to_the_top_eight():
    final = random_stage(np.random.default_rng(5))
    rows = final_table(final)
    assert [r["seed_seguinte"] for r in rows] == [*range(9, 17), *[None] * 8]
    assert [r["time"] for r in rows[:8]] == advancing_teams(final)
    assert sum(r["difficulty"] for r in rows) == 0


def test_round_matches_flips_probability_to_the_better_seed():
    final = random_stage(np.random.default_rng(7))
    first = final.round_matches(1)[0]
    better, worse = sorted((first.team_a, first.team_b), key=final.seed_of)
    rows = [result(worse, better, 13, 4)]
    stored = {"time_a": worse, "p_a": 0.7, "acertou": True, "log_loss": 0.1, "brier": 0.1}
    key = (1, frozenset((better, worse)))
    match = round_matches(final, rows, {key: ("previo", stored)})[0][0]
    assert (match["a"], match["b"]) == (better, worse)
    assert (match["placar_a"], match["placar_b"]) == (4, 13)
    assert match["previsao"]["p_a"] == pytest.approx(0.3)
