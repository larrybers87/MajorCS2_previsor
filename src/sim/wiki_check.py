"""Conferência SECUNDÁRIA do CSV contra o texto bruto da Wikipedia (arquivo local).

Não baixa nada e não altera dados: o CSV do Larry é a fonte dos resultados. Para salvar
o texto uma vez (cópia em ``data/raw/wikipedia/<carimbo>/``)::

    curl -o <arquivo> "https://en.wikipedia.org/w/index.php?title=PGL_Major_Singapore_2026&action=raw"
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .results import ResultRow
from .singapore2026 import canonical_name


def _plain(text: str) -> str:
    text = re.sub(r"\{\{efn[^}]*\}\}", "", text)
    return re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)


def _number(value: str | None) -> int | None:
    return int(value) if value and value.strip().isdigit() else None


def parse_matches(wikitext: str, stage: int) -> list[ResultRow]:
    """Partidas listadas na seção ``== Stage N ==``; confrontos indefinidos são ignorados."""
    parts = wikitext.split(f"== Stage {stage} ==")
    if len(parts) < 2:
        raise ValueError(f"seção do Stage {stage} não encontrada")
    section = _plain(re.split(r"\n==(?!=)[^\n]*==\s*\n", parts[1])[0])
    rounds = re.split(r"==== Round (\d) ====", section)[1:]
    rows: list[ResultRow] = []
    for number, body in zip(rounds[::2], rounds[1::2]):
        for block in body.split("{{Esports match")[1:]:
            fields = {
                key: value.strip()
                for key, value in re.findall(r"\|\s*([a-z0-9_]+)\s*=\s*([^|}\n]*)", block)
            }
            try:
                a = canonical_name(fields.get("team1", ""))
                b = canonical_name(fields.get("team2", ""))
            except ValueError:
                continue
            series_a = _number(fields.get("team1score"))
            series_b = _number(fields.get("team2score"))
            score_a, score_b, best_of = series_a, series_b, None
            if series_a is not None and series_b is not None and series_a != series_b:
                best_of = 1 if max(series_a, series_b) == 1 else 3
                if best_of == 1:  # no Bo1 o CSV guarda os rounds do mapa
                    score_a = _number(fields.get("map1team1score"))
                    score_b = _number(fields.get("map1team2score"))
            else:
                score_a = score_b = None
            rows.append(ResultRow(int(number), a, b, score_a, score_b, best_of, 0))
    return rows


def compare_with_csv(rows: Sequence[ResultRow], wiki: Sequence[ResultRow]) -> list[str]:
    """Diferenças entre o CSV e a Wikipedia, para o Larry conferir."""
    listed = {(w.round, frozenset((w.team_a, w.team_b))): w for w in wiki}
    notes = []
    for row in rows:
        label = f"R{row.round} {row.team_a} x {row.team_b}"
        other = listed.pop((row.round, frozenset((row.team_a, row.team_b))), None)
        if other is None:
            notes.append(f"{label}: confronto não listado na Wikipedia")
        elif row.winner is None:
            if other.winner is not None:
                notes.append(f"{label}: pendente no CSV; Wikipedia diz {other.winner}")
        elif other.winner is None:
            notes.append(f"{label}: sem resultado na Wikipedia")
        elif other.winner != row.winner:
            notes.append(f"{label}: vencedor no CSV {row.winner}; na Wikipedia {other.winner}")
        elif other.score_a is not None:
            theirs = {other.team_a: other.score_a, other.team_b: other.score_b}
            mine = {row.team_a: row.score_a, row.team_b: row.score_b}
            if theirs != mine:
                notes.append(
                    f"{label}: placar no CSV {row.score_a}-{row.score_b}; na Wikipedia "
                    f"{theirs[row.team_a]}-{theirs[row.team_b]}"
                )
    notes += [
        f"R{w.round} {w.team_a} x {w.team_b}: jogada segundo a Wikipedia, ausente no CSV"
        for w in listed.values()
        if w.winner is not None
    ]
    return notes
