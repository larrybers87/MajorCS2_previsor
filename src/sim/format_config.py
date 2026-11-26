"""Formato do Singapore 2026 (decisão 2 da sessão 02; ver ``docs/decisoes.md``).

Stage 3 todo em Bo3 e final em Bo5 NÃO constam no rulebook da Valve: são decisões
adotadas com base na imprensa e ficam configuráveis aqui.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from swiss import StageState


@dataclass(frozen=True)
class TournamentFormat:
    all_best_of_three_stages: frozenset[int] = frozenset({3})
    playoff_best_of: int = 3
    final_best_of: int = 5
    third_place_match: bool = True
    third_place_best_of: int = 3  # HIPÓTESE: formato não confirmado

    def stage_state(self, stage: int, names_by_seed: Sequence[str]) -> StageState:
        """Estado inicial de um stage suíço (1, 2 ou 3) com o formato configurado."""
        if stage not in (1, 2, 3):
            raise ValueError(f"stage suíço inválido: {stage}")
        return StageState.new(
            names_by_seed, all_best_of_three=stage in self.all_best_of_three_stages
        )


DEFAULT_FORMAT = TournamentFormat()
