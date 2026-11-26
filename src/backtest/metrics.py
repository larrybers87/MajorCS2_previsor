"""Métricas por partida e intervalos por bootstrap."""

from __future__ import annotations

import numpy as np

_EPSILON = 1e-12


def log_loss_each(p: np.ndarray, won: np.ndarray) -> np.ndarray:
    """Log loss de cada partida; ``p`` = probabilidade prevista de ``team_a`` vencer."""
    p = np.clip(np.asarray(p, dtype=float), _EPSILON, 1 - _EPSILON)
    return np.where(np.asarray(won, dtype=bool), -np.log(p), -np.log1p(-p))


def brier_each(p: np.ndarray, won: np.ndarray) -> np.ndarray:
    return (np.asarray(p, dtype=float) - np.asarray(won, dtype=float)) ** 2


def cluster_bootstrap_ci(
    values: np.ndarray,
    clusters: np.ndarray,
    rng: np.random.Generator,
    n_boot: int = 2000,
    level: float = 0.95,
) -> tuple[float, float]:
    """IC da média reamostrando GRUPOS inteiros (aqui: dias), pois há dependência."""
    values = np.asarray(values, dtype=float)
    _, index = np.unique(np.asarray(clusters), return_inverse=True)
    sums = np.bincount(index, weights=values)
    counts = np.bincount(index)
    draws = rng.integers(0, len(sums), size=(n_boot, len(sums)))
    means = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    low, high = np.quantile(means, [(1 - level) / 2, (1 + level) / 2])
    return float(low), float(high)
