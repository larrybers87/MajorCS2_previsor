"""Leitura do VRS, união de partidas, rating point-in-time e seeds (dados sintéticos)."""

from datetime import date

import pytest

from ingest.vrs import Standing, list_snapshots, parse_detail, parse_standings
from ingest.vrs_matches import MatchMerger, RatingBook, build_table, matches_in_snapshot
from sim.singapore2026 import ENTRANTS, canonical_name

STANDINGS = """### Standings as of 2026_01_05<br />

| Standing | Points | Team Name | Roster | |
| :- | -: | :- | :- | :- |
| 1 | 1900 | Alpha | a1, a2, a3, a4, a5 | [details](details/2026_01_05/0001--alpha.md) |
| 2 | 1500 | Beta | b1, b2, b3, b4, b5 | [details](details/2026_01_05/0002--beta.md) |
"""


def detail(team, roster, rows):
    lines = [
        "### Roster Details<br />",
        f"Team Name: {team}<br />",
        "",
        "| Match Played | Match ID | Date | Opponent | W/L | Age Weight | Event Weight | "
        "Bounty Collected | Opponent Network | LAN Wins | H2H Adj. | Roster |",
        "| -: | -: | :- | :- | :- | :- | :- | :- | :- | :- | -: | :- |",
    ]
    for i, (match_id, day, opponent, result, lan) in enumerate(rows, start=1):
        lines.append(
            f"| {i} | {match_id} | {day} | {opponent} | {result} | 1.0 | - | - | - | {lan} | "
            f"1.0 | {roster} |"
        )
    # Segunda tabela do arquivo (prêmios), que não deve ser lida como partidas.
    lines += ["", "| Event Date | Age Weight | Prize Winnings | Scaled Winnings |",
              "| :- | -: | :- | :- |", "| 2026-01-01 | 1.000 | $1.00 | $1.00 |"]  # fmt: skip
    return "\n".join(lines) + "\n"


@pytest.fixture
def repo(tmp_path):
    folder = tmp_path / "invitation" / "2026"
    details = folder / "details" / "2026_01_05"
    details.mkdir(parents=True)
    (folder / "standings_global_2026_01_05.md").write_text(STANDINGS, encoding="utf-8")
    (details / "0001--alpha.md").write_text(
        detail("Alpha", "a1, a2, a3, a4, a5", [(7, "2026-01-03", "Beta", "W", "1 (1.000)")]),
        encoding="utf-8",
    )
    (details / "0002--beta.md").write_text(
        detail("Beta", "b1, b2, b3, b4, b5", [(7, "2026-01-03", "Alpha", "L", "-"),
                                               (9, "2026-01-02", "Gamma", "W", "-")]),
        encoding="utf-8",
    )  # fmt: skip
    return tmp_path


def read_rows(repo):
    snapshot = list_snapshots(repo)[0]
    standings = parse_standings(snapshot.path)
    return [r for s in standings for r in parse_detail(snapshot.folder / s.detail)]


def test_parse_standings_and_details(repo):
    snapshot = list_snapshots(repo)[0]
    assert snapshot.published == date(2026, 1, 5)
    standings = parse_standings(snapshot.path)
    assert [(s.rank, s.points, s.name) for s in standings] == [(1, 1900, "Alpha"), (2, 1500, "Beta")]
    rows = read_rows(repo)
    assert len(rows) == 3
    assert rows[0].lan_win and rows[0].won and rows[0].roster[0] == "a1"


def test_both_views_of_a_match_become_one(repo):
    matches, inconsistent = matches_in_snapshot(read_rows(repo), date(2026, 1, 5))
    assert inconsistent == 0
    assert sorted((m.winner, m.loser, m.lan) for m in matches) == [
        ("Alpha", "Beta", True),
        ("Beta", "Gamma", False),
    ]


def test_merger_deduplicates_across_snapshots_but_keeps_rematches(repo):
    rows = read_rows(repo)
    first, _ = matches_in_snapshot(rows, date(2026, 1, 5))
    again, _ = matches_in_snapshot(rows, date(2026, 2, 2))
    merger = MatchMerger()
    merger.add_snapshot(first)
    merger.add_snapshot(again)
    assert len(merger.matches()) == 2
    # Duas partidas idênticas no mesmo snapshot continuam sendo duas.
    twice, _ = matches_in_snapshot(rows, date(2026, 1, 5))
    thrice, _ = matches_in_snapshot(rows, date(2026, 1, 5))
    merger = MatchMerger()
    merger.add_snapshot(twice + thrice)
    assert len(merger.matches()) == 4


def standing(rank, points, name, roster):
    return Standing(rank, points, name, tuple(roster.split()), "x")


def test_rating_uses_only_strictly_earlier_snapshot():
    book = RatingBook(
        {
            date(2026, 1, 5): [standing(1, 1000, "Alpha", "a1 a2 a3 a4 a5")],
            date(2026, 2, 2): [standing(1, 2000, "Alpha", "a1 a2 a3 a4 a5")],
        }
    )
    assert book.snapshot_before(date(2026, 1, 5)) is None
    assert book.snapshot_before(date(2026, 2, 2)) == date(2026, 1, 5)
    assert book.snapshot_before(date(2026, 2, 3)) == date(2026, 2, 2)


def test_roster_identity_needs_three_players():
    day = date(2026, 1, 5)
    book = RatingBook({day: [standing(1, 1000, "Alpha", "a1 a2 a3 a4 a5")]})
    found = book.lookup(day, "Renomeado", frozenset({"a1", "a2", "a3", "x", "y"}))
    assert found[0].points == 1000 and found[1] == "roster"
    # Mesmo nome com outro elenco não herda os pontos.
    assert book.lookup(day, "Alpha", frozenset({"a1", "a2", "z", "x", "y"})) is None
    assert book.lookup(day, "alpha", frozenset())[1] == "name"


def test_table_orientation_does_not_depend_on_result(repo):
    matches, _ = matches_in_snapshot(read_rows(repo), date(2026, 1, 5))
    book = RatingBook({date(2025, 12, 1): parse_standings(list_snapshots(repo)[0].path)})
    table = build_table(matches, book)
    assert (table["team_a"] < table["team_b"]).all()
    row = table[table["team_a"] == "Alpha"].iloc[0]
    assert bool(row["team_a_won"]) and row["points_a"] == 1900 and row["points_b"] == 1500


def test_entrants_and_aliases():
    assert len(ENTRANTS) == 32
    assert [sum(e.stage == s for e in ENTRANTS) for s in (1, 2, 3)] == [16, 8, 8]
    assert canonical_name("parivision") == "PVISION"
    assert canonical_name("1win") == "THE ONE"
    assert canonical_name("bc.game") == "GOSH"
    assert canonical_name("Ninjas in Pyjamas") == "NiP"
    with pytest.raises(ValueError, match="desconhecido"):
        canonical_name("TYLOO")
