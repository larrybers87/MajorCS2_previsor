"""CSV de resultados, formato, encadeamento e scripts de previsão (dados sintéticos)."""

import json

import numpy as np
import pandas as pd
import pytest

from sim import predict_stage2, v3_stage1
from sim.chain import simulate_chained
from sim.format_config import DEFAULT_FORMAT
from sim.results import build_state, format_notes, pairing_report, read_results
from sim.singapore2026 import ENTRANTS
from sim.stages import entrants_by_seed, stage2_names
from swiss import advancing_teams, current_round, pair_round, apply_results, simulate_stage

HEADER = "round,team_a,team_b,score_a,score_b,best_of\n"


def fake_seeds() -> pd.DataFrame:
    """Pontos fictícios, decrescentes por stage (3 > 2 > 1)."""
    ordered = sorted(ENTRANTS, key=lambda e: -e.stage)
    return pd.DataFrame(
        {
            "name": [e.name for e in ordered],
            "region": "x",
            "vrs_points": [2000 - 20 * i for i in range(32)],
            "pre_event_seed": range(1, 33),
            "stage": [e.stage for e in ordered],
        }
    )


@pytest.fixture
def files(tmp_path):
    seeds = tmp_path / "seeds.csv"
    fake_seeds().to_csv(seeds, index=False)
    params = tmp_path / "params.json"
    params.write_text(
        json.dumps(
            {"beta": 0.15, "transform": "points", "train_last": "2026-11-01",
             "sensitivity_bo1": {"beta": 0.23}}
        ),
        encoding="utf-8",
    )  # fmt: skip
    return {"seeds": seeds, "params": params, "dir": tmp_path}


def play_stage(state, rounds=5, seed=0):
    """Joga ``rounds`` rodadas com a engine e vencedores sorteados."""
    rng = np.random.default_rng(seed)
    for _ in range(rounds):
        if current_round(state) is None:
            break
        results = []
        for p in pair_round(state):
            pair = (p.team_a, p.team_b)
            results.append(pair if rng.random() < 0.5 else pair[::-1])
        state = apply_results(state, results)
    return state


