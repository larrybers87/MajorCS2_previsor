"""Ratings do B1 para o Major (dados sintéticos)."""

import numpy as np
import pandas as pd
import pytest

from models.ratings import EloConfig
from sim.b1_ratings import b1_prob_fn, config_from, major_ratings
from sim.results import ResultRow
from sim.singapore2026 import ENTRANTS, ROSTERS


def seeds():
    return pd.DataFrame(
        {
            "name": [e.name for e in ENTRANTS],
            "vrs_name": [e.vrs_name for e in ENTRANTS],
            "vrs_points": [2000 - 20 * i for i in range(32)],
        }
    )


def history():
    """GOSH (elenco da BC.Game) vence NiP várias vezes, sob outro nome de organização."""
    n = 6
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-10-01", periods=n),
            "team_a": "BC.Game",
            "team_b": "Ninjas in Pyjamas",
            "roster_a": ", ".join(ROSTERS["GOSH"]),
            "roster_b": ", ".join(ROSTERS["NiP"]),
            "points_a": pd.array([1300] * n, dtype="Int64"),
            "points_b": pd.array([1500] * n, dtype="Int64"),
            "team_a_won": True,
        }
    )


def test_history_is_linked_by_roster_and_major_results_update_ratings():
    config = EloConfig(s=0.5, k=20, half_life=None, provisional=1)
    rows = [
        ResultRow(1, "Liquid", "GOSH", 13, 1, 1, 2),
        ResultRow(2, "FaZe", "GOSH", None, None, 1, 3),  # pendente: não altera nada
    ]
    table = major_ratings(history(), seeds(), config, {1: rows}).set_index("time")
    prior = lambda name: 1500 + 0.5 * (seeds().set_index("name").loc[name, "vrs_points"] - 1000)
    # GOSH ganhou pontos no histórico mesmo aparecendo como "BC.Game".
    assert table.loc["GOSH", "b1_pre_evento"] > 1500 + 0.5 * (1300 - 1000)
    assert table.loc["Vitality", "b1_pre_evento"] == pytest.approx(prior("Vitality"))
    assert table.loc["Liquid", "b1_atual"] > table.loc["Liquid", "b1_pre_evento"]
    assert table.loc["GOSH", "b1_atual"] < table.loc["GOSH", "b1_pre_evento"]
    assert table.loc["FaZe", "b1_atual"] == table.loc["FaZe", "b1_pre_evento"]
    assert table.loc["GOSH", "partidas_no_major"] == 1
    assert len(table) == 32


def test_config_roundtrip_and_prob_fn():
    chosen = {"kind": "EloConfig", "s": 0.5, "k": 20, "half_life": None, "provisional": 2}
    assert config_from(chosen) == EloConfig(0.5, 20, None, 2)
    prob = b1_prob_fn({"A": 1900.0, "B": 1700.0}, 0.3)
    assert prob("A", "B", 1) == pytest.approx(1 / (1 + np.exp(-0.6)))
    assert prob("A", "B", 3) + prob("B", "A", 3) == pytest.approx(1.0)
