"""Leitura do repositório oficial do VRS (``ValveSoftware/counter-strike_regional_standings``).

O repositório é clonado FORA do projeto (ver ``docs/fonte_vrs.md``). Aqui só se leem
arquivos Markdown; nenhum código do repositório é executado.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPO_DIR = PROJECT_ROOT.parent / "_external" / "counter-strike_regional_standings"
REGIONS = ("europe", "americas", "asia")
# TOR §1.1: a pasta ``invitation`` é a versão relevante; ``live`` só acrescenta datas.
FLAVORS = ("invitation", "live")

_STANDINGS_NAME = re.compile(r"standings_global_(\d{4})_(\d{2})_(\d{2})\.md$")


@dataclass(frozen=True)
class Standing:
    rank: int
    points: int
    name: str
    roster: tuple[str, ...]
    detail: str  # caminho relativo do arquivo de detalhes


@dataclass(frozen=True)
class DetailMatch:
    """Linha da tabela de partidas de um arquivo de detalhes (visão de um time)."""

    match_id: int
    played_on: date
    team: str
    opponent: str
    won: bool
    lan_win: bool  # True só quando a coluna "LAN Wins" traz valor; False = desconhecido
    roster: tuple[str, ...]


@dataclass(frozen=True)
class Snapshot:
    published: date
    flavor: str
    path: Path  # arquivo global

    @property
    def folder(self) -> Path:
        return self.path.parent


def repo_dir() -> Path:
    path = Path(os.environ.get("VRS_REPO_DIR", DEFAULT_REPO_DIR))
    if not (path / "invitation").is_dir():
        raise FileNotFoundError(
            f"repositório do VRS não encontrado em {path}; clone-o ou defina VRS_REPO_DIR "
            "(ver docs/fonte_vrs.md)"
        )
    return path


def repo_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def list_snapshots(root: Path) -> list[Snapshot]:
    """Um snapshot global por data, em ordem; ``invitation`` tem preferência."""
    found: dict[date, Snapshot] = {}
    for flavor in FLAVORS:
        for path in sorted(root.glob(f"{flavor}/*/standings_global_*.md")):
            match = _STANDINGS_NAME.search(path.name)
            if not match:
                continue
            published = date(*map(int, match.groups()))
            found.setdefault(published, Snapshot(published, flavor, path))
    return [found[key] for key in sorted(found)]


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _roster(text: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in text.split(",") if part.strip())


def parse_standings(path: Path) -> list[Standing]:
    """Lê um arquivo ``standings_*.md`` (global ou regional)."""
    standings: list[Standing] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if not cells or not cells[0].isdigit():
            continue
        if len(cells) != 5:
            raise ValueError(f"{path}: linha com {len(cells)} colunas: {line!r}")
        link = re.search(r"\((details/[^)]+)\)", cells[4])
        if not link:
            raise ValueError(f"{path}: linha sem link de detalhes: {line!r}")
        standings.append(
            Standing(int(cells[0]), int(cells[1]), cells[2], _roster(cells[3]), link.group(1))
        )
    if not standings:
        raise ValueError(f"{path}: nenhuma linha de classificação reconhecida")
    return standings


def parse_detail(path: Path) -> list[DetailMatch]:
    """Lê a tabela de partidas de um arquivo de detalhes de roster."""
    text = path.read_text(encoding="utf-8")
    name = re.search(r"^Team Name: (.*?)<br />", text, re.MULTILINE)
    if not name:
        raise ValueError(f"{path}: sem 'Team Name'")
    team = name.group(1).strip()
    matches: list[DetailMatch] = []
    columns: dict[str, int] | None = None
    for line in text.splitlines():
        if not line.startswith("|"):
            columns = None
            continue
        cells = _cells(line)
        if "Match ID" in cells:
            columns = {label: i for i, label in enumerate(cells)}
            continue
        if columns is None or not cells[0].isdigit():
            continue
        if len(cells) != len(columns):
            raise ValueError(f"{path}: linha de partida malformada: {line!r}")
        result = cells[columns["W/L"]]
        if result not in ("W", "L"):
            raise ValueError(f"{path}: resultado desconhecido {result!r}")
        matches.append(
            DetailMatch(
                match_id=int(cells[columns["Match ID"]]),
                played_on=date.fromisoformat(cells[columns["Date"]]),
                team=team,
                opponent=cells[columns["Opponent"]],
                won=result == "W",
                lan_win=result == "W" and cells[columns["LAN Wins"]] not in ("-", ""),
                roster=_roster(cells[columns["Roster"]]),
            )
        )
    return matches
