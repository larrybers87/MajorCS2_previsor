"""Stage ao vivo, rotina por rodada, Simulador, servidor e conferência com a Wikipedia.

Tudo com dados sintéticos em pastas temporárias; nada toca ``predictions/``.
"""

import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import numpy as np
import pandas as pd
import pytest

from sim import predict_stage2, round_update
from sim.export_site import latest_update, stage2_live
from sim.format_config import DEFAULT_FORMAT
from sim.live import Pick, apply_picks, full_round, official_model, stage_view
from sim.results import ResultRow, build_state, read_results
from sim.singapore2026 import ENTRANTS, ROSTERS
from sim.site_server import Handler, parse_request, simulate
from sim.stages import entrants_by_seed, stage2_names, stage3_names
from sim.wiki_check import compare_with_csv, parse_matches
from swiss import apply_results, best_of, current_round, pair_round, records

from conftest import NAMES

HEADER = "round,team_a,team_b,score_a,score_b,best_of\n"


def fake_seeds() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": [e.name for e in ENTRANTS],
            "vrs_name": [e.vrs_name for e in ENTRANTS],
            "region": "x",
            "vrs_points": [2000 - 20 * i for i in range(32)],
            "pre_event_seed": range(1, 33),
            "stage": [e.stage for e in ENTRANTS],
        }
    )


def play(state, rounds=5):
    """Vence sempre o primeiro time de cada par da engine."""
    for _ in range(rounds):
        if current_round(state) is None:
            break
        state = apply_results(state, [(p.team_a, p.team_b) for p in pair_round(state)])
    return state


def rows_of(state):
    rows = []
    for line, m in enumerate(state.matches, start=2):
        wins, losses = records(state.before_round(m.round))[m.team_a]
        fmt = best_of(wins, losses, state.all_best_of_three)
        score = (2, 1) if fmt == 3 else (13, 9)
        a, b = score if m.winner == m.team_a else score[::-1]
        rows.append(ResultRow(m.round, m.team_a, m.team_b, a, b, fmt, line))
    return rows


def to_csv(rows, path):
    text = HEADER + "".join(
        f"{r.round},{r.team_a},{r.team_b},{'' if r.score_a is None else r.score_a},"
        f"{'' if r.score_b is None else r.score_b},{r.best_of}\n"
        for r in rows
    )
    path.write_text(text, encoding="utf-8")
    return path


def empty_stage(names=NAMES):
    return DEFAULT_FORMAT.stage_state(1, names)


# ---------- escolhas e visão ----------


def first_winners(state):
    return [Pick(current_round(state), p.team_a, p.team_b, p.team_a) for p in pair_round(state)]


def test_picks_advance_the_bracket_with_the_engine():
    base = empty_stage()
    picks = first_winners(base)
    state, chosen, ignored = apply_picks(base, picks[:7])
    assert current_round(state) == 1 and len(chosen) == 7 and not ignored
    state, chosen, _ = apply_picks(base, picks)
    assert current_round(state) == 2 and len(chosen) == 8
    # A rodada seguinte é exatamente a da engine, ainda pendente.
    expected = {p.pair for p in pair_round(play(base, 1))}
    assert {m.pair for m in state.round_matches(2)} == expected
    assert all(m.winner is None for m in state.round_matches(2))


def test_full_simulation_by_picks_matches_the_engine():
    base = empty_stage()
    final = play(base)
    picks = [Pick(m.round, m.team_a, m.team_b, m.winner) for m in final.matches]
    state, chosen, ignored = apply_picks(base, list(reversed(picks)))
    assert current_round(state) is None and len(chosen) == 33 and not ignored
    view = stage_view(state, chosen=chosen)
    assert view["completo"] and len(view["classificados"]) == 8
    assert [len(r) for r in view["rodadas"]] == [8, 8, 8, 6, 3]
    assert {m["origem"] for r in view["rodadas"] for m in r} == {"escolha"}
    assert sum(map(len, view["finais"].values())) == 16


def test_real_results_cannot_be_overridden_and_stale_picks_are_reported():
    base = empty_stage()
    real = play(base, 1)
    opposite = [
        Pick(1, m.team_a, m.team_b, m.team_b) for m in real.round_matches(1)
    ]
    state, chosen, ignored = apply_picks(real, opposite)
    assert not chosen and len(ignored) == 8
    assert [m.winner for m in state.round_matches(1)] == [m.winner for m in real.round_matches(1)]
    # Escolha na rodada 2 que deixa de existir ao mudar a rodada 1.
    picks = first_winners(base)
    second = first_winners(play(base, 1))
    first = picks[0]
    changed = [Pick(1, first.team_a, first.team_b, first.team_b), *picks[1:]]
    # (Inverter TODOS os vencedores manteria os mesmos pares, agora no grupo 0-1.)
    _, _, stale = apply_picks(base, changed + second)
    assert stale and all(p.round == 2 for p in stale)


