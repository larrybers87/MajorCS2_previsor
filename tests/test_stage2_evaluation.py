"""Avaliação oficial do Stage 2 (dados sintéticos; nenhum resultado real)."""

import math

import numpy as np
import pandas as pd
import pytest

from backtest import stage2_evaluation as ev
from sim.format_config import DEFAULT_FORMAT
from swiss import seed_strength_prob_fn
from swiss.simulate import probability_table, simulate_chunk

from conftest import NAMES
from test_live import play, rows_of, to_csv, world  # noqa: F401 (world é fixture)

SIMS = 4000


@pytest.mark.parametrize(
    ("difference", "error", "expected"),
    [
        (-0.0201, 0.01, ev.BETTER),
        (-0.02, 0.01, ev.INCONCLUSIVE),  # exatamente 2 EP
        (0.0, 0.01, ev.INCONCLUSIVE),
        (0.02, 0.01, ev.INCONCLUSIVE),
        (0.0201, 0.01, ev.WORSE),
    ],
)
def test_reading_rule_of_amendment_3(difference, error, expected):
    assert ev.label(difference, error) == expected


def test_fixed_parameters_are_the_preregistered_ones():
    assert (ev.VRS_FAVORITE_P, ev.BOOTSTRAP_REPS, ev.BOOTSTRAP_SEED) == (
        0.595137, 10_000, 20261128,
    )  # fmt: skip
    assert (ev.SIMULATIONS, ev.SIMULATION_SEED) == (200_000, 20261127)
    assert round(3084 / 5182, 6) == ev.VRS_FAVORITE_P


def test_reference_probabilities():
    refs = ev.reference_prob_fns({"A": 1500.0, "B": 1400.0, "C": 1400.0})
    assert refs["50%"]("A", "B", 3) == 0.5
    assert refs["maior VRS fixo"]("A", "B", 1) == 0.595137
    assert refs["maior VRS fixo"]("B", "A", 3) == pytest.approx(1 - 0.595137)
    with pytest.raises(ValueError, match="iguais"):
        refs["maior VRS fixo"]("B", "C", 1)


def test_comparisons_use_paired_differences():
    loss = np.array([0.2, 0.4, 0.9, 0.5])
    table = pd.DataFrame(
        {
            f"log_loss {ev.MODEL}": loss, f"brier {ev.MODEL}": loss / 2,
            "log_loss 50%": math.log(2), "brier 50%": 0.25,
            "log_loss maior VRS fixo": loss + 0.1, "brier maior VRS fixo": loss / 2 + 0.05,
        }
    )  # fmt: skip
    coin, vrs = ev.comparisons(table)
    d = loss - math.log(2)
    assert coin["log_loss"] == pytest.approx(d.mean())
    assert coin["erro_padrao"] == pytest.approx(d.std(ddof=1) / 2)
    assert coin["leitura"] == ev.label(d.mean(), d.std(ddof=1) / 2)
    # Diferença constante: erro padrão zero, IC degenerado.
    assert vrs["erro_padrao"] == pytest.approx(0.0, abs=1e-12)
    assert vrs["log_loss_ic"] == pytest.approx([-0.1, -0.1])
    assert vrs["leitura"] == ev.BETTER
    assert ev.comparisons(table) == [coin, vrs]  # semente fixa


def test_zero_probability_record_uses_half_a_simulation():
    surprise = ev.surprise_table(np.array([[0.0, 0.5]]), 1000)
    assert surprise[0, 0] == pytest.approx(math.log(2000))
    assert surprise[0, 1] == pytest.approx(math.log(2))


def test_consistency_simulator_matches_the_engine_simulator():
    base = DEFAULT_FORMAT.stage_state(2, NAMES)
    table = probability_table(seed_strength_prob_fn(NAMES), base.names)
    wins, losses, rounds = ev.play_tournaments(table, base, 500, np.random.default_rng(5))
    w2, l2, _ = simulate_chunk(table, base, 500, np.random.default_rng(5))
    np.testing.assert_array_equal(wins, w2)
    np.testing.assert_array_equal(losses, l2)
    assert [a.shape[1] for a, *_ in rounds] == [8, 8, 8, 6, 3]
    assert [int(fmt.sum() / 500) for _, _, fmt, _ in rounds] == [0, 0, 4, 6, 3]


def evaluate(world, rows):  # noqa: F811
    csv_path = to_csv(rows, world["dir"] / "stage2.csv")
    return ev.evaluate(
        world["stage1_csv"], csv_path, world["official"], world["seeds_path"], SIMS
    )


def test_incomplete_stage_is_not_evaluated(world):  # noqa: F811
    with pytest.raises(ValueError, match="não terminou"):
        evaluate(world, rows_of(play(world["base2"], 4)))


def test_full_evaluation_and_report(world):  # noqa: F811
    data = evaluate(world, rows_of(play(world["base2"])))
    assert len(data["partidas"]) == 33 and len(data["times"]) == 16
    order = [(m["rodada"], m["seed_a"]) for m in data["partidas"]]
    assert order == sorted(order)
    assert data["por_partida"]["50%"]["log_loss"] == pytest.approx(math.log(2))
    assert data["por_partida"]["50%"]["brier"] == pytest.approx(0.25)
    assert data["cartel"][ev.MODEL] == pytest.approx(sum(t["log_score"] for t in data["times"]))
    # 50%: cartéis perto de 1/8 e 3/16.
    expected = -(4 * math.log(1 / 8) + 12 * math.log(3 / 16))
    assert data["cartel"]["50%"] == pytest.approx(expected, rel=0.03)
    assert sum(t["avancou"] for t in data["times"]) == 8
    checks = {(c["metrica"], c["contra"]): c for c in data["consistencia"]}
    assert len(checks) == 9
    for c in checks.values():
        assert c["q2_5"] <= c["q97_5"] and 0 <= c["percentil"] <= 1
    # Em 50% a métrica é constante em qualquer torneio simulado.
    own = checks[("log_loss", None)]
    against = checks[("log_loss", "50%")]
    assert against["observado"] == pytest.approx(own["observado"] - math.log(2))
    assert against["percentil"] == pytest.approx(own["percentil"])
    header = {
        "gerado_em": "x", "commit": "abc", "sujo": False, "integridade": "ok",
        "csv_sha256": "h", "wiki": "-", "atualizacoes": [],
    }  # fmt: skip
    text = ev.report(data, header)
    assert "## 5. Leitura (emenda 3)" in text and "33 de 33" in text
    assert any(label in text for label in (ev.BETTER, ev.WORSE, ev.INCONCLUSIVE))


def test_model_probability_is_the_mean_of_the_official_variants(world):  # noqa: F811
    from sim.live import official_model

    data = evaluate(world, rows_of(play(world["base2"])))
    model = official_model(world["seeds"], world["official"])
    for m in data["partidas"]:
        a, b, fmt = m["time_a"], m["time_b"], m["best_of"]
        mean = np.mean([f(a, b, fmt) for f in model.prob_fns])
        assert m[f"p {ev.MODEL}"] == pytest.approx(mean)


def test_report_is_not_overwritten_without_force(tmp_path, capsys):
    path = tmp_path / "r.md"
    path.write_text("anotações", encoding="utf-8")
    assert ev.main(["--report", str(path)]) == 1
    assert path.read_text(encoding="utf-8") == "anotações"
    assert "--force" in capsys.readouterr().out


def test_official_folder_matches_its_commit():
    assert ev.official_integrity() == "idêntica ao commit"
