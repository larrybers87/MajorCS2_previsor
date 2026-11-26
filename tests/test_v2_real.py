"""V2: a engine reproduz os emparelhamentos reais do Stage 1 deste Major.

Ativa quando ``data/manual/stage1_results.csv`` e os seeds existem; senão é pulado.
Uma falha aqui é uma divergência a relatar, não motivo para forçar a engine.
"""

import pytest

from ingest.seeds import SEEDS_PATH, load_seeds
from sim.common import MANUAL_DIR
from sim.format_config import DEFAULT_FORMAT
from sim.results import build_state, pairing_report, read_results
from sim.stages import entrants_by_seed

RESULTS = MANUAL_DIR / "stage1_results.csv"


@pytest.mark.skipif(
    not (RESULTS.exists() and SEEDS_PATH.exists()),
    reason="V2: falta data/manual/stage1_results.csv ou os seeds (python -m ingest.seeds)",
)
def test_v2_stage1_real_pairings():
    base = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(load_seeds(), 1))
    state = build_state(base, read_results(RESULTS))
    assert pairing_report(state) == []
