"""Formato do Singapore 2026 (decisão 2 da sessão 02; ver ``docs/decisoes.md``).

Stage 3 todo em Bo3, final em Bo5 e disputa de 3º lugar NÃO constam no rulebook da
Valve: são decisões adotadas com base na imprensa, **sem confirmação oficial legível**.

Para trocar quando a fonte oficial for confirmada, mude ``ACTIVE_FORMAT``: ``anunciado``
(imprensa) ou ``rulebook`` (texto da Valve). Se a fonte oficial disser outra coisa,
ajuste os campos de ``ANNOUNCED``.
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


ANNOUNCED = TournamentFormat()
# Rulebook: Bo1 fora de avanço/eliminação em todo stage suíço, playoffs todos em Bo3 e
# nenhuma disputa de 3º lugar prevista.
RULEBOOK = TournamentFormat(
    all_best_of_three_stages=frozenset(), final_best_of=3, third_place_match=False
)
FORMATS = {"anunciado": ANNOUNCED, "rulebook": RULEBOOK}

ACTIVE_FORMAT = "anunciado"
DEFAULT_FORMAT = FORMATS[ACTIVE_FORMAT]
