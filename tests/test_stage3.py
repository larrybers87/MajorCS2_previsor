"""Combinação B0/B1, checagem de desastre e previsão do Stage 3 (dados sintéticos)."""

import json
import math

import numpy as np
import pandas as pd
import pytest

from sim import predict_stage3, stage3_check
from sim.stage3_check import BACK_TO_B0, BOTH_FAILED, KEEP, check_table, decide
from sim.stage3_model import (
    B0_BETAS,
    B1_CONFIG,
    SENSITIVITY_GRID,
    assert_frozen_b1_code,
    b1_ratings_at,
    load_b1_config,
    load_stages,
    mean_prob_fn,
    prob_fns,
    simulate_average,
    vrs_points,
)
from backtest.v3_compare import B1_BETAS
from sim.format_config import DEFAULT_FORMAT
from sim.results import ResultRow
from sim.stages import stage3_names

from conftest import NAMES
from test_live import play, rows_of, to_csv, world  # noqa: F401 (world é fixture)


def test_preregistered_constants():
    assert B0_BETAS == {0.0: 0.155760, 1.0: 0.236080}
    assert B1_BETAS == {0.0: 0.350419, 1.0: 0.532006}
    assert (stage3_check.BOOTSTRAP_REPS, stage3_check.BOOTSTRAP_SEED) == (10_000, 20261202)
    assert SENSITIVITY_GRID == {"Vitality": (0, -25, -50), "Legacy": (0, -50, -100)}
    # Confirmados em 27/11, antes de os seeds do Stage 3 existirem.
    assert (predict_stage3.SIMULATIONS, predict_stage3.RNG_SEED) == (200_000, 20261202)


def test_frozen_b1_code_and_config(world):  # noqa: F811
    assert_frozen_b1_code()
    assert load_b1_config(world["b1"]) == B1_CONFIG
    other = json.loads(world["b1"].read_text(encoding="utf-8"))
    other["chosen"]["k"] = 30
    world["b1"].write_text(json.dumps(other), encoding="utf-8")
    with pytest.raises(ValueError, match="congelada"):
        load_b1_config(world["b1"])


def test_combination_gives_a_quarter_to_each_variant():
    points = {"A": 1700.0, "B": 1500.0}
    ratings = {"A": 1800.0, "B": 1750.0}
    fns = prob_fns(points, ratings)
    assert set(fns) == {("B0", 0.0), ("B0", 1.0), ("B1", 0.0), ("B1", 1.0)}
    logistic = lambda x: 1 / (1 + math.exp(-x))  # noqa: E731
    expected = [logistic(0.155760 * 2), logistic(0.236080 * 2),
                logistic(0.350419 * 0.5), logistic(0.532006 * 0.5)]  # fmt: skip
    assert mean_prob_fn(list(fns.values()))("A", "B", 1) == pytest.approx(np.mean(expected))
    assert set(prob_fns(points, ratings, ["B0"])) == {("B0", 0.0), ("B0", 1.0)}


def test_discount_gives_the_same_log_odds_shift_in_both_models():
    points = {"A": 1700.0, "B": 1500.0}
    ratings = {"A": 1800.0, "B": 1750.0}
    base = prob_fns(points, ratings)
    cut = prob_fns(points, ratings, discounts={"A": -50})
    logit = lambda p: math.log(p / (1 - p))  # noqa: E731
    for w in (0.0, 1.0):
        shifts = [logit(cut[(m, w)]("A", "B", 1)) - logit(base[(m, w)]("A", "B", 1))
                  for m in ("B0", "B1")]  # fmt: skip
        assert shifts[0] == pytest.approx(-50 * B0_BETAS[w] / 100)
        assert shifts[1] == pytest.approx(shifts[0])
        # Valores da tabela da emenda 4 (cerca de -22 pontos no B1).
        assert -50 * B0_BETAS[w] / B1_BETAS[w] == pytest.approx(-22.2, abs=0.05)


