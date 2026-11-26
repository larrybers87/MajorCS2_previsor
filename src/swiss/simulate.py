"""Simulação Monte Carlo vetorizada de um stage suíço.

Os times são indexados por ``seed inicial - 1``. As rodadas já determinadas pelos
fatos são iguais em todas as simulações; a partir daí cada simulação é emparelhada
em lote.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .engine import (
    NoValidPairingError,
    check_pairings,
    current_round,
    pair_round,
    records,
)
from .probability import ProbFn
from .rules import (
    FINAL_RECORD_LABELS,
    FINAL_RECORDS,
    GROUP_SIZES,
    LOSSES_TO_ELIMINATE,
    MATCHES_PER_ROUND,
    N_ROUNDS,
    N_TEAMS,
    SIX_TEAM_PRIORITY,
    TABLE_ROUNDS,
    WINS_TO_ADVANCE,
)
from .state import Match, StageState


@dataclass(frozen=True)
class SimulationResult:
    """Contagens agregadas das simulações. Linhas na ordem de ``teams`` (seed inicial)."""

    teams: tuple[str, ...]
    n_sims: int
    record_counts: np.ndarray  # (16, 6), colunas na ordem de FINAL_RECORD_LABELS
    position_counts: np.ndarray  # (16, 16), coluna k = posição final k+1

    def record_probabilities(self) -> dict[str, dict[str, float]]:
        probs = self.record_counts / self.n_sims
        return {
            name: dict(zip(FINAL_RECORD_LABELS, map(float, probs[i])))
            for i, name in enumerate(self.teams)
        }

    def advance_probabilities(self) -> dict[str, float]:
        advanced = [i for i, (wins, _) in enumerate(FINAL_RECORDS) if wins == WINS_TO_ADVANCE]
        probs = self.record_counts[:, advanced].sum(axis=1) / self.n_sims
        return {name: float(probs[i]) for i, name in enumerate(self.teams)}

    def position_probabilities(self) -> dict[str, np.ndarray]:
        """Posição final (1..16) pelo "Mid-stage Seed Calculation" ao fim do stage."""
        probs = self.position_counts / self.n_sims
        return {name: probs[i] for i, name in enumerate(self.teams)}


def _ordered_matchings(size: int) -> list[list[tuple[int, int]]]:
    """Todos os emparelhamentos perfeitos de ``range(size)`` em ordem de prioridade
    "melhor x pior": a primeira posição tenta o último, depois o penúltimo etc.

    O primeiro item sem rematch desta lista equivale à busca com retrocesso de
    ``engine._pair_high_low``.
    """

    def build(items: list[int]) -> list[list[tuple[int, int]]]:
        if not items:
            return [[]]
        top, rest = items[0], items[1:]
        result = []
        for i in range(len(rest) - 1, -1, -1):
            for tail in build(rest[:i] + rest[i + 1 :]):
                result.append([(top, rest[i]), *tail])
        return result

    return build(list(range(size)))


_HIGH_LOW_MATCHINGS = {size: np.array(_ordered_matchings(size)) for size in (4, 8)}
_TABLE_MATCHINGS = np.array(SIX_TEAM_PRIORITY) - 1


def _pair_round_batch(
    round_number: int, wins: np.ndarray, losses: np.ndarray, played: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Emparelha a rodada ``round_number`` (2..5) para um lote de simulações.

    ``wins``/``losses``: (n, 16); ``played``: (n, 16, 16) bool.
    Retorna índices ``team_a`` e ``team_b``, ambos (n, partidas), na mesma ordem de
    ``engine.pair_round``.
    """
    n = wins.shape[0]
    net = (wins - losses).astype(np.int32)
    difficulty = np.einsum("nij,nj->ni", played.astype(np.int32), net)
    active = (wins < WINS_TO_ADVANCE) & (losses < LOSSES_TO_ELIMINATE)
    # Chave inteira: ativo, mais vitórias, Buchholz maior, seed inicial menor.
    key = (
        (~active) * 1_000_000
        + (WINS_TO_ADVANCE - wins.astype(np.int32)) * 10_000
        + (100 - difficulty) * N_TEAMS
        + np.arange(N_TEAMS)
    )
    order = np.argsort(key, axis=1)

    rows = np.arange(n)[:, None]
    a_parts, b_parts = [], []
    start = 0
    for size in GROUP_SIZES[round_number]:
        group = order[:, start : start + size]
        start += size
        matchings = (
            _TABLE_MATCHINGS if round_number in TABLE_ROUNDS else _HIGH_LOW_MATCHINGS[size]
        )
        rematch = played[rows[:, :, None], group[:, :, None], group[:, None, :]]
        valid = ~rematch[:, matchings[:, :, 0], matchings[:, :, 1]].any(axis=2)
        if not valid.any(axis=1).all():
            bad = int((~valid.any(axis=1)).sum())
            raise NoValidPairingError(
                f"rodada {round_number}: {bad} simulação(ões) sem emparelhamento sem rematch"
            )
        chosen = matchings[valid.argmax(axis=1)]  # (n, pares, 2)
        a_parts.append(group[rows, chosen[:, :, 0]])
        b_parts.append(group[rows, chosen[:, :, 1]])
    return np.concatenate(a_parts, axis=1), np.concatenate(b_parts, axis=1)


