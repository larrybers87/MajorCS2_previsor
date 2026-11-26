"""Simulador vetorizado: equivalência com a engine, invariantes e uso ao vivo."""

import numpy as np
import pytest
from conftest import NAMES, play, random_stage, t

from swiss import (
    announce_pairings,
    apply_results,
    pair_round,
    records,
    seed_strength_prob_fn,
    series_probability,
    simulate_stage,
    standings,
)
from swiss.rules import FINAL_RECORD_COUNTS, FINAL_RECORD_LABELS
from swiss.simulate import _initial_arrays, _pair_round_batch

TEST_PROB = seed_strength_prob_fn(NAMES)


def coin(team_a, team_b, best_of):
    return 0.5


def favorite(team_a, team_b, best_of):
    return 1.0 if team_a < team_b else 0.0


def simulate(prob_fn, state, n_sims, seed=0, **kwargs):
    return simulate_stage(prob_fn, state, n_sims, np.random.default_rng(seed), **kwargs)


def test_vectorized_pairing_matches_reference_engine():
    rng = np.random.default_rng(7)
    for _ in range(1500):
        state = random_stage(rng)
        for round_number in range(2, 6):
            history = state.before_round(round_number)
            arrays = _initial_arrays(history, round_number, 1)
            a, b = _pair_round_batch(round_number, *arrays)
            got = [(NAMES[i], NAMES[j]) for i, j in zip(a[0], b[0])]
            assert got == [(p.team_a, p.team_b) for p in pair_round(history)]


def test_large_simulation_totals(new_state):
    n = 200_000
    result = simulate(TEST_PROB, new_state, n)

    # Cada time termina em exatamente um cartel.
    np.testing.assert_array_equal(result.record_counts.sum(axis=1), n)
    # Cada cartel tem sempre o mesmo número de times.
    np.testing.assert_array_equal(
        result.record_counts.sum(axis=0), np.array(FINAL_RECORD_COUNTS) * n
    )
    np.testing.assert_array_equal(result.position_counts.sum(axis=1), n)
    np.testing.assert_array_equal(result.position_counts.sum(axis=0), n)

    for probs in result.record_probabilities().values():
        assert list(probs) == list(FINAL_RECORD_LABELS)
        assert sum(probs.values()) == pytest.approx(1.0)
    advance = result.advance_probabilities()
    assert sum(advance.values()) == pytest.approx(8.0)
    # Sanidade da prob_fn de teste: o seed 1 avança mais que o 16.
    assert advance[t(1)] > 0.8 > 0.2 > advance[t(16)]
    # Avançar equivale a terminar entre as 8 primeiras posições.
    for name, probs in result.position_probabilities().items():
        assert probs[:8].sum() == pytest.approx(advance[name])


def test_fair_coin_matches_analytic_distribution(new_state):
    """Com p = 0,5 cada time tem a distribuição binomial: 1/8, 3/16, 3/16, ..."""
    result = simulate(coin, new_state, 200_000)
    expected = np.array([1 / 8, 3 / 16, 3 / 16, 3 / 16, 3 / 16, 1 / 8])
    np.testing.assert_allclose(result.record_counts / result.n_sims, np.tile(expected, (16, 1)),
                               atol=0.005)  # fmt: skip


def test_deterministic_favorite_matches_hand_derived_path(new_state):
    result = simulate(favorite, new_state, 100)
    expected_column = [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5]
    for i, column in enumerate(expected_column):
        assert result.record_counts[i, column] == 100
    np.testing.assert_array_equal(result.position_counts, np.eye(16, dtype=int) * 100)


def test_same_seed_is_reproducible_and_chunks_are_consistent(new_state):
    first = simulate(TEST_PROB, new_state, 5000, seed=3)
    second = simulate(TEST_PROB, new_state, 5000, seed=3)
    np.testing.assert_array_equal(first.record_counts, second.record_counts)
    chunked = simulate(TEST_PROB, new_state, 5000, seed=3, chunk_size=777)
    np.testing.assert_array_equal(chunked.record_counts.sum(axis=1), 5000)


def test_played_results_are_facts(new_state):
    state = play(new_state, winners=[9, 10, 11, 12, 13, 14, 15, 16])
    probs = simulate(coin, state, 20_000).record_probabilities()
    for seed in range(1, 9):  # perderam na rodada 1
        assert probs[t(seed)]["3-0"] == 0.0
    for seed in range(9, 17):  # venceram na rodada 1
        assert probs[t(seed)]["0-3"] == 0.0
        assert probs[t(seed)]["3-0"] == pytest.approx(0.25, abs=0.02)


