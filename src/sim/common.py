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

from .results import file_sha256
from .singapore2026 import DATA_CUTOFF

MANUAL_DIR = PROJECT_ROOT / "data" / "manual"
PREDICTIONS_DIR = PROJECT_ROOT / "predictions"


def load_params(path: Path = PARAMS_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe; rode: python -m backtest.b0_calibration")
    params = json.loads(path.read_text(encoding="utf-8"))
    if params["train_last"] >= str(DATA_CUTOFF):
        raise ValueError(
            f"parâmetros treinados até {params['train_last']}, dentro do período do Major "
            f"(corte exclusivo {DATA_CUTOFF})"
        )
    return params


def load_stage2_model(path: Path) -> dict:
    """Modelo do Stage 2 a partir da saída de ``backtest.h10_format``.

    Devolve ``mode`` ("faixa" ou "estimado"), ``variants`` (w e beta), ``ci`` de w,
    ``transform`` e ``train_last``.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe; rode: python -m backtest.h10_format")
    params = json.loads(path.read_text(encoding="utf-8"))
    if params["train_last"] >= str(DATA_CUTOFF):
        raise ValueError(
            f"parâmetros treinados até {params['train_last']}, dentro do período do Major "
            f"(corte exclusivo {DATA_CUTOFF})"
        )
    rule = params["rule"]
    return {
        "mode": rule["mode"],
        "variants": rule["variants"],
        "ci": rule["ci"],
        "transform": params["b0_config"]["transform"],
        "train_last": params["train_last"],
    }


def freeze_inputs(out: Path, seeds_path: Path, params_path: Path) -> dict:
    """Copia os parâmetros para a pasta da previsão e devolve os hashes das entradas.

    A cópia é gravada com quebras de linha LF; o hash é o dela, como o GitHub a serve.
    """
    copy = out / "model_params.json"
    copy.write_bytes(params_path.read_bytes().replace(b"\r\n", b"\n"))
    return {
        "seeds_file_sha256": file_sha256(seeds_path),
        "params_file_sha256": file_sha256(copy),
    }


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


# As saídas das previsões usam LF para que o arquivo local seja byte a byte o que o git
# guarda (e o hash local seja verificável no GitHub).
def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: dict) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, encoding="utf-8", float_format="%.6f", lineterminator="\n")


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def markdown_table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines
