"""Modelo B0: regressão logística nos pontos do VRS, sem intercepto.

``p_mapa = logística(beta * x)``, com ``x`` uma diferença de ratings; a probabilidade
da série vem de mapas independentes (Bo1, Bo3, Bo5).

HIPÓTESE H10: o VRS não informa o formato das partidas históricas; na calibração
todas são tratadas como ``assumed_best_of`` (padrão 3).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

from swiss.probability import series_probability

TRANSFORMS = ("points", "log")
POINTS_SCALE = 100.0
_BETA_BOUNDS = (-5.0, 50.0)
_EPSILON = 1e-12


def logistic(x):
    return 1.0 / (1.0 + np.exp(-x))


def features(points_a, points_b, transform: str) -> np.ndarray:
    """Diferença de ratings: ``points`` = (A - B)/100; ``log`` = ln(A) - ln(B)."""
    a = np.asarray(points_a, dtype=float)
    b = np.asarray(points_b, dtype=float)
    if transform == "points":
        return (a - b) / POINTS_SCALE
    if transform == "log":
        if np.any(a <= 0) or np.any(b <= 0):
            raise ValueError("a transformação log exige pontos positivos")
        return np.log(a) - np.log(b)
    raise ValueError(f"transformação desconhecida: {transform!r}")


def series_win_probability(beta: float, x, best_of: int):
    return series_probability(logistic(beta * np.asarray(x, dtype=float)), best_of)


def negative_log_likelihood(beta: float, x: np.ndarray, won: np.ndarray, best_of: int) -> float:
    p = np.clip(series_win_probability(beta, x, best_of), _EPSILON, 1 - _EPSILON)
    return float(-np.sum(np.where(won, np.log(p), np.log1p(-p))))


def fit_beta(x: np.ndarray, won: np.ndarray, best_of: int = 3, tolerance: float = 1e-7) -> float:
    """Máxima verossimilhança em uma dimensão (busca da seção áurea)."""
    x = np.asarray(x, dtype=float)
    won = np.asarray(won, dtype=bool)
    if x.size == 0 or x.shape != won.shape:
        raise ValueError("dados de calibração vazios ou inconsistentes")
    ratio = (np.sqrt(5) - 1) / 2
    low, high = _BETA_BOUNDS
    c, d = high - ratio * (high - low), low + ratio * (high - low)
    fc, fd = negative_log_likelihood(c, x, won, best_of), negative_log_likelihood(d, x, won, best_of)
    while high - low > tolerance:
        if fc < fd:
            high, d, fd = d, c, fc
            c = high - ratio * (high - low)
            fc = negative_log_likelihood(c, x, won, best_of)
        else:
            low, c, fc = c, d, fd
            d = low + ratio * (high - low)
            fd = negative_log_likelihood(d, x, won, best_of)
    beta = (low + high) / 2
    if min(beta - _BETA_BOUNDS[0], _BETA_BOUNDS[1] - beta) < 1e-3:
        raise RuntimeError(f"ótimo na fronteira da busca (beta = {beta:.3f})")
    return float(beta)


@dataclass(frozen=True)
class B0Model:
    beta: float
    transform: str
    ratings: Mapping[str, float]

    def map_probability(self, team_a: str, team_b: str) -> float:
        x = features(self.ratings[team_a], self.ratings[team_b], self.transform)
        return float(logistic(self.beta * x))

    def prob_fn(self) -> Callable[[str, str, int], float]:
        """Interface esperada por ``swiss.simulate_stage``."""

        def prob_fn(team_a: str, team_b: str, best_of: int) -> float:
            return float(series_probability(self.map_probability(team_a, team_b), best_of))

        return prob_fn