def test_full_round_rejects_a_partial_round_with_other_pairings():
    base = empty_stage()
    odd = [ResultRow(1, NAMES[0], NAMES[1], None, None, 1, 2)]
    with pytest.raises(ValueError, match="liste no CSV"):
        full_round(build_state(base, odd))


def test_view_orients_by_seed_and_keeps_real_scores():
    base = empty_stage()
    rows = [ResultRow(1, NAMES[8], NAMES[0], 13, 4, 1, 2)]  # seed 9 vence o seed 1
    state, _, _ = apply_picks(build_state(base, rows), ())
    view = stage_view(state, rows, prob_fn=lambda a, b, bo: 0.75)
    match = view["rodadas"][0][0]
    assert (match["a"], match["b"], match["placar_a"], match["placar_b"]) == (
        NAMES[0], NAMES[8], 4, 13,
    )  # fmt: skip
    assert match["origem"] == "real" and match["p_a"] == 0.75
    assert [m["origem"] for m in view["rodadas"][0][1:]] == ["pendente"] * 7


# ---------- previsão oficial sintética, rotina por rodada e site ----------


@pytest.fixture
def world(tmp_path):
    seeds = fake_seeds()
    seeds_path = tmp_path / "seeds.csv"
    seeds.to_csv(seeds_path, index=False)
    model = tmp_path / "model.json"
    model.write_text(
        json.dumps(
            {"train_last": "2026-11-01", "b0_config": {"transform": "points"},
             "rule": {"mode": "faixa", "ci": [0.0, 1.0],
                      "variants": [{"w": 0.0, "beta": 0.15}, {"w": 1.0, "beta": 0.23}]}}
        ),
        encoding="utf-8",
    )  # fmt: skip
    stage1 = play(DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1)))
    stage1_csv = to_csv(rows_of(stage1), tmp_path / "stage1.csv")
    official_root = tmp_path / "official"
    assert predict_stage2.main(
        ["--stage1", str(stage1_csv), "--sims", "2000", "--out", str(official_root),
         "--seeds-file", str(seeds_path), "--params-file", str(model)]
    ) == 0  # fmt: skip
    official = next(official_root.iterdir())
    history = pd.DataFrame(
        {
            "date": pd.date_range("2026-10-01", periods=3), "team_a": "BC.Game",
            "team_b": "Ninjas in Pyjamas", "roster_a": ", ".join(ROSTERS["GOSH"]),
            "roster_b": ", ".join(ROSTERS["NiP"]),
            "points_a": pd.array([1300] * 3, dtype="Int64"),
            "points_b": pd.array([1500] * 3, dtype="Int64"), "team_a_won": True,
        }
    )  # fmt: skip
    history.to_parquet(tmp_path / "matches.parquet")
    b1 = tmp_path / "b1.json"
    b1.write_text(
        json.dumps(
            {"train_last": "2026-11-01",
             "chosen": {"kind": "EloConfig", "s": 0.5, "k": 20, "half_life": None,
                        "provisional": 2}}
        ),
        encoding="utf-8",
    )  # fmt: skip
    base2 = DEFAULT_FORMAT.stage_state(2, stage2_names(seeds, stage1))
    return {
        "dir": tmp_path, "seeds": seeds, "seeds_path": seeds_path, "stage1_csv": stage1_csv,
        "official": official, "base2": base2, "b1": b1,
        "matches": tmp_path / "matches.parquet",
    }  # fmt: skip


def update(world, rows, *extra):
    stage2_csv = to_csv(rows, world["dir"] / "stage2.csv")
    out = world["dir"] / "updates"
    code = round_update.main(
        ["--stage1", str(world["stage1_csv"]), "--stage2", str(stage2_csv), "--sims", "2000",
         "--seeds-file", str(world["seeds_path"]), "--official-dir", str(world["official"]),
         "--matches-file", str(world["matches"]), "--b1-params-file", str(world["b1"]),
         "--out", str(out), *extra]
    )  # fmt: skip
    return code, out


def snapshot(folder):
    return {p.name: p.read_bytes() for p in folder.iterdir()}


