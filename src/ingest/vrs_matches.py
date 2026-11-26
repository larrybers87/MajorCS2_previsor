"""Partidas com data a partir dos arquivos de detalhes do VRS, com rating point-in-time.

Uso::

    python -m ingest.vrs_matches

Grava ``data/processed/matches.parquet``. O VRS não informa formato (Bo1/Bo3),
placar, evento nem tier; essas colunas ficam vazias.
"""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from sim.singapore2026 import DATA_CUTOFF

from .vrs import (
    PROJECT_ROOT,
    DetailMatch,
    Snapshot,
    Standing,
    list_snapshots,
    parse_detail,
    parse_standings,
    repo_commit,
    repo_dir,
)

MATCHES_PATH = PROJECT_ROOT / "data" / "processed" / "matches.parquet"
WINDOW_START = date(2025, 6, 1)  # decisão: dados desde o Major de Austin
MIN_SHARED_PLAYERS = 3  # um roster é o mesmo com 3 jogadores em comum (TOR §3.2.5 a)


def name_key(name: str) -> str:
    """Normalização de nomes: só espaços nas pontas e maiúsculas/minúsculas."""
    return name.strip().casefold()


def roster_key(roster: tuple[str, ...]) -> frozenset[str]:
    return frozenset(player.casefold() for player in roster)


@dataclass
class RawMatch:
    """Uma partida vista em um snapshot; rosters vazios quando desconhecidos."""

    played_on: date
    winner: str
    loser: str
    winner_roster: frozenset[str]
    loser_roster: frozenset[str]
    lan: bool
    first_seen: date


def matches_in_snapshot(rows: list[DetailMatch], published: date) -> tuple[list[RawMatch], int]:
    """Une as duas visões de cada ``match_id``. Retorna as partidas e as inconsistentes."""
    by_id: dict[int, list[DetailMatch]] = defaultdict(list)
    for row in rows:
        by_id[row.match_id].append(row)
    matches: list[RawMatch] = []
    inconsistent = 0
    for views in by_id.values():
        winners = [v for v in views if v.won]
        losers = [v for v in views if not v.won]
        if len(winners) > 1 or len(losers) > 1 or len({v.played_on for v in views}) != 1:
            inconsistent += 1
            continue
        w = winners[0] if winners else None
        l_ = losers[0] if losers else None
        if w and l_ and (
            name_key(w.opponent) != name_key(l_.team) or name_key(l_.opponent) != name_key(w.team)
        ):
            inconsistent += 1
            continue
        matches.append(
            RawMatch(
                played_on=views[0].played_on,
                winner=w.team if w else l_.opponent,
                loser=l_.team if l_ else w.opponent,
                winner_roster=roster_key(w.roster) if w else frozenset(),
                loser_roster=roster_key(l_.roster) if l_ else frozenset(),
                lan=bool(w and w.lan_win),
                first_seen=published,
            )
        )
    return matches, inconsistent


def _same_side(name_a: str, roster_a: frozenset, name_b: str, roster_b: frozenset) -> bool:
    if roster_a and roster_b:
        return len(roster_a & roster_b) >= MIN_SHARED_PLAYERS
    return name_key(name_a) == name_key(name_b)


class MatchMerger:
    """Deduplica partidas repetidas entre snapshots (a janela do VRS é de 6 meses).

    Dentro de um snapshot cada ``match_id`` é uma partida; entre snapshots, os ids são
    renumerados, então a identidade é (data, lado vencedor, lado perdedor), com
    correspondência um a um (duas partidas iguais no mesmo dia são preservadas).
    """

    def __init__(self) -> None:
        self.by_date: dict[date, list[RawMatch]] = defaultdict(list)
        self.merged_views = 0

    def add_snapshot(self, matches: list[RawMatch]) -> None:
        used: set[int] = set()
        pending: list[RawMatch] = []
        for new in matches:
            for old in self.by_date[new.played_on]:
                if id(old) in used:
                    continue
                if _same_side(
                    old.winner, old.winner_roster, new.winner, new.winner_roster
                ) and _same_side(old.loser, old.loser_roster, new.loser, new.loser_roster):
                    used.add(id(old))
                    old.winner_roster = old.winner_roster or new.winner_roster
                    old.loser_roster = old.loser_roster or new.loser_roster
                    old.lan = old.lan or new.lan
                    self.merged_views += 1
                    break
            else:
                pending.append(new)
        for new in pending:
            self.by_date[new.played_on].append(new)

    def matches(self) -> list[RawMatch]:
        return [m for day in sorted(self.by_date) for m in self.by_date[day]]


