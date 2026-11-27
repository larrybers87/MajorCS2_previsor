"""Anexo D25: cenário 0 igual à oficial, seeds intactos e direção do efeito."""

import json

import pandas as pd
import pytest
from test_sim import files, play_stage, run_predict, stage1_base, to_csv  # noqa: F401

from sim import anexo_d25
from sim.stages import entrants_by_seed


def run_annex(files, *args):  # noqa: F811
    out = files["dir"] / "annex"
    code = anexo_d25.main(
        [*args, "--sims", "3000", "--out", str(out), "--seeds-file", str(files["seeds"]),
         "--params-file", str(files["model"])]
    )  # fmt: skip
    folders = sorted(out.iterdir(), key=lambda p: p.stat().st_mtime_ns) if out.exists() else []
    return code, folders[-1] if folders else None


def test_adjustment_changes_points_but_not_seeds(files):  # noqa: F811
    seeds = pd.read_csv(files["seeds"])
    changed = anexo_d25.adjusted_seeds(seeds, -100)
    different = changed["vrs_points"] != seeds["vrs_points"]
    assert sorted(changed.loc[different, "name"]) == ["Astralis", "FUT"]
    assert (changed.loc[different, "vrs_points"] - seeds.loc[different, "vrs_points"] == -100).all()
    pd.testing.assert_series_equal(changed["pre_event_seed"], seeds["pre_event_seed"])
    assert entrants_by_seed(changed, 2) == entrants_by_seed(seeds, 2)
    assert (seeds["vrs_points"] == pd.read_csv(files["seeds"])["vrs_points"]).all()


@pytest.mark.parametrize("complete", [True, False])
def test_scenario_zero_reproduces_the_official_prediction(files, complete):  # noqa: F811
    state = play_stage(stage1_base(), rounds=5 if complete else 4, seed=12)
    csv_path = to_csv(state, files["dir"] / "s1.csv")
    mode = ["--stage1", str(csv_path)] + ([] if complete else ["--conditioned"])
    official = run_predict(files, *mode)
    code, folder = run_annex(files, *mode, "--official", str(official))
    assert code == 0
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["official"] is False and meta["check_max_difference"] <= anexo_d25.TOLERANCE
    table = pd.read_csv(folder / "scenarios.csv")
    assert sorted(table["delta"].unique()) == [-100, -50, 0]
    advance = table.pivot(index="time", columns="delta", values="P(avançar)")
    for team in ("FUT", "Astralis"):
        assert advance.loc[team, 0] > advance.loc[team, -50] > advance.loc[team, -100]
    # A soma de P(avançar) continua 8: o que um perde os outros ganham.
    assert advance.sum().tolist() == pytest.approx([8.0, 8.0, 8.0], abs=1e-4)
    matches = pd.read_csv(folder / "matches.csv")
    assert set(matches["time"]) == {"FUT", "Astralis"}
    assert "arbitrários" in (folder / "summary.md").read_text(encoding="utf-8")


def test_mismatch_with_official_fails(files):  # noqa: F811
    csv_path = to_csv(play_stage(stage1_base(), seed=12), files["dir"] / "s1.csv")
    official = run_predict(files, "--stage1", str(csv_path))
    code, folder = run_annex(
        files, "--stage1", str(csv_path), "--official", str(official), "--seed", "1"
    )
    assert code == 1 and folder is None


def test_annex_refuses_stage2_results(files):  # noqa: F811
    from sim.format_config import DEFAULT_FORMAT
    from sim.stages import stage2_names

    stage1 = play_stage(stage1_base(), seed=12)
    csv_path = to_csv(stage1, files["dir"] / "s1.csv")
    names = stage2_names(pd.read_csv(files["seeds"]), stage1)
    played = play_stage(DEFAULT_FORMAT.stage_state(2, names), rounds=1)
    stage2_csv = to_csv(played, files["dir"] / "s2.csv")
    with pytest.raises(SystemExit):
        run_annex(files, "--stage1", str(csv_path), "--stage2", str(stage2_csv))
