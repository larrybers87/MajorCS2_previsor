"""Utilitários compartilhados pelos testes."""

import numpy as np
import pytest

from swiss import StageState, apply_results, current_round, pair_round

NAMES = tuple(f"T{seed:02d}" for seed in range(1, 17))


def t(seed: int) -> str:
    """Nome do time de seed inicial ``seed``."""
    return NAMES[seed - 1]


def seeds_of(pairings) -> list[tuple[int, int]]:
    """Emparelhamentos como pares de seeds iniciais, preservando ordem A/B."""
    return [(int(p.team_a[1:]), int(p.team_b[1:])) for p in pairings]


def play(state: StageState, winners: list[int]) -> StageState:
    """Joga a rodada atual da engine; ``winners`` lista os seeds vencedores."""
    results = []
    for p in pair_round(state):
        chosen = [n for n in (p.team_a, p.team_b) if int(n[1:]) in winners]
        assert len(chosen) == 1, f"partida {p.team_a} x {p.team_b} sem vencedor único"
        loser = p.team_b if chosen[0] == p.team_a else p.team_a
        results.append((chosen[0], loser))
    return apply_results(state, results)


def random_stage(rng: np.random.Generator) -> StageState:
    """Stage completo com vencedores sorteados, usando a engine de referência."""
    state = StageState.new(NAMES)
    while current_round(state) is not None:
        results = []
        for p in pair_round(state):
            pair = (p.team_a, p.team_b) if rng.random() < 0.5 else (p.team_b, p.team_a)
            results.append(pair)
        state = apply_results(state, results)
    return state


@pytest.fixture
def new_state() -> StageState:
    return StageState.new(NAMES)
