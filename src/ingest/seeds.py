"""Seeds do Major a partir do VRS global de 02/11/2026.

Uso::

    python -m ingest.seeds

Grava ``data/processed/seeds_singapore.csv``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from sim.singapore2026 import ENTRANTS, PINNED_VRS_COMMIT, ROSTERS, SEEDING_SNAPSHOT

from .vrs import (
    MIN_SHARED_PLAYERS,
    PROJECT_ROOT,
    REGIONS,
    Standing,
    parse_standings,
    repo_dir,
    require_commit,
    roster_key,
)

SEEDS_PATH = PROJECT_ROOT / "data" / "processed" / "seeds_singapore.csv"


def _snapshot_folder(root: Path) -> Path:
    return root / "invitation" / str(SEEDING_SNAPSHOT.year)


def _standings(root: Path, scope: str) -> list[Standing]:
    name = f"standings_{scope}_{SEEDING_SNAPSHOT:%Y_%m_%d}.md"
    return parse_standings(_snapshot_folder(root) / name)


def find_by_roster(rows: list[Standing], roster: tuple[str, ...]) -> Standing:
    """Linha do VRS com o maior número de jogadores em comum (mínimo 3), sem ambiguidade."""
    wanted = roster_key(roster)
    shared = [(len(wanted & roster_key(row.roster)), row) for row in rows]
    best = max((n for n, _ in shared), default=0)
    if best < MIN_SHARED_PLAYERS:
        raise ValueError(f"nenhum roster do VRS compartilha 3 jogadores com {roster}")
    found = [row for n, row in shared if n == best]
    if len(found) > 1:
        raise ValueError(f"elenco ambíguo no VRS: {roster} casa com {[r.name for r in found]}")
    return found[0]


def build_seeds(root: Path) -> pd.DataFrame:
    """Tabela dos 32 times: nome, região, pontos, seed pré-evento e seed no stage.

    Cada participante é localizado no VRS pelo elenco (``ROSTERS``).
    ``stage_seed`` é a ordem relativa do seed pré-evento entre os que ENTRAM naquele
    stage (Stage 1: seeds 1-16, hipótese H4; Stages 2 e 3: seeds 1-8 dos convidados).
    """
    global_rows = _standings(root, "global")
    region_of: dict[tuple[str, tuple[str, ...]], tuple[str, int]] = {}
    for region in REGIONS:
        for row in _standings(root, region):
            region_of[(row.name, row.roster)] = (region, row.rank)

    records = []
    for entrant in ENTRANTS:
        row = find_by_roster(global_rows, ROSTERS[entrant.name])
        region, region_rank = region_of[(row.name, row.roster)]
        records.append(
            {
                "name": entrant.name,
                "region": region,
                "vrs_points": row.points,
                "vrs_global_rank": row.rank,
                "vrs_region_rank": region_rank,
                "stage": entrant.stage,
                "vrs_name": row.name,
                "roster": ", ".join(row.roster),
            }
        )
    table = pd.DataFrame(records).sort_values("vrs_global_rank", ignore_index=True)
    table.insert(4, "pre_event_seed", range(1, len(table) + 1))
    table.insert(6, "stage_seed", table.groupby("stage")["pre_event_seed"].rank().astype(int))
    return table


def invitation_order_issues(table: pd.DataFrame, root: Path) -> list[str]:
    """Confere a ordem de convites em cada região.

    Esperado: convidados são os primeiros do VRS regional, sem pular ninguém, e quem
    entra num stage posterior está acima de quem entra num stage anterior.
    """
    issues: list[str] = []
    for region in REGIONS:
        invited = table[table["region"] == region].sort_values("vrs_region_rank")
        if invited.empty:
            continue
        ranks = set(invited["vrs_region_rank"])
        for row in _standings(root, region):
            if row.rank < max(ranks) and row.rank not in ranks:
                issues.append(f"{region}: {row.name} (#{row.rank}) não está entre os convidados")
        stages = invited["stage"].tolist()
        if stages != sorted(stages, reverse=True):
            order = ", ".join(f"{n} (S{s})" for n, s in zip(invited["name"], stages))
            issues.append(f"{region}: ordem de stages inconsistente: {order}")
    return issues


def load_seeds(path: Path = SEEDS_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{path} não existe; rode: python -m ingest.seeds")
    return pd.read_csv(path)


def main() -> int:
    root = repo_dir()
    commit = require_commit(root, PINNED_VRS_COMMIT)
    table = build_seeds(root)
    SEEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(SEEDS_PATH, index=False, encoding="utf-8")
    print(f"VRS commit {commit}, snapshot {SEEDING_SNAPSHOT}")
    columns = ["pre_event_seed", "name", "region", "vrs_points", "stage", "stage_seed"]
    print(table[columns].to_string(index=False))
    issues = invitation_order_issues(table, root)
    print("Ordem de convites:", "consistente" if not issues else "")
    for issue in issues:
        print("  -", issue)
    print(f"gravado em {SEEDS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