def to_csv(state, path):
    from swiss import best_of, records

    lines = [HEADER]
    for m in state.matches:
        wins, losses = records(state.before_round(m.round))[m.team_a]
        fmt = best_of(wins, losses, state.all_best_of_three)
        high, low = (2, 1) if fmt == 3 else (13, 9)
        a, b = (high, low) if m.winner == m.team_a else (low, high)
        lines.append(f"{m.round},{m.team_a},{m.team_b},{a},{b},{fmt}\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path


def stage1_base():
    return DEFAULT_FORMAT.stage_state(1, entrants_by_seed(fake_seeds(), 1))


def test_format_defaults():
    assert not DEFAULT_FORMAT.stage_state(1, entrants_by_seed(fake_seeds(), 1)).all_best_of_three
    assert 3 in DEFAULT_FORMAT.all_best_of_three_stages
    assert (DEFAULT_FORMAT.final_best_of, DEFAULT_FORMAT.third_place_best_of) == (5, 3)


def test_csv_roundtrip(tmp_path):
    state = play_stage(stage1_base())
    rows = read_results(to_csv(state, tmp_path / "s1.csv"))
    rebuilt = build_state(stage1_base(), rows)
    assert rebuilt == state
    assert format_notes(rebuilt, rows) == []
    assert pairing_report(rebuilt) == []


def test_csv_accepts_aliases_semicolon_bom_and_pending(tmp_path):
    path = tmp_path / "s.csv"
    path.write_text(
        "round;team_a;team_b;score_a;score_b;best_of\n1;Ninjas in Pyjamas;M80;13;7;bo1\n"
        "1;parivision;9z;;;\n;;;;;\n",
        encoding="utf-8-sig",
    )
    rows = read_results(path)
    assert [(r.team_a, r.winner, r.best_of) for r in rows] == [
        ("NiP", "NiP", 1), ("PVISION", None, None),
    ]  # fmt: skip


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("1,NiP,M80,13,13,1", "empatado"),
        ("1,NiP,M80,13,,1", "dois placares"),
        ("1,NiP,TYLOO,13,3,1", "desconhecido"),
        ("1,NiP,M80,13,3,2", "best_of"),
        (",NiP,M80,13,3,1", "rodada"),
    ],
)
def test_csv_errors(tmp_path, line, message):
    path = tmp_path / "s.csv"
    path.write_text(HEADER + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        read_results(path)


def test_format_and_pairing_notes(tmp_path):
    names = stage1_base().names
    pairs = [(names[2 * i], names[2 * i + 1]) for i in range(8)]  # 1x2, 3x4, ...
    path = tmp_path / "s.csv"
    path.write_text(
        HEADER + "".join(f"1,{a},{b},2,0,3\n" for a, b in pairs), encoding="utf-8"
    )
    rows = read_results(path)
    state = build_state(stage1_base(), rows)
    assert len(format_notes(state, rows)) == 8  # CSV diz Bo3 na rodada 1
    assert pairing_report(state)[0].startswith("rodada 1:")


def test_stage2_seeding():
    state = play_stage(stage1_base())
    names = stage2_names(fake_seeds(), state)
    assert names[:8] == entrants_by_seed(fake_seeds(), 2)
    assert names[8:] == advancing_teams(state)


def coin(a, b, best_of):
    return 0.5


def favorite(a, b, best_of):
    strength = {n: -i for i, n in enumerate(fake_seeds()["name"])}
    return 1.0 if strength[a] > strength[b] else 0.0


def test_chain_with_finished_stage1_equals_direct_simulation():
    stage1 = play_stage(stage1_base(), seed=4)
    invited = entrants_by_seed(fake_seeds(), 2)
    chained = simulate_chained(favorite, stage1, invited, 20, np.random.default_rng(0))
    base2 = DEFAULT_FORMAT.stage_state(2, stage2_names(fake_seeds(), stage1))
    direct = simulate_stage(favorite, base2, 20, np.random.default_rng(0))
    for i, team in enumerate(direct.teams):
        j = chained.teams.index(team)
        np.testing.assert_array_equal(chained.record_counts[j], direct.record_counts[i])
        assert chained.participation_counts[j] == 20
    assert chained.participation_counts.sum() == 16 * 20
    # Rodada 1: convidado i enfrenta o seed i+9.
    for i in range(8):
        assert chained.opening_counts[i, chained.teams.index(base2.names[8 + i])] == 20


def test_chain_totals_and_marginals():
    n = 60_000
    invited = entrants_by_seed(fake_seeds(), 2)
    result = simulate_chained(coin, stage1_base(), invited, n, np.random.default_rng(2))
    np.testing.assert_array_equal(result.participation_counts[16:], n)
    np.testing.assert_array_equal(result.record_counts.sum(axis=1), result.participation_counts)
    np.testing.assert_array_equal(result.record_counts.sum(axis=0), np.array([2, 3, 3, 3, 3, 2]) * n)
    # Moeda justa: cada time do Stage 1 chega ao Stage 2 com probabilidade 1/2.
    np.testing.assert_allclose(result.participation_counts[:16] / n, 0.5, atol=0.01)
    np.testing.assert_array_equal(result.opening_counts.sum(axis=1), n)


def run_predict(files, *args):
    out = files["dir"] / "out"
    code = predict_stage2.main(
        [*args, "--sims", "3000", "--out", str(out), "--seeds-file", str(files["seeds"]),
         "--params-file", str(files["params"])]
    )  # fmt: skip
    assert code == 0
    return max(out.iterdir(), key=lambda p: p.stat().st_mtime_ns)


def test_predict_stage2_full_and_live(files):
    stage1 = play_stage(stage1_base(), seed=5)
    stage1_csv = to_csv(stage1, files["dir"] / "s1.csv")
    folder = run_predict(files, "--stage1", str(stage1_csv))
    table = pd.read_csv(folder / "probabilities.csv")
    assert len(table) == 16
    assert table["P(avançar)"].sum() == pytest.approx(8.0, abs=1e-4)
    opening = pd.read_csv(folder / "opening_round.csv")
    assert list(zip(opening["seed_a"], opening["seed_b"])) == [(s, s + 8) for s in range(1, 9)]
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["stage2_seeds"][8:] == advancing_teams(stage1)
    assert (folder / "summary.md").exists()

    base2 = DEFAULT_FORMAT.stage_state(2, stage2_names(fake_seeds(), stage1))
    stage2_csv = to_csv(play_stage(base2, rounds=2, seed=6), files["dir"] / "s2.csv")
    live = run_predict(files, "--stage1", str(stage1_csv), "--stage2", str(stage2_csv))
    assert live != folder
    upcoming = pd.read_csv(live / "next_round.csv")
    assert set(upcoming["rodada"]) == {3} and len(upcoming) == 8
    live_table = pd.read_csv(live / "probabilities.csv").set_index("time")
    played = play_stage(base2, rounds=2, seed=6)
    from swiss import records

    for team, (wins, losses) in records(played).items():
        if wins == 2:
            assert live_table.loc[team, "P(0-3)"] == live_table.loc[team, "P(1-3)"] == 0


def test_predict_stage2_conditioned(files):
    partial = play_stage(stage1_base(), rounds=3, seed=8)
    csv_path = to_csv(partial, files["dir"] / "partial.csv")
    folder = run_predict(files, "--conditioned", "--stage1", str(csv_path))
    table = pd.read_csv(folder / "probabilities.csv")
    assert len(table) == 24
    assert table["P(participa)"].sum() == pytest.approx(16.0, abs=1e-4)
    assert table["P(avançar)"].sum() == pytest.approx(8.0, abs=1e-4)
    assert (table["P(avançar)"] <= table["P(participa)"] + 1e-9).all()


def test_params_trained_during_the_major_are_rejected(files, capsys):
    params = json.loads(files["params"].read_text(encoding="utf-8"))
    files["params"].write_text(json.dumps(params | {"train_last": "2026-11-23"}), encoding="utf-8")
    code = predict_stage2.main(
        ["--conditioned", "--sims", "10", "--out", str(files["dir"] / "out"),
         "--seeds-file", str(files["seeds"]), "--params-file", str(files["params"])]
    )  # fmt: skip
    assert code == 1 and "período do Major" in capsys.readouterr().out


def test_v3_hides_record_metrics_while_stage_is_open(files):
    csv_path = to_csv(play_stage(stage1_base(), rounds=3), files["dir"] / "partial.csv")
    out = files["dir"] / "v3"
    code = v3_stage1.main(
        ["--results", str(csv_path), "--sims", "500", "--out", str(out),
         "--seeds-file", str(files["seeds"]), "--params-file", str(files["params"])]
    )  # fmt: skip
    assert code == 0
    meta = json.loads((next(out.iterdir()) / "meta.json").read_text(encoding="utf-8"))
    assert "log_score_cartel" not in meta["scores"] and meta["scores"]["partidas"] == 24
    assert meta["params_file_sha256"]


def test_predict_stage2_requires_complete_stage1(files, capsys):
    csv_path = to_csv(play_stage(stage1_base(), rounds=4), files["dir"] / "partial.csv")
    with pytest.raises(SystemExit):
        run_predict(files, "--stage1", str(csv_path))
    assert "incompleto" in capsys.readouterr().err


def test_v3_report(files):
    state = play_stage(stage1_base(), seed=9)
    csv_path = to_csv(state, files["dir"] / "s1.csv")
    out = files["dir"] / "v3"
    code = v3_stage1.main(
        ["--results", str(csv_path), "--sims", "3000", "--out", str(out),
         "--seeds-file", str(files["seeds"]), "--params-file", str(files["params"])]
    )  # fmt: skip
    assert code == 0
    folder = next(out.iterdir())
    text = (folder / "summary.md").read_text(encoding="utf-8")
    assert "RETROSPECTIVO" in text and "sem divergências" in text
    matches = pd.read_csv(folder / "matches.csv")
    assert len(matches) == 33
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["scores"]["times_encerrados"] == 16