@pytest.mark.parametrize(
    ("mean", "b0", "b1", "decision", "models"),
    [
        (0.80, 0.70, 0.90, BACK_TO_B0, ["B0"]),
        (0.80, 0.90, 0.70, BOTH_FAILED, ["B0", "B1"]),
        (0.60, 0.70, 0.90, KEEP, ["B0", "B1"]),
        (0.60, 0.90, 0.70, KEEP, ["B0", "B1"]),
        (math.log(2), 0.70, 0.90, KEEP, ["B0", "B1"]),  # igual ao 50% não é pior
    ],
)
def test_decision_table_of_amendment_1(mean, b0, b1, decision, models):
    table = pd.DataFrame(
        {"log_loss_media": [mean] * 20, "log_loss_B0": b0, "log_loss_B1": b1}
    )
    result = decide(table)
    assert (result["decisao"], result["modelos"]) == (decision, models)


def test_one_sided_test_needs_significance():
    noisy = [0.1, 1.5] * 20  # média acima de ln 2, mas dentro do ruído
    table = pd.DataFrame({"log_loss_media": noisy, "log_loss_B0": 0.5, "log_loss_B1": 0.9})
    result = decide(table)
    assert result["a_media_menos_ln2"] > 0 and not result["a_vale"]
    assert result["decisao"] == KEEP


def complete(world):  # noqa: F811
    final = play(world["base2"])
    path = to_csv(rows_of(final), world["dir"] / "s2_full.csv")
    return final, path


def test_check_never_uses_the_current_round(world):  # noqa: F811
    _, path = complete(world)
    stage1, rows1, stage2, rows2 = load_stages(world["seeds"], world["stage1_csv"], path)
    history = pd.read_parquet(world["matches"])
    stages = [(1, stage1, rows1), (2, stage2, rows2)]
    table = check_table(world["seeds"], history, B1_CONFIG, stages)
    assert len(table) == 66
    keys = list(zip(table["stage"], table["rodada"], table["seed_a"]))
    assert keys == sorted(keys)
    # Rodada 2 do Stage 2: ratings com o Stage 1 e a rodada 1 do Stage 2, nada mais.
    ratings = b1_ratings_at(
        history, world["seeds"], B1_CONFIG,
        {1: rows1, 2: [r for r in rows2 if r.round < 2]},
    )  # fmt: skip
    fns = prob_fns(vrs_points(world["seeds"]), ratings)
    row = table[(table["stage"] == 2) & (table["rodada"] == 2)].iloc[0]
    for (model, w), fn in fns.items():
        expected = fn(row["time_a"], row["time_b"], row["best_of"])
        assert row[f"p_{model}_w{w:g}"] == pytest.approx(expected)
    # Inverter o último resultado não muda probabilidade alguma.
    last = rows2[-1]
    flipped = rows2[:-1] + [
        ResultRow(last.round, last.team_a, last.team_b, last.score_b, last.score_a,
                  last.best_of, last.line)
    ]  # fmt: skip
    again = check_table(world["seeds"], history, B1_CONFIG,
                        [(1, stage1, rows1), (2, stage2, flipped)])  # fmt: skip
    pd.testing.assert_series_equal(table["p_media"], again["p_media"])


def arguments(world, stage2_csv):  # noqa: F811
    return [
        "--stage1", str(world["stage1_csv"]), "--stage2", str(stage2_csv),
        "--seeds-file", str(world["seeds_path"]), "--matches-file", str(world["matches"]),
        "--b1-params-file", str(world["b1"]),
    ]  # fmt: skip


def test_incomplete_stage2_blocks_the_check(world, capsys):  # noqa: F811
    path = to_csv(rows_of(play(world["base2"], 4)), world["dir"] / "s2_part.csv")
    out = world["dir"] / "stage3" / "disaster_check"
    assert stage3_check.main([*arguments(world, path), "--out", str(out)]) == 1
    assert "não terminou" in capsys.readouterr().out and not out.exists()


