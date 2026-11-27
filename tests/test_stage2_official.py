"""Integridade da previsão oficial do Stage 2, lida do commit marcado.

Só confere o que foi commitado: não calcula previsão nova. As probabilidades por
partida são recalculadas a partir dos parâmetros e pontos da própria pasta apenas para
verificar que os números publicados são coerentes entre si.
"""

import io
import json
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from ingest.vrs import PROJECT_ROOT
from models.b0 import B0Model
from sim.official import DEADLINE_UTC, OFFICIAL_COMMIT, OFFICIAL_DIR, OFFICIAL_RELATIVE
from swiss.rules import FINAL_RECORD_COUNTS, FINAL_RECORD_LABELS

RECORDS = [f"P({label})" for label in FINAL_RECORD_LABELS]
FILES = (
    "meta.json", "model_params.json", "opening_round.csv", "probabilities.csv", "summary.md",
)  # fmt: skip
# Os CSVs têm 6 casas: o erro de arredondamento de uma soma de 16 valores é < 1e-5.
TOLERANCE = 1e-5


def git(*args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(PROJECT_ROOT), *args], capture_output=True)
    if result.returncode != 0:
        pytest.skip(f"commit oficial indisponível neste clone: git {' '.join(args)}")
    return result.stdout


def committed(name: str) -> bytes:
    return git("cat-file", "blob", f"{OFFICIAL_COMMIT}:{OFFICIAL_RELATIVE}/{name}")


@pytest.fixture(scope="module")
def table() -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(committed("probabilities.csv")))


@pytest.fixture(scope="module")
def opening() -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(committed("opening_round.csv")))


@pytest.fixture(scope="module")
def meta() -> dict:
    return json.loads(committed("meta.json"))


@pytest.mark.parametrize("name", FILES)
def test_working_copy_is_the_committed_one(name):
    local = (OFFICIAL_DIR / name).read_bytes()
    assert local.replace(b"\r\n", b"\n") == committed(name).replace(b"\r\n", b"\n")


def test_committed_before_the_deadline():
    when = git("show", "-s", "--format=%cI", OFFICIAL_COMMIT).decode().strip()
    assert datetime.fromisoformat(when) < datetime.fromisoformat(DEADLINE_UTC)


@pytest.mark.parametrize("column", ["P(avançar)", "P(avançar) w=0", "P(avançar) w=1"])
def test_eight_teams_advance_in_expectation(table, column):
    assert len(table) == 16
    assert table[column].sum() == pytest.approx(8.0, abs=TOLERANCE)


def test_expected_number_of_teams_per_record(table):
    np.testing.assert_allclose(table[RECORDS].sum(), FINAL_RECORD_COUNTS, atol=TOLERANCE)


def test_each_team_distribution_is_consistent(table):
    np.testing.assert_allclose(table[RECORDS].sum(axis=1), 1.0, atol=TOLERANCE)
    np.testing.assert_allclose(table[RECORDS[:3]].sum(axis=1), table["P(avançar)"], atol=TOLERANCE)
    assert ((table[RECORDS] >= 0) & (table[RECORDS] <= 1)).all().all()


def test_opening_round_has_a_probability_for_every_match(opening, meta):
    names = meta["stage2_seeds"]
    assert len(opening) == 8
    assert list(zip(opening["seed_a"], opening["seed_b"])) == [(s, s + 8) for s in range(1, 9)]
    assert list(opening["time_a"]) == names[:8] and list(opening["time_b"]) == names[8:]
    assert (opening["best_of"] == 1).all() and (opening["origem"] == "engine").all()
    assert opening["P(time_a vence)"].between(0, 1, inclusive="neither").all()


def test_opening_probabilities_match_the_published_parameters(opening, table, meta):
    ratings = dict(zip(table["time"], table["vrs_pontos"].astype(float)))
    models = [B0Model(v["beta"], meta["transform"], ratings) for v in meta["variants"]]
    for row in opening.itertuples():
        a, b = row.time_a, row.time_b
        mean = np.mean([m.prob_fn()(a, b, int(row.best_of)) for m in models])
        assert row[opening.columns.get_loc("P(time_a vence)") + 1] == pytest.approx(mean, abs=1e-6)
