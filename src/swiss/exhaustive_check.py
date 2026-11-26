"""Verificação exaustiva dos emparelhamentos em todos os caminhos de um stage.

Uso (demora vários minutos e usa vários núcleos)::

    python -m swiss.exhaustive_check

Responde:
1. Em quantas combinações de resultados das rodadas 1 e 2 o "melhor x pior" sem
   retrocesso trava na rodada 3.
2. Se existe algum caminho em que as rodadas 3, 4 ou 5 não têm emparelhamento sem
   rematch (usando a resolução H1 na rodada 3).
"""

from __future__ import annotations

import itertools
import os
from multiprocessing import Pool

import numpy as np

from .engine import apply_results, current_round, pair_round, records, standings
from .simulate import _pair_round_batch
from .state import StageState

NAMES = tuple(f"T{seed:02d}" for seed in range(1, 17))
_R2_STATES: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None


def _naive_high_low_dead_end(state: StageState) -> bool:
    """Indica se a escolha gulosa sem retrocesso trava em algum grupo da rodada atual."""
    current = records(state)
    played = {m.pair for m in state.matches}
    for record in ((2, 0), (1, 1), (0, 2)):
        group = [n for n in standings(state) if current[n] == record]
        while group:
            top = group.pop(0)
            options = [o for o in reversed(group) if frozenset((top, o)) not in played]
            if not options:
                return True
            group.remove(options[0])
    return False


def _states_after_round_two() -> tuple[list[StageState], int]:
    """Todos os estados após a rodada 2 e quantos travariam sem retrocesso."""
    states = [StageState.new(NAMES)]
    for _ in range(2):
        expanded = []
        for state in states:
            pairings = pair_round(state)
            for bits in itertools.product((False, True), repeat=len(pairings)):
                results = [
                    (p.team_b, p.team_a) if flip else (p.team_a, p.team_b)
                    for p, flip in zip(pairings, bits)
                ]
                expanded.append(apply_results(state, results))
        states = expanded
    assert all(current_round(s) == 3 for s in states)
    return states, sum(_naive_high_low_dead_end(s) for s in states)


def _arrays(states: list[StageState]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    index = {name: i for i, name in enumerate(NAMES)}
    n = len(states)
    wins = np.zeros((n, 16), dtype=np.int8)
    losses = np.zeros((n, 16), dtype=np.int8)
    played = np.zeros((n, 16, 16), dtype=bool)
    for row, state in enumerate(states):
        for name, (w, l_) in records(state).items():
            wins[row, index[name]] = w
            losses[row, index[name]] = l_
        for m in state.matches:
            a, b = index[m.team_a], index[m.team_b]
            played[row, a, b] = played[row, b, a] = True
    return wins, losses, played


def _expand(wins, losses, played, a, b):
    """Duplica cada estado para todos os 2^k resultados das k partidas."""
    n, k = a.shape
    outcomes = (np.arange(2**k)[:, None] >> np.arange(k)) & 1  # (2^k, k)
    wins = np.repeat(wins, 2**k, axis=0)
    losses = np.repeat(losses, 2**k, axis=0)
    played = np.repeat(played, 2**k, axis=0)
    a = np.repeat(a, 2**k, axis=0)
    b = np.repeat(b, 2**k, axis=0)
    a_wins = np.tile(outcomes, (n, 1)).astype(bool)
    rows = np.arange(len(wins))[:, None]
    wins[rows, np.where(a_wins, a, b)] += 1
    losses[rows, np.where(a_wins, b, a)] += 1
    played[rows, a, b] = True
    played[rows, b, a] = True
    return wins, losses, played


def _init_worker(arrays) -> None:
    global _R2_STATES
    _R2_STATES = arrays


def _check_block(block: tuple[int, int]) -> tuple[int, int]:
    """Expande as rodadas 3 e 4 de um bloco de estados; levanta se faltar pareamento."""
    assert _R2_STATES is not None
    state = tuple(x[block[0] : block[1]] for x in _R2_STATES)
    for round_number in (3, 4):
        a, b = _pair_round_batch(round_number, *state)
        state = _expand(*state, a, b)
    _pair_round_batch(5, *state)
    return (block[1] - block[0]) * 256, len(state[0])


def main() -> None:
    states, dead_ends = _states_after_round_two()
    total = len(states)
    print(f"Resultados R1 x R2: {total}", flush=True)
    print(
        f"R3 trava com 'melhor x pior' sem retrocesso em {dead_ends} deles "
        f"({dead_ends / total:.2%})",
        flush=True,
    )
    arrays = _arrays(states)
    blocks = [(i, min(i + 16, total)) for i in range(0, total, 16)]
    checked_r4 = checked_r5 = 0
    workers = max(1, (os.cpu_count() or 2) - 2)
    with Pool(workers, initializer=_init_worker, initargs=(arrays,)) as pool:
        for done, (r4, r5) in enumerate(pool.imap_unordered(_check_block, blocks), start=1):
            checked_r4 += r4
            checked_r5 += r5
            if done % 512 == 0:
                print(f"  {done}/{len(blocks)} blocos", flush=True)
    print(f"R4: {checked_r4} históricos, todos com emparelhamento sem rematch")
    print(f"R5: {checked_r5} históricos, todos com emparelhamento sem rematch")


if __name__ == "__main__":
    main()
