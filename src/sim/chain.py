"""Simulação encadeada: restante do Stage 1 seguido do Stage 2 completo."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from swiss import ProbFn, StageState
from swiss.rules import FINAL_RECORDS, N_ADVANCING, N_TEAMS
from swiss.simulate import final_order, probability_table, simulate_chunk


@dataclass(frozen=True)
class ChainResult:
    """Contagens do Stage 2 para os 24 times (16 do Stage 1 + 8 convidados)."""

    teams: tuple[str, ...]
    n_sims: int
    participation_counts: np.ndarray  # (24,)
    record_counts: np.ndarray  # (24, 6), conjunta com a participação
    opening_counts: np.ndarray  # (8, 24): adversário de cada convidado na rodada 1


def simulate_chained(
    prob_fn: ProbFn,
    stage1: StageState,
    stage2_invited: Sequence[str],
    n_sims: int,
    rng: np.random.Generator,
    stage2_all_best_of_three: bool = False,
    chunk_size: int = 50_000,
) -> ChainResult:
    """Em cada simulação, os 8 classificados do Stage 1 viram os seeds 9-16 do Stage 2.

    A seed final do Stage 1 (cartel, Difficulty, seed inicial) define a ordem deles.
    ``prob_fn`` não muda entre os stages (probabilidades fixas na v1).
    """
    if n_sims <= 0 or chunk_size <= 0:
        raise ValueError("n_sims e chunk_size devem ser positivos")
    if len(stage2_invited) != N_TEAMS - N_ADVANCING:
        raise ValueError("o Stage 2 tem 8 convidados")
    teams = (*stage1.names, *stage2_invited)
    if len(set(teams)) != len(teams):
        raise ValueError("há time repetido entre o Stage 1 e os convidados do Stage 2")
    total = len(teams)
    table1 = probability_table(prob_fn, stage1.names, stage1.all_best_of_three)
    table2 = probability_table(prob_fn, teams, stage2_all_best_of_three)
    # Estado vazio com nomes fictícios: só os seeds importam; ``team_ids`` diz quem é quem.
    blank = StageState.new(
        [f"seed{i}" for i in range(1, N_TEAMS + 1)], stage2_all_best_of_three
    )

    participation = np.zeros(total, dtype=np.int64)
    record_counts = np.zeros((total, len(FINAL_RECORDS)), dtype=np.int64)
    opening = np.zeros((N_TEAMS - N_ADVANCING, total), dtype=np.int64)
    invited_ids = np.arange(N_TEAMS, total)

    remaining = n_sims
    while remaining:
        n = min(chunk_size, remaining)
        remaining -= n
        order = final_order(*simulate_chunk(table1, stage1, n, rng))
        ids = np.concatenate(
            [np.tile(invited_ids, (n, 1)), order[:, :N_ADVANCING]], axis=1
        )  # ids[:, k] = time com seed k+1 no Stage 2
        wins, losses, _ = simulate_chunk(table2, blank, n, rng, team_ids=ids)
        participation += np.bincount(ids.ravel(), minlength=total)
        for column, (w, l_) in enumerate(FINAL_RECORDS):
            mask = (wins == w) & (losses == l_)
            record_counts[:, column] += np.bincount(ids[mask], minlength=total)
        for i in range(N_TEAMS - N_ADVANCING):  # rodada 1: seed i+1 x seed i+9
            opening[i] += np.bincount(ids[:, N_ADVANCING + i], minlength=total)

    return ChainResult(teams, n_sims, participation, record_counts, opening)
