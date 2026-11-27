"""Stage 3, playoffs e configuração de formato (probabilidades sintéticas)."""

import numpy as np
import pandas as pd
import pytest

from sim.format_config import ACTIVE_FORMAT, ANNOUNCED, DEFAULT_FORMAT, FORMATS, RULEBOOK
from sim.playoffs import (
    PLACINGS,
    bracket,
    simulate_playoffs,
    simulate_stage3,
)
from sim.singapore2026 import ENTRANTS
from sim.stages import entrants_by_seed, stage3_names
from swiss import StageState, advancing_teams, seed_strength_prob_fn

from conftest import NAMES, random_stage

EIGHT = tuple(f"P{i}" for i in range(1, 9))


def seed_of(name: str) -> int:
    return int(name[1:])


def favorite(a, b, best_of):
    """O menor número sempre vence."""
    return 1.0 if seed_of(a) < seed_of(b) else 0.0


def coin(a, b, best_of):
    return 0.5


def pairs(matches):
    return {m.name: (m.seed_a, m.seed_b, m.best_of) for m in matches}


def win(a, b):
    return {frozenset((a, b)): a}


def test_format_flag():
    assert FORMATS[ACTIVE_FORMAT] is DEFAULT_FORMAT is ANNOUNCED
    assert ANNOUNCED.stage_state(3, NAMES).all_best_of_three
    assert not RULEBOOK.stage_state(3, NAMES).all_best_of_three
    assert (RULEBOOK.final_best_of, RULEBOOK.third_place_match) == (3, False)
    for fmt in FORMATS.values():  # Stages 1 e 2 seguem o rulebook em qualquer opção
        assert not fmt.stage_state(1, NAMES).all_best_of_three
        assert not fmt.stage_state(2, NAMES).all_best_of_three


def test_quarterfinals_follow_the_rulebook():
    assert pairs(bracket(EIGHT)) == {
        "QF1": (1, 8, 3), "QF2": (4, 5, 3), "QF3": (2, 7, 3), "QF4": (3, 6, 3),
    }  # fmt: skip


def full_results():
    """Zebras nas quartas A; favoritos no resto."""
    results = {}
    for winner, loser in (
        ("P8", "P1"), ("P4", "P5"), ("P2", "P7"), ("P3", "P6"),
        ("P4", "P8"), ("P2", "P3"), ("P8", "P3"), ("P4", "P2"),
    ):  # fmt: skip
        results |= win(winner, loser)
    return results


def test_semifinals_stay_in_their_bracket_and_losers_play_for_third():
    matches = bracket(EIGHT, full_results())
    # Sem reordenar seeds: vencedor de 1v8 contra o de 4v5, mesmo com zebra.
    assert pairs(matches)["SF1"] == (4, 8, 3)
    assert pairs(matches)["SF2"] == (2, 3, 3)
    assert pairs(matches)["3º"] == (3, 8, 3)
    assert pairs(matches)["Final"] == (2, 4, 5)
    rulebook = bracket(EIGHT, {k: v for k, v in full_results().items()
                               if k != frozenset(("P8", "P3"))}, RULEBOOK)  # fmt: skip
    assert "3º" not in pairs(rulebook) and pairs(rulebook)["Final"][2] == 3


def test_partial_bracket_and_invalid_results():
    matches = bracket(EIGHT, win("P1", "P8") | win("P5", "P4"))
    assert pairs(matches)["SF1"] == (1, 5, 3)
    assert "SF2" not in pairs(matches) and "Final" not in pairs(matches)
    with pytest.raises(ValueError, match="fora da chave"):
        bracket(EIGHT, win("P1", "P2"))
    with pytest.raises(ValueError, match="8 times"):
        bracket(EIGHT[:7])


def test_favorites_give_a_deterministic_podium_and_use_each_format():
    calls = set()

    def prob_fn(a, b, best_of):
        calls.add(best_of)
        return favorite(a, b, best_of)

    result = simulate_playoffs(prob_fn, EIGHT, 50, np.random.default_rng(0))
    p = result.placing_probabilities()
    assert (p["P1"]["campeão"], p["P2"]["vice"], p["P3"]["3º"], p["P4"]["4º"]) == (1, 1, 1, 1)
    assert all(p[t]["quartas (5º-8º)"] == 1 for t in EIGHT[4:])
    assert calls == {3, 5}