def test_round_one_belongs_to_the_official_prediction(world, capsys):
    code, out = update(world, rows_of(play(world["base2"], 1))[:3])
    assert code == 1 and "previsão oficial" in capsys.readouterr().out
    assert not out.exists()


def test_round_update_writes_a_new_folder_and_keeps_the_official(world):
    before = snapshot(world["official"])
    code, out = update(world, rows_of(play(world["base2"], 1)))
    assert code == 0 and snapshot(world["official"]) == before
    folder = next((out / "round2").iterdir())
    pairings = pd.read_csv(folder / "pairings.csv")
    assert len(pairings) == 8 and set(pairings["rodada"]) == {2}
    assert set(pairings["origem"]) == {"engine"}
    expected = {p.pair for p in pair_round(play(world["base2"], 1))}
    assert {frozenset((r.time_a, r.time_b)) for r in pairings.itertuples()} == expected
    mean = (pairings["P(time_a vence) w=0"] + pairings["P(time_a vence) w=1"]) / 2
    np.testing.assert_allclose(pairings["P(time_a vence)"], mean, atol=2e-6)
    table = pd.read_csv(folder / "probabilities.csv")
    assert table["P(avançar)"].sum() == pytest.approx(8.0, abs=1e-4)
    won = table[table["cartel_atual"] == "1-0"]
    assert (won["P(0-3)"] == 0).all()
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["b1_rounds"] == [1] and meta["v2_mismatches"] == []
    assert (folder / "b1_ratings.csv").exists()
    assert latest_update(out)["rodada"] == 2
    # Uma segunda execução não sobrescreve a primeira.
    update(world, rows_of(play(world["base2"], 1)))
    assert len(list((out / "round2").iterdir())) == 2


def test_partial_round_is_a_fact_but_not_a_rating(world):
    rows = rows_of(play(world["base2"], 1))
    code, out = update(world, rows)
    complete = pd.read_csv(next((out / "round2").iterdir()) / "b1_ratings.csv")
    two = rows_of(play(world["base2"], 2))
    partial = rows + [r for r in two if r.round == 2][:1]
    code, out = update(world, partial)
    assert code == 0
    folder = max((out / "round2").iterdir(), key=lambda p: p.stat().st_mtime_ns)
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert len(meta["decided_in_current_round"]) == 1 and meta["b1_rounds"] == [1]
    pd.testing.assert_frame_equal(pd.read_csv(folder / "b1_ratings.csv"), complete)
    assert len(pd.read_csv(folder / "pairings.csv")) == 7
    assert "PARCIAL" in (folder / "summary.md").read_text(encoding="utf-8")


def test_v2_divergence_is_reported_not_forced(world):
    rows = rows_of(play(world["base2"], 1))
    engine = pair_round(play(world["base2"], 1))
    # Troca os adversários de duas partidas do grupo 1-0.
    first, second = engine[0], engine[1]
    official = [(first.team_a, second.team_b), (second.team_a, first.team_b)] + [
        (p.team_a, p.team_b) for p in engine[2:]
    ]
    rows += [ResultRow(2, a, b, None, None, 1, 0) for a, b in official]
    code, out = update(world, rows)
    assert code == 0
    folder = next((out / "round2").iterdir())
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["v2_mismatches"]
    pairings = pd.read_csv(folder / "pairings.csv")
    assert set(pairings["origem"]) == {"anunciada"}
    assert {frozenset((r.time_a, r.time_b)) for r in pairings.itertuples()} == {
        frozenset(p) for p in official
    }


def test_finished_stage2_gives_stage3_seeds(world):
    final = play(world["base2"])
    code, out = update(world, rows_of(final))
    assert code == 0
    folder = next((out / "final").iterdir())
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["stage3_seeds"] == stage3_names(world["seeds"], final)
    assert not (folder / "pairings.csv").exists()


def test_official_model_rejects_other_vrs_points(world):
    seeds = world["seeds"].copy()
    seeds["vrs_points"] += 1
    with pytest.raises(ValueError, match="pontos VRS"):
        official_model(seeds, world["official"])


def test_live_view_for_the_site(world):
    model = official_model(world["seeds"], world["official"])
    names = list(world["base2"].names)
    empty = stage2_live(names, [], model)
    assert empty["partidas_jogadas"] == 0 and empty["resumo"] is None
    assert [len(r) for r in empty["rodadas"]] == [8]
    live = stage2_live(names, rows_of(play(world["base2"], 1)), model)
    assert live["partidas_jogadas"] == 8 and live["resumo"]["n"] == 8
    assert [len(r) for r in live["rodadas"]] == [8, 8]
    assert all("previsao" in m for m in live["rodadas"][0])
    assert all("previsao" not in m for m in live["rodadas"][1])


