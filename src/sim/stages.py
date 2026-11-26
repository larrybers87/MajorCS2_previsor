"""Participantes e seeds de cada stage."""

from __future__ import annotations

import pandas as pd

from swiss import StageState, advancing_teams


def entrants_by_seed(seeds: pd.DataFrame, stage: int) -> list[str]:
    """Times que ENTRAM no stage, em ordem de seed pré-evento.

    Stage 1: são os seeds 1-16 (H4). Stages 2 e 3: são os seeds 1-8 (rulebook).
    """
    rows = seeds[seeds["stage"] == stage].sort_values("pre_event_seed")
    expected = 16 if stage == 1 else 8
    if len(rows) != expected:
        raise ValueError(f"stage {stage}: esperados {expected} times, há {len(rows)}")
    return rows["name"].tolist()


def stage2_names(seeds: pd.DataFrame, stage1: StageState) -> list[str]:
    """Seeds do Stage 2: convidados 1-8; classificados do Stage 1 como 9-16 (H3)."""
    return entrants_by_seed(seeds, 2) + advancing_teams(stage1)
