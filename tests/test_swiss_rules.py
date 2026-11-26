"""Casos escritos à mão a partir das regras de ``docs/regras_suica.md``.

Os números são seeds iniciais. Os valores esperados foram derivados do texto do
rulebook, não da saída da engine.
"""

import pytest
from conftest import play, seeds_of, t

from swiss import (
    NoValidPairingError,
    advancing_teams,
    best_of,
    buchholz,
    check_pairings,
    current_round,
    is_decider_match,
    pair_round,
    records,
    standings,
)
from swiss.engine import _pair_by_table, _pair_high_low
from swiss.rules import SIX_TEAM_PRIORITY


def test_round_one_is_1v9_to_8v16(new_state):
    pairings = pair_round(new_state)
    assert seeds_of(pairings) == [(s, s + 8) for s in range(1, 9)]
    assert {p.best_of for p in pairings} == {1}


@pytest.mark.parametrize(
    ("wins", "losses", "decider"),
    [
        (0, 0, False), (1, 0, False), (0, 1, False), (1, 1, False),
        (2, 0, True), (0, 2, True), (2, 1, True), (1, 2, True), (2, 2, True),
    ],
)
def test_decider_matches_are_best_of_three(wins, losses, decider):
    assert is_decider_match(wins, losses) is decider
    assert best_of(wins, losses) == (3 if decider else 1)
    assert best_of(wins, losses, all_best_of_three=True) == 3


@pytest.mark.parametrize(("wins", "losses"), [(3, 0), (0, 3), (3, 2), (-1, 0)])
def test_decider_rejects_finished_records(wins, losses):
    with pytest.raises(ValueError):
        is_decider_match(wins, losses)


def test_priority_table_has_all_15_distinct_matchings():
    matchings = set()
    for row in SIX_TEAM_PRIORITY:
        assert sorted(x for pair in row for x in pair) == [1, 2, 3, 4, 5, 6]
        matchings.add(frozenset(frozenset(pair) for pair in row))
    assert len(SIX_TEAM_PRIORITY) == len(matchings) == 15


def test_table_picks_topmost_row_without_rematch():
    group = list("ABCDEF")
    assert _pair_by_table(group, set()) == [("A", "F"), ("B", "E"), ("C", "D")]
    # A-F já jogaram: linhas 1 e 2 usam 1v6; a linha 3 é a primeira válida.
    assert _pair_by_table(group, {frozenset("AF")}) == [("A", "E"), ("B", "F"), ("C", "D")]
    # A tabela não é "melhor x pior disponível": com C-D jogado, vale a linha 2
    # (1v6, 2v4, 3v5).
    assert _pair_by_table(group, {frozenset("CD")}) == [("A", "F"), ("B", "D"), ("C", "E")]


def test_no_pairing_without_rematch_returns_none():
    group = list("ABCDEF")
    everything_with_a = {frozenset(("A", other)) for other in "BCDEF"}
    assert _pair_by_table(group, everything_with_a) is None
    assert _pair_high_low(list("ABCD"), {frozenset(("A", o)) for o in "BCD"}) is None
    assert issubclass(NoValidPairingError, RuntimeError)


# --- Caminho completo em que o melhor seed inicial sempre vence ----------------


