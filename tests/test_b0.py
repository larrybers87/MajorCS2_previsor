"""Modelo B0, métricas e walk-forward (dados sintéticos)."""

import numpy as np
import pandas as pd
import pytest

from backtest.b0_calibration import rated_matches, walk_forward
from backtest.metrics import brier_each, cluster_bootstrap_ci, log_loss_each
from models.b0 import B0Model, features, fit_beta, series_win_probability
from swiss import StageState, simulate_stage


@pytest.mark.parametrize("best_of", [1, 3])
def test_fit_recovers_known_beta(best_of):
    rng = np.random.default_rng(1)
    x = rng.uniform(-6, 6, 100_000)
    won = rng.random(x.size) < series_win_probability(0.3, x, best_of)
    assert fit_beta(x, won, best_of) == pytest.approx(0.3, abs=0.01)


def test_features():
    assert features(1500, 1300, "points") == pytest.approx(2.0)
    assert features(1500, 1300, "log") == pytest.approx(np.log(1500 / 1300))
    with pytest.raises(ValueError):
        features(0, 1300, "log")


def test_prob_fn_is_symmetric_and_bo3_amplifies():
    model = B0Model(0.2, "points", {"A": 1800.0, "B": 1400.0})
    prob = model.prob_fn()
    for best_of in (1, 3, 5):
        assert prob("A", "B", best_of) + prob("B", "A", best_of) == pytest.approx(1.0)
    assert 0.5 < prob("A", "B", 1) < prob("A", "B", 3) < prob("A", "B", 5)
    assert prob("A", "B", 1) == pytest.approx(1 / (1 + np.exp(-0.2 * 4)))


def test_prob_fn_plugs_into_simulator():
    names = [f"T{i}" for i in range(16)]
    model = B0Model(0.2, "points", {n: 2000.0 - 50 * i for i, n in enumerate(names)})
    result = simulate_stage(
        model.prob_fn(), StageState.new(names), 2000, np.random.default_rng(0)
    )
    assert sum(result.advance_probabilities().values()) == pytest.approx(8.0)


def test_metrics():
    assert log_loss_each(0.5, True) == pytest.approx(np.log(2))
    assert log_loss_each(0.8, False) == pytest.approx(-np.log(0.2))
    assert brier_each(0.8, True) == pytest.approx(0.04)
    values = np.array([1.0, 1.0, 1.0, 1.0])
    low, high = cluster_bootstrap_ci(values, np.array([1, 1, 2, 3]), np.random.default_rng(0))
    assert low == high == 1.0


def synthetic_matches(n=3000, seed=3):
    rng = np.random.default_rng(seed)
    dates = pd.Timestamp("2025-06-02") + pd.to_timedelta(np.sort(rng.integers(0, 500, n)), "D")
    a, b = rng.integers(800, 2000, n), rng.integers(800, 2000, n)
    won = rng.random(n) < series_win_probability(0.15, features(a, b, "points"), 3)
    return pd.DataFrame(
        {
            "date": dates,
            "points_a": a,
            "points_b": b,
            "rank_a": rng.integers(1, 200, n),
            "rank_b": rng.integers(1, 200, n),
            "team_a_won": won,
            "rating_snapshot": dates - pd.Timedelta(days=1),
        }
    )


def test_walk_forward_does_not_use_the_future():
    data = rated_matches(synthetic_matches())
    p, p_favorite, tested = walk_forward(data, "points", "todas")
    # Inverter todos os resultados a partir de março/2026 não muda previsões anteriores
    # nem as do próprio mês de março (ajustadas só com dados anteriores a ele).
    changed = data.copy()
    later = changed["date"] >= pd.Timestamp("2026-03-01")
    changed.loc[later, "team_a_won"] = ~changed.loc[later, "team_a_won"]
    p2, p_favorite2, _ = walk_forward(changed, "points", "todas")
    until_march = tested & (data["date"] < pd.Timestamp("2026-04-01")).to_numpy()
    np.testing.assert_array_equal(p[until_march], p2[until_march])
    np.testing.assert_array_equal(p_favorite[until_march], p_favorite2[until_march])
    assert not np.array_equal(p[tested], p2[tested])
    assert not tested[(data["date"] < pd.Timestamp("2025-09-01")).to_numpy()].any()


def test_calibration_window_excludes_the_major_and_rejects_leakage():
    data = synthetic_matches(50)
    extra = data.iloc[:2].assign(
        date=[pd.Timestamp("2026-11-23"), pd.Timestamp("2025-05-31")],
        rating_snapshot=pd.Timestamp("2025-05-01"),
    )
    kept = rated_matches(pd.concat([data, extra]))
    assert kept["date"].max() < pd.Timestamp("2026-11-23")
    assert kept["date"].min() >= pd.Timestamp("2025-06-01")
    leaked = data.assign(rating_snapshot=data["date"])
    with pytest.raises(ValueError, match="vazamento"):
        rated_matches(leaked)
