"""Protocolo de avaliação pré-registrado (``docs/protocolo_sessao_03.md``).

Desenvolvimento (2025-09 a 2026-05) escolhe hiperparâmetros; o teste (2026-06-01 até o
corte) é calculado depois, uma vez por modelo escolhido. Walk-forward mensal.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date

import numpy as np
import pandas as pd

from sim.singapore2026 import DATA_CUTOFF

from .metrics import brier_each, cluster_bootstrap_ci, log_loss_each

DEV_START = date(2025, 9, 1)
TEST_START = date(2026, 6, 1)
PERIODS = {"dev": (DEV_START, TEST_START), "test": (TEST_START, DATA_CUTOFF)}
Z_95 = 1.959963984540054

# fit(treino) -> parâmetro; predict(parâmetro, teste) -> probabilidades
Fit = Callable[[np.ndarray], object]
Predict = Callable[[object, np.ndarray], np.ndarray]


def period_mask(dates: pd.Series, period: str) -> np.ndarray:
    start, end = PERIODS[period]
    return ((dates >= pd.Timestamp(start)) & (dates < pd.Timestamp(end))).to_numpy()


def monthly_folds(dates: pd.Series, period: str) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Pares (máscara de treino, máscara do mês previsto) dentro do período."""
    inside = period_mask(dates, period)
    month = dates.dt.to_period("M")
    for current in month[inside].unique():
        test = inside & (month == current).to_numpy()
        train = (dates < current.start_time).to_numpy()
        yield train, test


def walk_forward(
    dates: pd.Series, period: str, eligible: np.ndarray, fit: Fit, predict: Predict
) -> np.ndarray:
    """Previsões fora da amostra no período (NaN fora dele).

    ``eligible`` limita as partidas usadas no TREINO; a previsão é feita para todas as do
    período.
    """
    p = np.full(len(dates), np.nan)
    for train, test in monthly_folds(dates, period):
        params = fit(train & eligible)
        p[test] = predict(params, test)
    return p


def summarize(p: np.ndarray, won: np.ndarray, days: np.ndarray, rng) -> dict:
    ll, brier = log_loss_each(p, won), brier_each(p, won)
    return {
        "n": int(len(p)),
        "log_loss": float(ll.mean()),
        "log_loss_ci": cluster_bootstrap_ci(ll, days, rng),
        "brier": float(brier.mean()),
        "brier_ci": cluster_bootstrap_ci(brier, days, rng),
    }


def paired_difference(
    p: np.ndarray, reference: np.ndarray, won: np.ndarray, days: np.ndarray, rng
) -> dict:
    """Candidato menos referência (negativo = candidato melhor), IC por dias."""
    out = {}
    for name, each in (("log_loss", log_loss_each), ("brier", brier_each)):
        delta = each(p, won) - each(reference, won)
        out[name] = float(delta.mean())
        out[f"{name}_ci"] = cluster_bootstrap_ci(delta, days, rng, n_boot=10_000)
    return out


def wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("intervalo de Wilson exige n > 0")
    rate = successes / n
    denominator = 1 + z**2 / n
    center = (rate + z**2 / (2 * n)) / denominator
    half = z * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / denominator
    return float(center - half), float(center + half)


def favorite_calibration(p: np.ndarray, won: np.ndarray) -> list[dict]:
    """Calibração do favorito do modelo por faixas, com Wilson 95%, e o agregado >= 80%.

    O intervalo de Wilson supõe partidas independentes.
    """
    favorite_p = np.maximum(p, 1 - p)
    favorite_won = np.where(p >= 0.5, won, ~won)
    bands = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01), (0.8, 1.01)]
    rows = []
    for low, high in bands:
        inside = (favorite_p >= low) & (favorite_p < high)
        n = int(inside.sum())
        label = ">= 80%" if (low, high) == (0.8, 1.01) else f"{low:.0%}-{min(high, 1):.0%}"
        row = {"faixa": label, "n": n}
        if n:
            hits = int(favorite_won[inside].sum())
            row |= {
                "previsto": float(favorite_p[inside].mean()),
                "observado": hits / n,
                "ic": wilson_interval(hits, n),
            }
        rows.append(row)
    return rows
