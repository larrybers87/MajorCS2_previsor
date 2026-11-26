"""Leitura dos resultados digitados à mão e montagem do estado de um stage.

CSV com as colunas ``round,team_a,team_b,score_a,score_b,best_of``. Placar vazio =
partida anunciada e ainda não jogada. Vence quem tem o placar maior (rounds num Bo1,
mapas num Bo3).
"""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from swiss import Match, StageState, best_of, check_pairings, records

from .singapore2026 import canonical_name

COLUMNS = ("round", "team_a", "team_b", "score_a", "score_b", "best_of")


@dataclass(frozen=True)
class ResultRow:
    round: int
    team_a: str
    team_b: str
    score_a: int | None
    score_b: int | None
    best_of: int | None
    line: int

    @property
    def winner(self) -> str | None:
        if self.score_a is None:
            return None
        return self.team_a if self.score_a > self.score_b else self.team_b


def _integer(value: str, field: str, line: int) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"linha {line}: {field} não é um inteiro: {value!r}") from None


def read_results(path: Path) -> list[ResultRow]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.readline()
        handle.seek(0)
        # O Excel em português costuma salvar CSV com ponto e vírgula.
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        header = [name.strip() for name in reader.fieldnames or []]
        missing = [c for c in COLUMNS if c not in header]
        if missing:
            raise ValueError(f"{path}: faltam as colunas {missing}")
        reader.fieldnames = header
        rows: list[ResultRow] = []
        for line, raw in enumerate(reader, start=2):
            values = {k: (raw.get(k) or "").strip() for k in COLUMNS}
            if not any(values.values()):
                continue
            round_number = _integer(values["round"], "round", line)
            score_a = _integer(values["score_a"], "score_a", line)
            score_b = _integer(values["score_b"], "score_b", line)
            fmt = _integer(values["best_of"].lower().removeprefix("bo"), "best_of", line)
            if round_number is None:
                raise ValueError(f"linha {line}: rodada vazia")
            if (score_a is None) != (score_b is None):
                raise ValueError(f"linha {line}: preencha os dois placares ou nenhum")
            if score_a is not None and score_a == score_b:
                raise ValueError(f"linha {line}: placar empatado")
            if fmt not in (None, 1, 3, 5):
                raise ValueError(f"linha {line}: best_of inválido: {fmt}")
            rows.append(
                ResultRow(
                    round_number,
                    canonical_name(values["team_a"]),
                    canonical_name(values["team_b"]),
                    score_a,
                    score_b,
                    fmt,
                    line,
                )
            )
    return rows


def build_state(base: StageState, rows: Sequence[ResultRow]) -> StageState:
    """Estado do stage com as partidas do CSV como fatos (validadas pelo formato)."""
    matches = tuple(Match(r.round, r.team_a, r.team_b, r.winner) for r in rows)
    return base.with_matches(matches)


def format_notes(state: StageState, rows: Sequence[ResultRow]) -> list[str]:
    """Divergências entre ``best_of``/placar do CSV e a regra de formato da engine."""
    notes = []
    for row in rows:
        wins, losses = records(state.before_round(row.round))[row.team_a]
        expected = best_of(wins, losses, state.all_best_of_three)
        label = f"linha {row.line}: R{row.round} {row.team_a} x {row.team_b}"
        if row.best_of is not None and row.best_of != expected:
            notes.append(f"{label}: CSV diz Bo{row.best_of}, a regra daria Bo{expected}")
        if expected == 3 and row.score_a is not None:
            high, low = sorted((row.score_a, row.score_b), reverse=True)
            if high != 2 or low not in (0, 1):
                notes.append(f"{label}: placar {row.score_a}-{row.score_b} não é de um Bo3")
    return notes


def pairing_report(state: StageState) -> list[str]:
    """V2: divergências entre os confrontos reais e os da engine, rodada a rodada."""

    def text(pairs):
        return ", ".join(sorted(" x ".join(sorted(p)) for p in pairs)) or "nenhum"

    lines = []
    for mismatch in check_pairings(state):
        expected, actual = set(mismatch.expected), set(mismatch.actual)
        lines.append(
            f"rodada {mismatch.round}: só na engine: {text(expected - actual)}; "
            f"só no real: {text(actual - expected)}"
        )
    return lines


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