def test_check_then_prediction(world, capsys):  # noqa: F811
    final, path = complete(world)
    root = world["dir"] / "stage3"
    check_args = [*arguments(world, path), "--out", str(root / "disaster_check")]
    predict_args = [*arguments(world, path), "--out", str(root), "--sims", "2000"]
    # Sem a checagem não há previsão.
    assert predict_stage3.main(predict_args) == 1
    assert stage3_check.main(check_args) == 0
    assert stage3_check.main(check_args) == 1  # uma única vez
    assert "única vez" in capsys.readouterr().out
    assert predict_stage3.main(predict_args) == 0

    folder = next(p for p in root.iterdir() if p.name != "disaster_check")
    table = pd.read_csv(folder / "probabilities.csv").set_index("time")
    assert table["P(avançar)"].sum() == pytest.approx(8.0, abs=1e-4)
    columns = [f"P({k})" for k in ("3-0", "3-1", "3-2", "2-3", "1-3", "0-3")]
    np.testing.assert_allclose(table[columns].sum(), [2, 3, 3, 3, 3, 2], atol=1e-4)
    assert (table["P(avançar) mín"] <= table["P(avançar)"] + 1e-9).all()
    assert (table["P(avançar)"] <= table["P(avançar) máx"] + 1e-9).all()
    # Com desconto, o próprio time perde chance: o mínimo fica abaixo do oficial.
    for team in SENSITIVITY_GRID:
        assert table.loc[team, "P(avançar) mín"] < table.loc[team, "P(avançar)"]
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    assert meta["stage3_seeds"] == stage3_names(world["seeds"], final)
    assert not meta["format_officially_confirmed"]
    # Os cenários da grade não são publicados (emenda 4).
    assert sorted(p.name for p in folder.iterdir()) == [
        "b1_ratings.csv", "meta.json", "opening_round.csv", "positions.csv",
        "probabilities.csv", "summary.md", "supplement_b0_b1.csv",
    ]  # fmt: skip
    assert (pd.read_csv(folder / "opening_round.csv")["best_of"] == 3).all()

    # Suplementar: B0 e B1 separados; a oficial é a combinação do que a checagem mandou.
    parts = pd.read_csv(folder / "supplement_b0_b1.csv")
    assert list(parts["componente"].unique()) == ["B0", "B1"] and len(parts) == 32
    used = parts[parts["na_oficial"]]
    assert sorted(used["componente"].unique()) == (
        ["B0"] if meta["decision"] == BACK_TO_B0 else ["B0", "B1"]
    )
    for column in (*columns, "P(avançar)"):
        mean = used.groupby("time")[column].mean()
        np.testing.assert_allclose(mean.loc[table.index], table[column], atol=2e-6)
    for _, part in parts.groupby("componente"):
        assert part["P(avançar)"].sum() == pytest.approx(8.0, abs=1e-4)
    # O texto principal não traz as componentes.
    text = (folder / "summary.md").read_text(encoding="utf-8")
    assert "supplement_b0_b1.csv" in text and "| B0 |" not in text


def test_supplement_keeps_both_components_when_only_b0_is_official():
    base = DEFAULT_FORMAT.stage_state(3, NAMES)
    points = {n: 1800.0 - 20 * i for i, n in enumerate(NAMES)}
    ratings = {n: 1700.0 + 10 * i for i, n in enumerate(NAMES)}
    parts = predict_stage3.component_table(points, ratings, ["B0"], base, 500, 1)
    flags = parts.groupby("componente")["na_oficial"].unique().to_dict()
    assert (list(flags["B0"]), list(flags["B1"])) == ([True], [False])
    only_b0, _ = simulate_average(list(prob_fns(points, ratings, ["B0"]).values()), base, 500, 1)
    np.testing.assert_array_equal(
        parts[parts["componente"] == "B0"]["P(avançar)"], only_b0[:, :3].sum(axis=1)
    )


def test_prediction_rejects_inputs_that_changed_after_the_check(world, capsys):  # noqa: F811
    final, path = complete(world)
    root = world["dir"] / "stage3"
    assert stage3_check.main(
        [*arguments(world, path), "--out", str(root / "disaster_check")]
    ) == 0  # fmt: skip
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert predict_stage3.main([*arguments(world, path), "--out", str(root)]) == 1
    assert "entradas diferentes" in capsys.readouterr().out
