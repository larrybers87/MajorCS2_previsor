"""Utilitários dos scripts de previsão: modelo, metadados e saídas."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backtest.b0_calibration import PARAMS_PATH
from ingest.vrs import PROJECT_ROOT
from models.b0 import B0Model

MANUAL_DIR = PROJECT_ROOT / "data" / "manual"
PREDICTIONS_DIR = PROJECT_ROOT / "predictions"


def load_params(path: Path = PARAMS_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe; rode: python -m backtest.b0_calibration")
    return json.loads(path.read_text(encoding="utf-8"))


def b0_from(seeds: pd.DataFrame, beta: float, transform: str) -> B0Model:
    """B0 com os pontos VRS pré-evento (snapshot de 02/11/2026)."""
    ratings = dict(zip(seeds["name"], seeds["vrs_points"].astype(float)))
    return B0Model(beta=beta, transform=transform, ratings=ratings)


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), *args], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return "desconhecido"
    return result.stdout.strip()


def run_metadata() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "generated_at_utc": now.isoformat(timespec="seconds"),
        "generated_at_local": now.astimezone().isoformat(timespec="seconds"),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_uncommitted_code": bool(_git("status", "--porcelain", "--", "src")),
    }


def new_output_dir(base: Path, metadata: dict) -> Path:
    """Pasta nova com carimbo de tempo UTC; nunca sobrescreve uma previsão."""
    stamp = metadata["generated_at_utc"].replace("-", "").replace(":", "").split("+")[0]
    path = base / f"{stamp}Z"
    suffix = 1
    while path.exists():
        suffix += 1
        path = base / f"{stamp}Z_{suffix}"
    path.mkdir(parents=True)
    return path


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def markdown_table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines
