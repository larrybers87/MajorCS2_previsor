"""Modelo pré-registrado do Stage 3: B0, B1 e a combinação, sem reponderar.

Fontes: ``docs/preregistro_stage3.md`` e emendas 1 a 4. Tudo aqui é constante: nada é
ajustado com resultados do Major.
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.v3_compare import B1_BETAS
from ingest.vrs import PROJECT_ROOT
from models.b0 import B0Model
from models.ratings import EloConfig
from swiss import ProbFn, StageState, current_round, simulate_stage

from .b1_ratings import b1_prob_fn, config_from, major_ratings
from .common import load_params
from .format_config import DEFAULT_FORMAT
from .results import ResultRow, build_state, read_results
from .stages import entrants_by_seed, stage2_names

B0_BETAS = {0.0: 0.155760, 1.0: 0.236080}  # pré-registro (calculados até 01/11)
B1_CONFIG = EloConfig(s=0.5, k=20, half_life=None, provisional=2)
B1_FROZEN_COMMIT = "30a519a"
B1_FROZEN_FILES = ("src/models/ratings.py", "src/sim/b1_ratings.py")
MODELS = ("B0", "B1")

# Emenda 4: descontos em pontos VRS (arbitrários), só na sensibilidade.
SENSITIVITY_GRID = {"Vitality": (0, -25, -50), "Legacy": (0, -50, -100)}


def load_b1_config(params_path: Path) -> EloConfig:
    """Configuração do B1, conferida contra a congelada."""
    config = config_from(load_params(params_path)["chosen"])
    if config != B1_CONFIG:
        raise ValueError(f"configuração do B1 diferente da congelada: {config}")
    return config


def assert_frozen_b1_code() -> None:
    """O código do B1 tem de ser o avaliado no commit congelado."""
    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "diff", "--quiet", B1_FROZEN_COMMIT, "--",
         *B1_FROZEN_FILES],
        capture_output=True,
    )  # fmt: skip
    if result.returncode != 0:
        raise ValueError(
            f"o código do B1 difere do commit congelado {B1_FROZEN_COMMIT} "
            "(ou o commit não está disponível)"
        )


def load_stages(
    seeds: pd.DataFrame, stage1_path: Path, stage2_path: Path
) -> tuple[StageState, list[ResultRow], StageState, list[ResultRow]]:
    """Stages 1 e 2 completos."""
    rows1, rows2 = read_results(stage1_path), read_results(stage2_path)
    stage1 = build_state(
        DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1)), rows1
    )
    if current_round(stage1) is not None:
        raise ValueError("o Stage 1 está incompleto no CSV")
    stage2 = build_state(
        DEFAULT_FORMAT.stage_state(2, stage2_names(seeds, stage1)), rows2
    )
    if current_round(stage2) is not None:
        raise ValueError(f"o Stage 2 não terminou (rodada {current_round(stage2)})")
    return stage1, rows1, stage2, rows2


def b1_ratings_at(
    matches: pd.DataFrame,
    seeds: pd.DataFrame,
    config: EloConfig,
    previous: Mapping[int, Sequence[ResultRow]],
) -> dict[str, float]:
    """Ratings do B1 com exatamente os resultados de ``previous`` (D33)."""
    table = major_ratings(matches, seeds, config, previous).set_index("time")
    played = any(rows for rows in previous.values())
    return table["b1_atual" if played else "b1_pre_evento"].to_dict()


def vrs_points(seeds: pd.DataFrame) -> dict[str, float]:
    return {n: float(p) for n, p in zip(seeds["name"], seeds["vrs_points"])}


def prob_fns(
    points: Mapping[str, float],
    b1_ratings: Mapping[str, float],
    models: Sequence[str] = MODELS,
    discounts: Mapping[str, float] | None = None,
) -> dict[tuple[str, float], ProbFn]:
    """``{(modelo, w): prob_fn}``.

    ``discounts`` (pontos VRS, negativos) vale só para estas probabilidades. No B1 vira o
    desconto que produz o mesmo deslocamento de log-odds: ``pontos x beta0 / beta1``.
    """
    discounts = discounts or {}
    out: dict = {}
    for w in (0.0, 1.0):
        if "B0" in models:
            ratings = {n: p + discounts.get(n, 0) for n, p in points.items()}
            out[("B0", w)] = B0Model(B0_BETAS[w], "points", ratings).prob_fn()
        if "B1" in models:
            factor = B0_BETAS[w] / B1_BETAS[w]
            ratings = {n: r + discounts.get(n, 0) * factor for n, r in b1_ratings.items()}
            out[("B1", w)] = b1_prob_fn(ratings, B1_BETAS[w])
    return out


def mean_prob_fn(fns: Sequence[ProbFn]) -> ProbFn:
    def prob_fn(team_a: str, team_b: str, best_of: int) -> float:
        return float(np.mean([f(team_a, team_b, best_of) for f in fns]))

    return prob_fn


def simulate_average(
    fns: Sequence[ProbFn], base: StageState, simulations: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Simula cada variante e faz a média: ``(cartéis (16, 6), posições (16, 16))``."""
    records, positions = [], []
    for fn in fns:
        result = simulate_stage(fn, base, simulations, np.random.default_rng(seed))
        records.append(result.record_counts / simulations)
        positions.append(result.position_counts / simulations)
    return np.mean(records, axis=0), np.mean(positions, axis=0)