def test_partial_round_keeps_decided_match_and_samples_the_rest(new_state):
    state = apply_results(new_state, [(t(9), t(1))])
    probs = simulate(coin, state, 40_000).record_probabilities()
    assert probs[t(1)]["3-0"] == 0.0
    assert probs[t(9)]["0-3"] == 0.0
    assert probs[t(2)]["3-0"] == pytest.approx(1 / 8, abs=0.01)


def test_announced_pairings_are_used(new_state):
    # Confronto oficial diferente da engine: 1 x 2 na rodada 1.
    official = [(t(2 * i + 1), t(2 * i + 2)) for i in range(8)]
    state = announce_pairings(new_state, official)

    def prob_fn(a, b, best_of):
        return 1.0 if a < b else 0.0

    with pytest.warns(UserWarning, match="difere do da engine"):
        probs = simulate(prob_fn, state, 100).record_probabilities()
    assert probs[t(2)]["3-0"] == 0.0  # perdeu de 1 na rodada 1
    assert probs[t(3)]["3-0"] + probs[t(3)]["3-1"] + probs[t(3)]["3-2"] == 1.0


def test_finished_stage_returns_actual_records():
    state = random_stage(np.random.default_rng(11))
    result = simulate(coin, state, 50)
    for name, probs in result.record_probabilities().items():
        wins, losses = records(state)[name]
        assert probs[f"{wins}-{losses}"] == 1.0
    order = standings(state)
    for name, probs in result.position_probabilities().items():
        assert probs[order.index(name)] == 1.0


@pytest.mark.parametrize("rounds_played", [1, 2, 3, 4])
def test_live_state_from_any_round(rounds_played):
    full = random_stage(np.random.default_rng(100 + rounds_played))
    state = full.before_round(rounds_played + 1)
    result = simulate(TEST_PROB, state, 5000)
    np.testing.assert_array_equal(
        result.record_counts.sum(axis=0), np.array(FINAL_RECORD_COUNTS) * 5000
    )
    current = records(state)
    for name, probs in result.record_probabilities().items():
        for label, p in probs.items():
            wins, losses = map(int, label.split("-"))
            if wins < current[name][0] or losses < current[name][1]:
                assert p == 0.0


@pytest.mark.parametrize(("all_bo3", "formats"), [(False, {1, 3}), (True, {3})])
def test_formats_requested_from_prob_fn(all_bo3, formats):
    from swiss import StageState

    seen = set()

    def prob_fn(a, b, best_of):
        seen.add(best_of)
        return 0.5

    simulate(prob_fn, StageState.new(NAMES, all_best_of_three=all_bo3), 10)
    assert seen == formats


def test_bo1_and_bo3_probabilities_are_applied_to_the_right_matches(new_state):
    """Bo1 sempre vencido pelo melhor seed e Bo3 pelo pior: o 3-0 exige perder a decisiva."""

    def prob_fn(a, b, best_of):
        better_seed_wins = a < b
        if best_of == 1:
            return 1.0 if better_seed_wins else 0.0
        return 0.0 if better_seed_wins else 1.0

    probs = simulate(prob_fn, new_state, 10).record_probabilities()
    # R1 e R2 são Bo1 (1 e 2 chegam a 2-0, como o 3 e o 4); R3 2-0 é Bo3: vencem 4 e 3.
    assert probs[t(4)]["3-0"] == 1.0
    assert probs[t(3)]["3-0"] == 1.0
    assert probs[t(1)]["3-0"] == 0.0


@pytest.mark.parametrize("value", [-0.1, 1.5, float("nan")])
def test_invalid_probability_is_rejected(new_state, value):
    with pytest.raises(ValueError):
        simulate(lambda a, b, f: value, new_state, 10)


def test_series_probability():
    assert series_probability(0.5, 3) == 0.5
    assert series_probability(0.7, 3) == pytest.approx(0.7**2 * (3 - 1.4))
    assert series_probability(0.7, 1) == 0.7
    # Bo5 contra a soma binomial: vence com 0, 1 ou 2 mapas perdidos.
    assert series_probability(0.7, 5) == pytest.approx(
        0.7**3 + 3 * 0.7**3 * 0.3 + 6 * 0.7**3 * 0.3**2
    )
    assert series_probability(0.5, 5) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        series_probability(0.5, 2)
