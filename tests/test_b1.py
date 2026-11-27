"""B1 (ratings por partida), protocolo de avaliação e regra do formato (dados sintéticos)."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from backtest.b1_selection import analyze, evaluation_mask, prepare, rating_differences
from backtest.h10_format import (
    fit_beta_given_w,
    format_rule,
    mixture_probability,
    profile,
    profile_interval,
)
from backtest.protocol import monthly_folds, period_mask, wilson_interval
from models.ratings import (
    Elo,
    EloConfig,
    Game,
    Glicko,
    GlickoConfig,
    Side,
    TeamRegistry,
    glicko_update,
)

DAY1, DAY2 = date(2026, 1, 1), date(2026, 1, 11)


def game(a, b, a_won=True, points=(None, None)):
    return Game(Side(a, points[0]), Side(b, points[1]), a_won)


def test_registry_identifies_by_roster():
    registry = TeamRegistry()
    first = registry.resolve("Alpha", frozenset("abcde"))
    assert registry.resolve("Renamed", frozenset("abcxy")) == first  # 3 em comum
    assert registry.resolve("Alpha", frozenset("vwxyz")) != first  # mesmo nome, outro elenco
    assert registry.find("renamed", frozenset()) == first  # elenco desconhecido: pelo nome
    # O elenco mais recente é que vale.
    assert registry.resolve("Alpha", frozenset("abcde")) == first
    assert registry.find("x", frozenset("defgh")) is None


def test_elo_is_zero_sum_and_uses_no_same_day_information():
    config = EloConfig(s=0.0, k=20, half_life=None, provisional=1)
    elo = Elo(config)
    assert elo.process_day(DAY1, [game(0, 1), game(0, 2)]) == [0.0, 0.0]
    ratings = [elo.rating(Side(i, None), DAY1) for i in range(3)]
    assert ratings == pytest.approx([1520, 1490, 1490])
    other = Elo(config)
    other.process_day(DAY1, [game(0, 2), game(0, 1)])
    assert [other.rating(Side(i, None), DAY1) for i in range(3)] == pytest.approx(ratings)


def test_elo_prior_decay_and_provisional_boost():
    elo = Elo(EloConfig(s=0.5, k=20, half_life=10, provisional=2))
    assert elo.rating(Side(0, 1400), DAY1) == 1700
    assert elo.process_day(DAY1, [game(0, 1, points=(1400, 1000))]) == [200.0]
    gained = elo.rating(Side(0, 1400), DAY1) - 1700
    assert gained == pytest.approx(40 * (1 - 1 / (1 + 10 ** (-0.5))))
    # Dez dias = uma meia-vida; o desvio cai à metade em direção ao prior do dia.
    assert elo.rating(Side(0, 1400), DAY2) == pytest.approx(1700 + gained / 2)
    # Se o prior muda (novo snapshot), o desvio é medido e decai em relação ao novo.
    assert elo.rating(Side(0, 1600), DAY2) == pytest.approx(1800 + (1700 + gained - 1800) / 2)


def test_glicko_matches_published_example():
    """Exemplo Glicko-1 de Glickman: 1500/200 contra 1400 (V), 1550 (D) e 1700 (D)."""
    rating, rd = glicko_update(1500, 200, [(1400, 30, 1.0), (1550, 100, 0.0), (1700, 300, 0.0)])
    assert rating == pytest.approx(1464.1, abs=0.1)
    assert rd == pytest.approx(151.4, abs=0.1)


def test_glicko_rd_shrinks_with_games_and_grows_with_time():
    glicko = Glicko(GlickoConfig(rd0=200, c=10, s=0.0))
    glicko.process_day(DAY1, [game(0, 1)])
    after = glicko._current(Side(0, None), DAY1)
    later = glicko._current(Side(0, None), DAY2)
    assert after[1] < 200 and later[1] > after[1] and later[0] == after[0] > 1500


def synthetic(n=2500, teams=40, seed=5):
    rng = np.random.default_rng(seed)
    strength = rng.normal(0, 1.2, teams)
    dates = pd.Timestamp("2025-06-01") + pd.to_timedelta(np.sort(rng.integers(0, 535, n)), "D")
    a = rng.integers(0, teams, n)
    b = (a + rng.integers(1, teams, n)) % teams
    won = rng.random(n) < 1 / (1 + np.exp(-(strength[a] - strength[b])))
    roster = [", ".join(f"p{t}_{i}" for i in range(5)) for t in range(teams)]
    points = rng.integers(900, 1900, teams)  # VRS sem informação sobre a força real
    return pd.DataFrame(
        {
            "date": dates,
            "team_a": [f"T{t}" for t in a],
            "team_b": [f"T{t}" for t in b],
            "roster_a": [roster[t] for t in a],
            "roster_b": [roster[t] for t in b],
            "points_a": pd.array(points[a], dtype="Int64"),
            "points_b": pd.array(points[b], dtype="Int64"),
            "rank_a": pd.array(a + 1, dtype="Int64"),
            "rank_b": pd.array(b + 1, dtype="Int64"),
            "team_a_won": won,
            "rating_snapshot": dates - pd.Timedelta(days=1),
        }
    )


@pytest.mark.parametrize("config", [EloConfig(0.5, 30, 90, 2), GlickoConfig(200, 20, 0.5)])
def test_ratings_never_see_the_future_or_the_same_day(config):
    table = synthetic()
    data, days, _ = prepare(table)
    base, _ = rating_differences(config, days, len(data))
    cut = pd.Timestamp("2026-03-15")
    changed = table.copy()
    later = changed["date"] >= cut
    changed.loc[later, "team_a_won"] = ~changed.loc[later, "team_a_won"]
    data2, days2, _ = prepare(changed)
    new, _ = rating_differences(config, days2, len(data2))
    until = (data["date"] <= cut).to_numpy()  # inclui o próprio dia alterado
    np.testing.assert_array_equal(base[until], new[until])
    assert not np.array_equal(base, new)


def test_b1_beats_uninformative_vrs_on_synthetic_data():
    result = analyze(synthetic(), configs=[EloConfig(0.0, 30, None, 1), EloConfig(0.0, 10, 60, 1)])
    assert result["dev"]["n_configs"] == 2
    assert result["test"]["b1_minus_b0"]["log_loss"] < 0
    assert result["meets_statistical_criterion"]
    assert result["train_last"] < "2026-11-23"


def test_selection_does_not_look_at_the_test_period():
    """Inverter todos os resultados do teste não muda a escolha nem os números do dev."""
    configs = [EloConfig(0.0, k, h, m) for k in (10, 40) for h in (60, None) for m in (1, 2)]
    table = synthetic()
    base = analyze(table, configs=configs)
    changed = table.copy()
    later = changed["date"] >= pd.Timestamp("2026-06-01")
    changed.loc[later, "team_a_won"] = ~changed.loc[later, "team_a_won"]
    other = analyze(changed, configs=configs)
    assert other["dev"] == base["dev"]
    assert other["chosen"] == base["chosen"] and other["b0_config"] == base["b0_config"]
    # O beta do primeiro mês do teste só usa partidas anteriores a ele.
    assert other["test"]["monthly_betas"][0] == base["test"]["monthly_betas"][0]
    assert other["test"]["b1"] != base["test"]["b1"]


@pytest.mark.parametrize("config", [EloConfig(0.0, 20, None, 2), GlickoConfig(200, 20, 0.0)])
def test_same_day_results_do_not_change_same_day_differences(config):
    """O mesmo time joga duas vezes no dia: a segunda diferença não vê a primeira."""
    elo = Elo(config) if isinstance(config, EloConfig) else Glicko(config)
    assert elo.process_day(DAY1, [game(0, 1), game(0, 2)]) == [0.0, 0.0]


def test_cutoff_and_target():
    table = synthetic(200)
    table.loc[0, "date"] = pd.Timestamp("2026-11-23")
    table.loc[1, "rank_a"] = 500
    data, _, _ = prepare(table)
    assert len(data) == 199 and data["date"].max() < pd.Timestamp("2026-11-23")
    mask = evaluation_mask(data)
    assert mask.sum() == ((data["rank_a"] <= 100) & (data["rank_b"] <= 100)).sum() == 198


def test_monthly_folds_train_only_on_the_past():
    dates = pd.Series(pd.date_range("2025-06-01", "2026-11-22", freq="D"))
    for period in ("dev", "test"):
        covered = np.zeros(len(dates), dtype=bool)
        for train, test in monthly_folds(dates, period):
            assert dates[train].max() < dates[test].min()
            covered |= test
        np.testing.assert_array_equal(covered, period_mask(dates, period))
    assert not (period_mask(dates, "dev") & period_mask(dates, "test")).any()


def test_mixture_and_fit_recover_parameters():
    rng = np.random.default_rng(0)
    x = rng.uniform(-6, 6, 50_000)
    assert mixture_probability(0.0, 0.2, 2.0) != mixture_probability(1.0, 0.2, 2.0)
    won = rng.random(x.size) < mixture_probability(1.0, 0.3, x)
    beta, _ = fit_beta_given_w(1.0, x, won, np.ones(x.size))
    assert beta == pytest.approx(0.3, abs=0.01)
    betas, values = profile(x, won, grid=np.array([0.0, 0.5, 1.0]))
    assert betas[0] < betas[1] < betas[2]  # forma Bo3 precisa de beta menor
    low, high = profile_interval(values, np.array([0.0, 0.5, 1.0]))
    assert low <= 1.0 <= high


def test_format_rule():
    betas = np.linspace(0.1, 0.2, 101)
    wide = format_rule(0.7, [(0.6, 0.8), (0.0, 0.75)], betas)
    assert wide["mode"] == "faixa" and [v["w"] for v in wide["variants"]] == [0.0, 1.0]
    assert [v["beta"] for v in wide["variants"]] == pytest.approx([0.1, 0.2])
    narrow = format_rule(0.7, [(0.55, 0.85), (0.6, 0.8)], betas)
    assert narrow["mode"] == "estimado" and narrow["variants"][0]["beta"] == pytest.approx(0.17)


def test_wilson_interval():
    low, high = wilson_interval(12, 21)
    assert (low, high) == pytest.approx((0.365, 0.755), abs=0.002)
