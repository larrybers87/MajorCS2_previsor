"""Invariantes do formato e validação do estado."""

from collections import Counter

import numpy as np
import pytest
from conftest import NAMES, play, random_stage, t

from swiss import (
    Match,
    StageState,
    Team,
    advancing_teams,
    announce_pairings,
    apply_results,
    buchholz,
    check_pairings,
    current_round,
    pair_round,
    records,
)
from swiss.rules import FINAL_RECORD_COUNTS, FINAL_RECORDS, MATCHES_PER_ROUND


def test_invariants_over_random_stages():
    rng = np.random.default_rng(20261126)
    for _ in range(2000):
        state = random_stage(rng)

        assert len(state.matches) == 33
        assert max(m.round for m in state.matches) == 5
        per_round = Counter(m.round for m in state.matches)
        assert tuple(per_round[r] for r in range(1, 6)) == MATCHES_PER_ROUND
        # Ninguém joga duas vezes contra o mesmo adversário.
        assert len({m.pair for m in state.matches}) == 33
        # Só se enfrentam times com o mesmo cartel.
        for round_number in range(1, 6):
            before = records(state.before_round(round_number))
            for m in state.round_matches(round_number):
                assert before[m.team_a] == before[m.team_b]

        final = records(state)
        distribution = Counter(final.values())
        assert tuple(distribution[r] for r in FINAL_RECORDS) == FINAL_RECORD_COUNTS
        assert sum(w == 3 for w, _ in final.values()) == 8
        assert sum(losses == 3 for _, losses in final.values()) == 8
        assert len(advancing_teams(state)) == 8
        assert all(final[n][0] == 3 for n in advancing_teams(state))
        # Consequência aritmética: a soma dos Buchholz finais é zero.
        assert sum(buchholz(state).values()) == 0


def test_pair_round_ignores_results_of_current_round(new_state):
    state = play(new_state, winners=list(range(1, 9)))
    full = pair_round(state)
    partial = apply_results(state, [(full[0].team_a, full[0].team_b)])
    assert pair_round(partial) == full
    assert current_round(partial) == 2


def test_apply_results_is_pure(new_state):
    apply_results(new_state, [(t(1), t(9))])
    assert new_state.matches == ()


def test_apply_results_rejects_pair_outside_engine(new_state):
    with pytest.raises(ValueError, match="announce_pairings"):
        apply_results(new_state, [(t(1), t(2))])


def test_apply_results_rejects_duplicate_result(new_state):
    state = apply_results(new_state, [(t(1), t(9))])
    with pytest.raises(ValueError, match="já registrado"):
        apply_results(state, [(t(9), t(1))])


def test_apply_results_accepts_several_rounds_in_order(new_state):
    expected = play(play(new_state, list(range(1, 9))), [1, 2, 3, 4, 9, 10, 11, 12])
    results = [(m.winner, next(iter(m.pair - {m.winner}))) for m in expected.matches]
    assert apply_results(new_state, results) == expected


def test_announced_pairings_override_engine_and_are_reported(new_state):
    official = [(t(2 * i + 1), t(2 * i + 2)) for i in range(8)]
    state = announce_pairings(new_state, official)
    state = apply_results(state, official)
    assert current_round(state) == 2
    mismatches = check_pairings(state)
    assert [m.round for m in mismatches] == [1]


def test_announce_requires_full_round(new_state):
    with pytest.raises(ValueError):
        announce_pairings(new_state, [(t(1), t(9))])


@pytest.mark.parametrize(
    "matches",
    [
        [Match(2, "T01", "T02")],  # rodada 1 incompleta
        [Match(1, "T01", "T09"), Match(1, "T01", "T10")],  # duas partidas na rodada
        [Match(1, "T01", "T01")],
        [Match(1, "T01", "XXX")],
        [Match(1, "T01", "T09", winner="T02")],
        [Match(6, "T01", "T09")],
    ],
)
def test_state_rejects_inconsistent_matches(matches):
    with pytest.raises(ValueError):
        StageState.new(NAMES).with_matches(matches)


def test_state_rejects_different_records(new_state):
    state = play(new_state, winners=list(range(1, 9)))
    with pytest.raises(ValueError, match="cartéis diferentes"):
        state.with_matches((*state.matches, Match(2, t(1), t(9))))


def test_state_validates_seeds():
    with pytest.raises(ValueError):
        StageState.new(NAMES[:15])
    teams = tuple(Team(n, 1) for n in NAMES)
    with pytest.raises(ValueError):
        StageState(teams)


@pytest.mark.skip(reason="V2 do design: aguarda resultados reais de eventos passados em data/")
def test_v2_reproduces_real_pairings():
    """Gancho da validação V2: 100% de coincidência com os emparelhamentos reais.

    Para cada stage histórico: criar ``StageState`` com os seeds iniciais oficiais,
    registrar todas as partidas reais (rodada, times, vencedor) como ``Match`` e
    exigir ``check_pairings(state) == []``.
    """
    historical_stages: list[StageState] = []  # preencher a partir de data/processed
    assert historical_stages, "sem dados históricos"
    for state in historical_stages:
        assert check_pairings(state) == []