def test_simulate_uses_real_results_or_starts_from_scratch(world):
    stage2_csv = to_csv(rows_of(play(world["base2"], 1)), world["dir"] / "s2.csv")
    paths = {
        "stage1_path": world["stage1_csv"], "stage2_path": stage2_csv,
        "seeds_path": world["seeds_path"], "official_dir": world["official"],
    }  # fmt: skip
    view = simulate(2, [], False, **paths)
    assert [m["origem"] for m in view["rodadas"][0]] == ["real"] * 8
    assert "p_a" in view["rodadas"][1][0]
    scratch = simulate(2, [], True, **paths)
    assert [m["origem"] for m in scratch["rodadas"][0]] == ["pendente"] * 8
    stage1 = simulate(1, [], True, **paths)
    assert "p_a" not in stage1["rodadas"][0][0]
    assert len(read_results(world["stage1_csv"])) == 33  # nada foi alterado em disco


# ---------- servidor ----------


@pytest.mark.parametrize(
    "body",
    [
        [],
        {"stage": 3},
        {"stage": 1, "picks": "x"},
        {"stage": 1, "picks": [{"rodada": 1}]},
        {"stage": 1, "picks": [{}] * 100},
    ],
)
def test_server_rejects_bad_requests(body):
    with pytest.raises(ValueError):
        parse_request(body)


def test_server_only_serves_the_app_to_local_hosts():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    def request(method, path, headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            response.read()
            return response.status
        finally:
            connection.close()

    try:
        assert request("GET", "/app/index.html") == 200
        assert request("GET", "/app/index.html", {"Host": "exemplo.invalido"}) == 403
        for path in ("/CLAUDE.md", "/.git/config", "/app/../CLAUDE.md", "/data/manual/x.csv"):
            assert request("GET", path) == 404
        assert request("POST", "/api/simulate", {"Content-Type": "text/plain"}, "{}") == 415
        json_headers = {"Content-Type": "application/json"}
        assert request("POST", "/api/simulate", json_headers, '{"stage": 9}') == 400
        assert request("POST", "/api/outra", json_headers, "{}") == 404
    finally:
        server.shutdown()
        server.server_close()


# ---------- Wikipedia (conferência secundária) ----------

WIKITEXT = """
== Stage 2 ==
=== Results ===
==== Round 1 ====
{{Esports match
| match = 0–0 | date = November 28
| team1 = FUT | team1score = 1
| team2 = [[FlyQuest]] | team2score = 0
| map1 = Nuke | map1team1score = 13 | map1team2score = 7
| location = Singapore}}
{{Esports match
| team1 = THE ONE{{efn|name=1winName}} | team1score =
| team2 = [[Eternal Fire (esports)|Eternal Fire]] | team2score =
| map1 = TBD}}
==== Round 3 ====
{{Esports match
| team1 = Nemiga | team1score = 2
| team2 = [[Ninjas in Pyjamas]] | team2score = 1
| map1 = Nuke | map1team1score = 13 | map1team2score = 7}}
{{Esports match
| team1 = TBD | team1score =
| team2 = TBD | team2score =}}
== Stage 3 ==
{{Esports match | team1 = MOUZ | team2 = Legacy }}
"""


def test_wiki_parser_and_comparison():
    wiki = parse_matches(WIKITEXT, 2)
    assert [(w.round, w.team_a, w.team_b, w.winner, w.score_a, w.score_b) for w in wiki] == [
        (1, "FUT", "FlyQuest", "FUT", 13, 7),
        (1, "THE ONE", "Eternal Fire", None, None, None),
        (3, "Nemiga", "NiP", "Nemiga", 2, 1),
    ]
    same = [ResultRow(1, "FlyQuest", "FUT", 7, 13, 1, 2)]
    assert compare_with_csv(same, wiki) == [
        "R3 Nemiga x NiP: jogada segundo a Wikipedia, ausente no CSV"
    ]
    different = [
        ResultRow(1, "FUT", "FlyQuest", 13, 9, 1, 2),
        ResultRow(3, "Nemiga", "NiP", 1, 2, 3, 3),
        ResultRow(2, "FUT", "G2", None, None, 1, 4),
    ]
    notes = compare_with_csv(different, wiki)
    assert len(notes) == 3
    assert "placar no CSV 13-9" in notes[0] and "vencedor no CSV NiP" in notes[1]
    with pytest.raises(ValueError, match="Stage 1"):
        parse_matches(WIKITEXT, 1)