def probability_table(
    prob_fn: ProbFn, names: Sequence[str], all_best_of_three: bool = False
) -> np.ndarray:
    """Tabela [formato, a, b] com P(a vence b). Formato 0 = Bo1, 1 = Bo3."""
    table = np.full((2, len(names), len(names)), np.nan)
    formats = (3,) if all_best_of_three else (1, 3)
    for fmt in formats:
        for i, name_a in enumerate(names):
            for j, name_b in enumerate(names):
                if i == j:
                    continue
                p = float(prob_fn(name_a, name_b, fmt))
                if not 0.0 <= p <= 1.0:
                    raise ValueError(f"prob_fn({name_a!r}, {name_b!r}, {fmt}) = {p}")
                table[fmt // 2, i, j] = p
    return table


def _current_round_matches(state: StageState, round_number: int) -> list[Match]:
    """Partidas da rodada atual: as registradas mais as que a engine completa."""
    listed = list(state.round_matches(round_number))
    if len(listed) == MATCHES_PER_ROUND[round_number - 1]:
        return listed
    expected = pair_round(state)
    expected_pairs = {p.pair for p in expected}
    listed_pairs = {m.pair for m in listed}
    if not listed_pairs <= expected_pairs:
        raise ValueError(
            f"a rodada {round_number} está incompleta e contém confrontos diferentes dos da "
            "engine; informe o emparelhamento completo da rodada"
        )
    listed.extend(
        Match(round_number, p.team_a, p.team_b) for p in expected if p.pair not in listed_pairs
    )
    return listed


def simulate_stage(
    prob_fn: ProbFn,
    current_state: StageState,
    n_sims: int,
    rng: np.random.Generator,
    chunk_size: int = 50_000,
) -> SimulationResult:
    """Simula o restante de um stage suíço.

    Resultados já registrados em ``current_state`` são fatos; partidas anunciadas sem
    resultado mantêm o confronto e sorteiam o vencedor. ``prob_fn`` é avaliada uma vez
    por par ordenado e formato (não pode depender do caminho simulado).
    """
    if n_sims <= 0 or chunk_size <= 0:
        raise ValueError("n_sims e chunk_size devem ser positivos")
    for mismatch in check_pairings(current_state):
        warnings.warn(
            f"rodada {mismatch.round}: o emparelhamento registrado difere do da engine "
            "(os fatos foram mantidos)",
            stacklevel=2,
        )
    table = probability_table(prob_fn, current_state.names, current_state.all_best_of_three)
    record_counts = np.zeros((N_TEAMS, len(FINAL_RECORDS)), dtype=np.int64)
    position_counts = np.zeros((N_TEAMS, N_TEAMS), dtype=np.int64)

    remaining = n_sims
    while remaining:
        n = min(chunk_size, remaining)
        remaining -= n
        wins, losses, played = simulate_chunk(table, current_state, n, rng)
        _accumulate(wins, losses, played, record_counts, position_counts)

    return SimulationResult(current_state.names, n_sims, record_counts, position_counts)


def _initial_arrays(
    state: StageState, round_number: int | None, n: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Arrays iniciais com as rodadas anteriores à atual (todas, se o stage acabou)."""
    history = state if round_number is None else state.before_round(round_number)
    index = {name: i for i, name in enumerate(state.names)}
    current = records(history)
    wins = np.tile(np.array([current[t][0] for t in state.names], dtype=np.int8), (n, 1))
    losses = np.tile(np.array([current[t][1] for t in state.names], dtype=np.int8), (n, 1))
    played = np.zeros((n, N_TEAMS, N_TEAMS), dtype=bool)
    for match in history.matches:
        a, b = index[match.team_a], index[match.team_b]
        played[:, a, b] = played[:, b, a] = True
    return wins, losses, played


def simulate_chunk(
    table: np.ndarray,
    state: StageState,
    n: int,
    rng: np.random.Generator,
    team_ids: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simula ``n`` caminhos e devolve vitórias, derrotas e confrontos (por seed).

    ``team_ids`` (n, 16), opcional, diz qual linha/coluna de ``table`` corresponde a
    cada seed em cada simulação; serve para encadear stages, em que os participantes
    variam entre simulações.
    """
    first_round = current_round(state)
    wins, losses, played = _initial_arrays(state, first_round, n)
    if first_round is None:
        return wins, losses, played

    index = {name: i for i, name in enumerate(state.names)}
    rows = np.arange(n)[:, None]
    for round_number in range(first_round, N_ROUNDS + 1):
        if round_number == first_round:
            matches = _current_round_matches(state, round_number)
            a = np.tile([index[m.team_a] for m in matches], (n, 1))
            b = np.tile([index[m.team_b] for m in matches], (n, 1))
            # 1 = team_a venceu, 0 = team_b venceu, -1 = a sortear
            fixed = np.array(
                [-1 if m.winner is None else int(m.winner == m.team_a) for m in matches]
            )
        else:
            a, b = _pair_round_batch(round_number, wins, losses, played)
            fixed = np.full(a.shape[1], -1)

        w, losses_a = wins[rows, a], losses[rows, a]
        if state.all_best_of_three:
            fmt = np.ones_like(a)
        else:
            fmt = ((w == WINS_TO_ADVANCE - 1) | (losses_a == LOSSES_TO_ELIMINATE - 1)).astype(int)
        if team_ids is None:
            p = table[fmt, a, b]
        else:
            p = table[fmt, team_ids[rows, a], team_ids[rows, b]]
        a_wins = rng.random(a.shape) < p
        a_wins = np.where(fixed >= 0, fixed == 1, a_wins)

        winner = np.where(a_wins, a, b)
        loser = np.where(a_wins, b, a)
        wins[rows, winner] += 1
        losses[rows, loser] += 1
        played[rows, a, b] = True
        played[rows, b, a] = True
    return wins, losses, played


def _accumulate(
    wins: np.ndarray,
    losses: np.ndarray,
    played: np.ndarray,
    record_counts: np.ndarray,
    position_counts: np.ndarray,
) -> None:
    for column, (w, l_) in enumerate(FINAL_RECORDS):
        record_counts[:, column] += ((wins == w) & (losses == l_)).sum(axis=0)

    order = final_order(wins, losses, played)
    for position in range(N_TEAMS):
        position_counts[:, position] += np.bincount(order[:, position], minlength=N_TEAMS)


def final_order(wins: np.ndarray, losses: np.ndarray, played: np.ndarray) -> np.ndarray:
    """``order[n, k]`` = índice (seed - 1) do time na posição final ``k``."""
    net = (wins - losses).astype(np.int32)
    difficulty = np.einsum("nij,nj->ni", played.astype(np.int32), net)
    key = (
        (WINS_TO_ADVANCE - wins.astype(np.int32)) * 100_000
        + losses.astype(np.int32) * 10_000
        + (100 - difficulty) * N_TEAMS
        + np.arange(N_TEAMS)
    )
    return np.argsort(key, axis=1)
