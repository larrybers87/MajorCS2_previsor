"""V2: a engine reproduz os emparelhamentos reais do Stage 1 deste Major.

Ativa quando ``data/manual/stage1_results.csv`` e os seeds existem; senão é pulado.
Uma falha aqui é uma divergência a relatar, não motivo para forçar a engine.
"""

import pytest

from ingest.seeds import SEEDS_PATH, load_seeds
from sim.common import MANUAL_DIR
from sim.format_config import DEFAULT_FORMAT
from sim.results import build_state, pairing_report, read_results
from sim.stages import entrants_by_seed, stage2_names
from swiss import current_round, pair_round

RESULTS = MANUAL_DIR / "stage1_results.csv"


@pytest.mark.skipif(
    not (RESULTS.exists() and SEEDS_PATH.exists()),
    reason="V2: falta data/manual/stage1_results.csv ou os seeds (python -m ingest.seeds)",
)
def test_v2_stage1_real_pairings():
    base = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(load_seeds(), 1))
    state = build_state(base, read_results(RESULTS))
    assert pairing_report(state) == []


# Rodada 1 do Stage 2 como listada antes dos jogos na Wikipedia (revisão de
# 27/11/2026 15:24 UTC; fonte secundária).
STAGE2_ROUND_ONE = {
    frozenset(pair)
    for pair in (
        ("FUT", "FlyQuest"), ("Nemiga", "NiP"), ("G2", "Liquid"),
        ("THE ONE", "Eternal Fire"), ("Natus Vincere", "PVISION"),
        ("Astralis", "Imperial"), ("The MongolZ", "Lynn Vision"), ("MIBR", "100 Thieves"),
    )  # fmt: skip
}


@pytest.mark.skipif(
    not (RESULTS.exists() and SEEDS_PATH.exists()),
    reason="V2: falta data/manual/stage1_results.csv ou os seeds (python -m ingest.seeds)",
)
def test_v2_stage2_listed_round_one_confirms_final_seeds():
    """Testa H3: seeds 9-16 pelo seed final, com Difficulty recalculado ao fim do stage."""
    seeds = load_seeds()
    base = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1))
    stage1 = build_state(base, read_results(RESULTS))
    if current_round(stage1) is not None:
        pytest.skip("Stage 1 incompleto no CSV")
    stage2 = DEFAULT_FORMAT.stage_state(2, stage2_names(seeds, stage1))
    assert {p.pair for p in pair_round(stage2)} == STAGE2_ROUND_ONE