def test_favorites_path_round_by_round(new_state):
    state = play(new_state, winners=list(range(1, 9)))

    # R2: dentro de cada grupo o Buchholz é igual, então vale o seed inicial.
    assert seeds_of(pair_round(state)) == [
        (1, 8), (2, 7), (3, 6), (4, 5), (9, 16), (10, 15), (11, 14), (12, 13),
    ]  # fmt: skip
    state = play(state, winners=[1, 2, 3, 4, 9, 10, 11, 12])

    # R3: grupos 2-0, 1-1 e 0-2, todos com Buchholz 0.
    assert set(buchholz(state).values()) == {0}
    assert seeds_of(pair_round(state)) == [
        (1, 4), (2, 3), (5, 12), (6, 11), (7, 10), (8, 9), (13, 16), (14, 15),
    ]  # fmt: skip
    assert [p.best_of for p in pair_round(state)] == [3, 3, 1, 1, 1, 1, 3, 3]
    state = play(state, winners=[1, 2, 5, 6, 7, 8, 13, 14])

    scores = buchholz(state)
    assert [scores[t(s)] for s in range(3, 15)] == [3, 3, -1, -1, -1, -1, 1, 1, 1, 1, -3, -3]
    # R4: tabela, linha 1 em ambos os grupos.
    assert seeds_of(pair_round(state)) == [(3, 8), (4, 7), (5, 6), (9, 14), (10, 13), (11, 12)]
    state = play(state, winners=[3, 4, 5, 9, 10, 11])

    # R5, grupo 2-2 ordenado por Buchholz: 6,7,8 (+2) e 9,10,11 (-2).
    scores = buchholz(state)
    assert [scores[t(s)] for s in range(6, 12)] == [2, 2, 2, -2, -2, -2]
    # Linha 1 daria 6v11 (já jogado na R3) e 8v9 (R3). Linha 2 mantém 6v11. Linha 3
    # daria 8v9. A linha 4 (1v5, 2v4, 3v6) é a primeira válida: 6v10, 7v9, 8v11.
    # O "melhor x pior disponível" daria 6v10, 7v11 e travaria em 8v9.
    assert seeds_of(pair_round(state)) == [(6, 10), (7, 9), (8, 11)]
    state = play(state, winners=[6, 7, 8])

    assert current_round(state) is None
    assert pair_round(state) == []
    final = records(state)
    expected = {
        (3, 0): [1, 2], (3, 1): [3, 4, 5], (3, 2): [6, 7, 8],
        (2, 3): [9, 10, 11], (1, 3): [12, 13, 14], (0, 3): [15, 16],
    }  # fmt: skip
    for record, seeds in expected.items():
        assert [s for s in range(1, 17) if final[t(s)] == record] == seeds
    scores = buchholz(state)
    assert [scores[t(s)] for s in range(1, 17)] == [
        2, 2, 4, 4, -1, 0, 0, 0, 0, 0, 0, 1, -4, -4, -2, -2,
    ]  # fmt: skip
    assert standings(state) == [t(s) for s in range(1, 17)]
    assert advancing_teams(state) == [t(s) for s in range(1, 9)]
    assert check_pairings(state) == []


# --- Rodada 3: escolha gulosa que travaria (HIPÓTESE H1) -----------------------


def test_round_three_dead_end_uses_backtracking(new_state):
    """Contraexemplo do auditor de regras: o "melhor x pior" literal sobra em rematch."""
    state = play(new_state, winners=[1, 2, 3, 12, 5, 14, 15, 16])
    state = play(state, winners=[16, 15, 14, 5, 4, 11, 10, 9])

    one_one = [n for n in standings(state) if records(state)[n] == (1, 1)]
    assert one_one == [t(s) for s in (1, 2, 3, 12, 4, 9, 10, 11)]
    scores = buchholz(state)
    assert [scores[n] for n in one_one] == [2, 2, 2, 2, -2, -2, -2, -2]

    group_pairs = [p for p in seeds_of(pair_round(state)) if t(p[0]) in one_one]
    # 1v11; 2v9 (2v10 é rematch); 3v10 deixaria 12v4 (rematch), então 3v4 e 12v10.
    assert group_pairs == [(1, 11), (2, 9), (3, 4), (12, 10)]


def test_higher_buchholz_ranks_first_within_record(new_state):
    """Direção do Difficulty Score: maior é melhor, antes do seed inicial."""
    state = play(new_state, winners=[1, 2, 3, 12, 5, 14, 15, 16])
    state = play(state, winners=[16, 15, 14, 5, 4, 11, 10, 9])
    order = standings(state)
    # 12 (Buchholz +2) fica acima de 4 (Buchholz -2) apesar do seed pior.
    assert order.index(t(12)) < order.index(t(4))