class RatingBook:
    """Pontos VRS vigentes: sempre o último snapshot ESTRITAMENTE anterior à data."""

    def __init__(self, standings_by_date: dict[date, list[Standing]]) -> None:
        self.dates = sorted(standings_by_date)
        self._by_name: dict[date, dict[str, list[Standing]]] = {}
        self._by_player: dict[date, dict[str, list[Standing]]] = {}
        for day, rows in standings_by_date.items():
            names: dict[str, list[Standing]] = defaultdict(list)
            players: dict[str, list[Standing]] = defaultdict(list)
            for row in rows:
                names[name_key(row.name)].append(row)
                for player in roster_key(row.roster):
                    players[player].append(row)
            self._by_name[day] = names
            self._by_player[day] = players

    def snapshot_before(self, day: date) -> date | None:
        index = bisect_left(self.dates, day)
        return self.dates[index - 1] if index else None

    def lookup(self, snapshot: date, name: str, roster: frozenset[str]) -> tuple[Standing, str] | None:
        """Linha do roster no snapshot e como foi encontrada ("roster" ou "name")."""
        if roster:
            shared: Counter[Standing] = Counter()
            for player in roster:
                shared.update(self._by_player[snapshot].get(player, []))
            candidates = [(n, row) for row, n in shared.items() if n >= MIN_SHARED_PLAYERS]
            if not candidates:
                return None
            same_name = name_key(name)
            _, row = max(
                candidates,
                key=lambda c: (c[0], name_key(c[1].name) == same_name, -c[1].rank),
            )
            return row, "roster"
        rows = self._by_name[snapshot].get(name_key(name), [])
        return (rows[0], "name") if len(rows) == 1 else None


def build_table(matches: list[RawMatch], book: RatingBook) -> pd.DataFrame:
    """Uma linha por partida; ``team_a``/``team_b`` em ordem alfabética (não do resultado)."""
    records = []
    for m in matches:
        sides = [(m.winner, m.winner_roster, True), (m.loser, m.loser_roster, False)]
        sides.sort(key=lambda s: (name_key(s[0]), sorted(s[1])))
        (name_a, roster_a, a_won), (name_b, roster_b, _) = sides
        snapshot = book.snapshot_before(m.played_on)
        found_a = book.lookup(snapshot, name_a, roster_a) if snapshot else None
        found_b = book.lookup(snapshot, name_b, roster_b) if snapshot else None
        records.append(
            {
                "date": pd.Timestamp(m.played_on),
                "event": None,
                "tier": None,
                "lan": True if m.lan else None,
                "team_a": name_a,
                "team_b": name_b,
                "best_of": None,
                "score": None,
                "winner": m.winner,
                "team_a_won": a_won,
                "source": "vrs",
                "roster_a": ", ".join(sorted(roster_a)),
                "roster_b": ", ".join(sorted(roster_b)),
                "rating_snapshot": pd.Timestamp(snapshot) if snapshot else pd.NaT,
                "points_a": found_a[0].points if found_a else None,
                "points_b": found_b[0].points if found_b else None,
                "rank_a": found_a[0].rank if found_a else None,
                "rank_b": found_b[0].rank if found_b else None,
                "match_a": found_a[1] if found_a else None,
                "match_b": found_b[1] if found_b else None,
            }
        )
    table = pd.DataFrame.from_records(records)
    for column in ("lan", "best_of"):
        table[column] = table[column].astype("boolean" if column == "lan" else "Int64")
    for column in ("event", "tier", "score"):
        table[column] = table[column].astype("string")
    for column in ("points_a", "points_b", "rank_a", "rank_b"):
        table[column] = table[column].astype("Int64")
    return table


def load_all(root: Path, start: date, end: date) -> tuple[pd.DataFrame, dict]:
    """Partidas com ``start <= data < end`` e um relatório de cobertura."""
    snapshots: list[Snapshot] = list_snapshots(root)
    standings = {s.published: parse_standings(s.path) for s in snapshots}
    merger = MatchMerger()
    stats = Counter()
    future_rows = 0
    for snapshot in snapshots:
        if snapshot.published < start:
            continue
        rows: list[DetailMatch] = []
        for standing in standings[snapshot.published]:
            rows.extend(parse_detail(snapshot.folder / standing.detail))
        future_rows += sum(r.played_on >= snapshot.published for r in rows)
        rows = [r for r in rows if start <= r.played_on < end]
        found, inconsistent = matches_in_snapshot(rows, snapshot.published)
        merger.add_snapshot(found)
        stats["snapshots"] += 1
        stats["team_rows"] += len(rows)
        stats["inconsistent_ids"] += inconsistent
    table = build_table(merger.matches(), RatingBook(standings))
    report = dict(stats)
    report["rows_dated_on_or_after_snapshot"] = future_rows
    report["duplicate_views_merged"] = merger.merged_views
    report["matches"] = len(table)
    return table, report


def main() -> int:
    root = repo_dir()
    table, report = load_all(root, WINDOW_START, DATA_CUTOFF)
    MATCHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(MATCHES_PATH, index=False)

    rated = table.dropna(subset=["points_a", "points_b"])
    print(f"VRS commit {repo_commit(root)}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print(f"período: {table['date'].min():%Y-%m-%d} a {table['date'].max():%Y-%m-%d}")
    print(f"com rating dos dois lados: {len(rated)}")
    sides = pd.concat([table["match_a"], table["match_b"]]).value_counts(dropna=False)
    print("como o rating foi encontrado (lados):", sides.to_dict())
    print(f"roster desconhecido em algum lado: "
          f"{((table['roster_a'] == '') | (table['roster_b'] == '')).sum()}")  # fmt: skip
    print(f"LAN conhecida: {table['lan'].sum()}")
    possible = table.duplicated(["date", "team_a", "team_b"], keep=False)
    print(f"linhas com mesmo par no mesmo dia (possíveis duplicatas ou revanches): {possible.sum()}")
    print("partidas por mês:")
    print(table.groupby(table["date"].dt.to_period("M")).size().to_string())
    print(f"gravado em {MATCHES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