def test_final_and_third_place_use_their_own_format():
    def prob_fn(a, b, best_of):
        # Em Bo5 o pior seed vence; nos demais formatos, o melhor.
        return 1 - favorite(a, b, best_of) if best_of == 5 else favorite(a, b, best_of)

    announced = simulate_playoffs(prob_fn, EIGHT, 5, np.random.default_rng(0))
    assert announced.placing_probabilities()["P2"]["campeão"] == 1
    rulebook = simulate_playoffs(prob_fn, EIGHT, 5, np.random.default_rng(0), fmt=RULEBOOK)
    assert rulebook.placing_probabilities()["P1"]["campeão"] == 1


@pytest.mark.parametrize("fmt", [ANNOUNCED, RULEBOOK])
def test_playoff_totals(fmt):
    n = 40_000
    result = simulate_playoffs(coin, EIGHT, n, np.random.default_rng(1), fmt=fmt)
    totals = dict(zip(PLACINGS, result.placing_counts.sum(axis=0) / n))
    third = 1 if fmt.third_place_match else 0
    assert totals == {
        "campeão": 1, "vice": 1, "3º": third, "4º": third,
        "semifinal (3º-4º)": 2 * (1 - third), "quartas (5º-8º)": 4,
    }  # fmt: skip
    np.testing.assert_array_equal(result.placing_counts.sum(axis=1), n)
    for p in result.reach_probabilities().values():
        assert p["quartas"] == pytest.approx(1.0)
        assert p["semifinal"] == pytest.approx(0.5, abs=0.01)
        assert p["título"] == pytest.approx(0.125, abs=0.01)


def test_known_playoff_results_are_facts():
    n = 20_000
    result = simulate_playoffs(coin, EIGHT, n, np.random.default_rng(2), full_results())
    p = result.placing_probabilities()
    assert (p["P4"]["campeão"], p["P2"]["vice"], p["P8"]["3º"], p["P3"]["4º"]) == (1, 1, 1, 1)
    partial = simulate_playoffs(coin, EIGHT, n, np.random.default_rng(3), win("P8", "P1"))
    assert partial.reach_probabilities()["P1"]["semifinal"] == 0
    assert partial.reach_probabilities()["P8"]["semifinal"] == 1


def stage_favorite(a, b, best_of):
    return 1.0 if int(a[1:]) < int(b[1:]) else 0.0


def test_stage3_playoff_seeds_are_the_final_seeds_of_stage3():
    """Com o Stage 3 encerrado, a chave usa a ordem de ``advancing_teams``."""
    finished = random_stage(np.random.default_rng(11))
    stage3 = StageState(finished.teams, finished.matches, all_best_of_three=True)
    order = advancing_teams(stage3)
    result = simulate_stage3(stage_favorite, stage3, 3, np.random.default_rng(0))
    by_seed = simulate_playoffs(
        lambda a, b, bo: stage_favorite(a, b, bo), order, 3, np.random.default_rng(0)
    )
    expected = by_seed.reach_probabilities()
    got = result.playoffs.reach_probabilities()
    for team in order:
        assert got[team] == expected[team]
    for team in set(NAMES) - set(order):
        assert got[team]["quartas"] == 0


def test_stage3_totals():
    n = 20_000
    stage3 = DEFAULT_FORMAT.stage_state(3, NAMES)
    result = simulate_stage3(
        seed_strength_prob_fn(NAMES), stage3, n, np.random.default_rng(4), chunk_size=7_000
    )
    np.testing.assert_array_equal(result.record_counts.sum(axis=0),
                                  np.array([2, 3, 3, 3, 3, 2]) * n)  # fmt: skip
    np.testing.assert_array_equal(result.position_counts.sum(axis=0), n)
    reach = result.playoffs.reach_probabilities()
    assert sum(p["título"] for p in reach.values()) == pytest.approx(1.0)
    assert sum(p["quartas"] for p in reach.values()) == pytest.approx(8.0)
    for i, team in enumerate(NAMES):
        advanced = result.record_counts[i, :3].sum() / n
        assert reach[team]["quartas"] == pytest.approx(advanced)
    assert reach[NAMES[0]]["título"] > reach[NAMES[-1]]["título"]


def test_stage3_seeding():
    seeds = pd.DataFrame(
        {
            "name": [e.name for e in ENTRANTS],
            "stage": [e.stage for e in ENTRANTS],
            "pre_event_seed": range(1, 33),
        }
    )
    stage2 = random_stage(np.random.default_rng(13))
    names = stage3_names(seeds, stage2)
    assert names[:8] == entrants_by_seed(seeds, 3)
    assert names[8:] == advancing_teams(stage2)
