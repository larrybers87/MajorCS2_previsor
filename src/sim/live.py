"""Estado de um stage ao vivo: resultados reais, escolhas do usuário e visão para o site.

Os emparelhamentos sempre vêm da engine (``swiss.pair_round``) ou, quando o CSV já traz
o confronto anunciado, do próprio CSV. O modelo do Stage 2 é o B0 da previsão oficial,
lido da pasta congelada.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from swiss import Match, ProbFn, StageState, advancing_teams, current_round, pair_round, records
from swiss.rules import FINAL_RECORD_LABELS, MATCHES_PER_ROUND

from .common import b0_from, load_stage2_model
from .official import OFFICIAL_DIR
from .results import ResultRow


@dataclass(frozen=True)
class Pick:
    """Vencedor escolhido pelo usuário para uma partida ainda não jogada."""

    round: int
    team_a: str
    team_b: str
    winner: str


@dataclass(frozen=True)
class OfficialModel:
    """B0 da previsão oficial: média de w=0 e w=1."""

    variants: tuple[Mapping, ...]
    prob_fns: tuple[ProbFn, ...]
    meta: Mapping
    probabilities: pd.DataFrame

    def prob_fn(self, team_a: str, team_b: str, best_of: int) -> float:
        return float(np.mean([f(team_a, team_b, best_of) for f in self.prob_fns]))


def official_model(seeds: pd.DataFrame, folder: Path = OFFICIAL_DIR) -> OfficialModel:
    """Carrega o modelo da pasta oficial e confere os pontos VRS dos 16 times."""
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    model = load_stage2_model(folder / "model_params.json")
    table = pd.read_csv(folder / "probabilities.csv")
    points = dict(zip(seeds["name"], seeds["vrs_points"]))
    different = [
        r.time for r in table.itertuples() if int(points.get(r.time, -1)) != int(r.vrs_pontos)
    ]
    if different:
        raise ValueError(f"pontos VRS diferentes dos da previsão oficial: {different}")
    fns = tuple(
        b0_from(seeds, v["beta"], model["transform"]).prob_fn() for v in model["variants"]
    )
    return OfficialModel(tuple(model["variants"]), fns, meta, table)


def full_round(state: StageState) -> list[Match]:
    """Partidas da rodada atual: as registradas mais as que a engine completa."""
    number = current_round(state)
    if number is None:
        return []
    listed = list(state.round_matches(number))
    if len(listed) == MATCHES_PER_ROUND[number - 1]:
        return listed
    expected = pair_round(state)
    outside = {m.pair for m in listed} - {p.pair for p in expected}
    if outside:
        text = ", ".join(sorted(" x ".join(sorted(p)) for p in outside))
        raise ValueError(
            f"rodada {number}: confrontos diferentes dos da engine ({text}); liste no CSV "
            "a rodada inteira, com o placar vazio nas partidas pendentes"
        )
    present = {m.pair for m in listed}
    return listed + [
        Match(number, p.team_a, p.team_b) for p in expected if p.pair not in present
    ]


def apply_picks(real: StageState, picks: Sequence[Pick]) -> tuple[StageState, set, list[Pick]]:
    """Avança o stage com as escolhas; os resultados reais nunca são sobrescritos.

    Devolve o estado (com a rodada seguinte já emparelhada), as chaves
    ``(rodada, par)`` decididas por escolha e as escolhas que não couberam na chave
    (por exemplo, depois de mudar uma escolha anterior).
    """
    pending = {(p.round, frozenset((p.team_a, p.team_b))): p for p in picks}
    chosen: set = set()
    state = real
    while (number := current_round(state)) is not None:
        matches = []
        for match in full_round(state):
            key = (number, match.pair)
            pick = pending.get(key)
            if match.winner is None and pick is not None and pick.winner in match.pair:
                match = Match(number, match.team_a, match.team_b, pick.winner)
                chosen.add(key)
                del pending[key]
            matches.append(match)
        others = tuple(m for m in state.matches if m.round != number)
        state = state.with_matches((*others, *matches))
        if any(m.winner is None for m in matches):
            break
    return state, chosen, list(pending.values())


def stage_view(
    state: StageState,
    rows: Sequence[ResultRow] = (),
    prob_fn: ProbFn | None = None,
    chosen: set | frozenset = frozenset(),
) -> dict:
    """Chave pronta para o site. Em cada partida, ``a`` é o melhor seed inicial."""
    seed = {team.name: team.seed for team in state.teams}
    scores = {
        (r.round, frozenset((r.team_a, r.team_b))): {r.team_a: r.score_a, r.team_b: r.score_b}
        for r in rows
        if r.winner is not None
    }
    rounds = []
    for number in sorted({m.round for m in state.matches}):
        before = records(state.before_round(number))
        matches = []
        for match in state.round_matches(number):
            a, b = sorted(match.pair, key=seed.__getitem__)
            key = (number, match.pair)
            wins, losses = before[a]
            fmt = 3 if state.all_best_of_three or wins == 2 or losses == 2 else 1
            origin = "pendente"
            if match.winner is not None:
                origin = "escolha" if key in chosen else "real"
            score = scores.get(key, {}) if origin == "real" else {}
            entry = {
                "rodada": number, "a": a, "b": b, "cartel": [wins, losses], "bo": fmt,
                "placar_a": score.get(a), "placar_b": score.get(b),
                "vencedor": match.winner, "origem": origin,
            }  # fmt: skip
            if prob_fn is not None:
                entry["p_a"] = float(prob_fn(a, b, fmt))
            matches.append(entry)
        matches.sort(key=lambda m: (-m["cartel"][0], m["cartel"][1], seed[m["a"]]))
        rounds.append(matches)
    final = records(state)
    finals = {
        label: [n for n in state.names if "{}-{}".format(*final[n]) == label]
        for label in FINAL_RECORD_LABELS
    }
    complete = current_round(state) is None
    return {
        "rodadas": rounds,
        "finais": finals,
        "completo": complete,
        "classificados": advancing_teams(state) if complete else None,
    }
