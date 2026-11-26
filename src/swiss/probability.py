"""Interface de probabilidade de partida e funções de TESTE.

``prob_fn(team_a, team_b, best_of) -> float`` devolve a probabilidade de ``team_a``
vencer a série. ``team_a`` é o melhor ordenado no emparelhamento (o rulebook dá a ele
a escolha de ser "Team A" no veto). O modelo real vai implementar esta interface.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

ProbFn = Callable[[str, str, int], float]


def series_probability(map_probability: float, best_of: int) -> float:
    """Probabilidade de vencer a série com mapas independentes e probabilidade constante."""
    if best_of == 1:
        return map_probability
    if best_of == 3:
        return map_probability**2 * (3 - 2 * map_probability)
    raise ValueError(f"formato não suportado: Bo{best_of}")


def seed_strength_prob_fn(names_by_seed: Sequence[str], scale: float = 0.15) -> ProbFn:
    """``prob_fn`` de TESTE: força fixa pelo seed (logística na diferença de seeds).

    Não é um modelo; ``scale`` é arbitrário.
    """
    seed = {name: i for i, name in enumerate(names_by_seed, start=1)}

    def prob_fn(team_a: str, team_b: str, best_of: int) -> float:
        p_map = 1.0 / (1.0 + math.exp(-scale * (seed[team_b] - seed[team_a])))
        return series_probability(p_map, best_of)

    return prob_fn
