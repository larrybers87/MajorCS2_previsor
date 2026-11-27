"""Ratings do B1 para os times do Major, atualizados com os resultados já jogados.

Uso::

    python -m sim.b1_ratings --stage1 data/manual/stage1_results.csv [--stage2 ...]

NÃO é o modelo do Stage 2 (o B1 não foi adotado); fica pronto para o Stage 3.
Nenhum hiperparâmetro é ajustado aqui: vêm de ``backtest.b1_selection``.
Grava ``data/processed/b1_major_ratings.csv``.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping, Sequence
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from backtest.b1_selection import PARAMS_PATH, prepare
from ingest.seeds import SEEDS_PATH, load_seeds
from ingest.vrs import PROJECT_ROOT
from ingest.vrs_matches import MATCHES_PATH
from models.b0 import logistic
from models.ratings import EloConfig, Game, GlickoConfig, Side, build_system
from swiss.probability import series_probability

from .common import load_params
from .results import ResultRow, read_results
from .singapore2026 import ROSTERS

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "b1_major_ratings.csv"
# Datas de início segundo a imprensa (não verificadas). Só importam em configurações com
# decaimento ou RD que cresce no tempo; a rodada r é tratada como o dia r do stage.
STAGE_START = {1: date(2026, 11, 24), 2: date(2026, 11, 28), 3: date(2026, 12, 2)}


def config_from(chosen: Mapping) -> EloConfig | GlickoConfig:
    values = {k: v for k, v in chosen.items() if k != "kind"}
    kind = {"EloConfig": EloConfig, "GlickoConfig": GlickoConfig}[chosen["kind"]]
    return kind(**values)


def major_ratings(
    matches: pd.DataFrame,
    seeds: pd.DataFrame,
    config: EloConfig | GlickoConfig,
    stages: Mapping[int, Sequence[ResultRow]],
) -> pd.DataFrame:
    """Rating de cada participante antes do Major e depois dos resultados informados."""
    data, days, registry = prepare(matches)
    system = build_system(config)
    for day, _, games in days:
        system.process_day(day, games)

    sides: dict[str, Side] = {}
    for row in seeds.itertuples():
        roster = frozenset(p.casefold() for p in ROSTERS[row.name])
        team = registry.resolve(row.vrs_name, roster)
        sides[row.name] = Side(team, float(row.vrs_points))
    if len({s.team for s in sides.values()}) != len(sides):
        raise ValueError("dois participantes foram ligados ao mesmo time do histórico")
    first_day = STAGE_START[1]
    before = {name: system.rating(side, first_day) for name, side in sides.items()}
    games_played = dict.fromkeys(sides, 0)
    last_day = first_day
    for stage in sorted(stages):
        decided = [r for r in stages[stage] if r.winner is not None]
        for round_number in sorted({r.round for r in decided}):
            last_day = STAGE_START[stage] + timedelta(days=round_number - 1)
            batch = [r for r in decided if r.round == round_number]
            system.process_day(
                last_day,
                [Game(sides[r.team_a], sides[r.team_b], r.winner == r.team_a) for r in batch],
            )
            for r in batch:
                games_played[r.team_a] += 1
                games_played[r.team_b] += 1

    next_day = last_day + timedelta(days=1)
    rows = [
        {
            "time": name,
            "vrs_pontos": side.points,
            "b1_pre_evento": before[name],
            "b1_atual": system.rating(side, next_day),
            "partidas_no_major": games_played[name],
        }
        for name, side in sides.items()
    ]
    return pd.DataFrame(rows).sort_values("b1_atual", ascending=False, ignore_index=True)


def b1_prob_fn(ratings: Mapping[str, float], beta: float) -> Callable[[str, str, int], float]:
    """Interface de ``swiss.simulate_stage`` para o B1 (probabilidades fixas no stage)."""

    def prob_fn(team_a: str, team_b: str, best_of: int) -> float:
        p_map = float(logistic(beta * (ratings[team_a] - ratings[team_b]) / 100.0))
        return float(series_probability(p_map, best_of))

    return prob_fn


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Ratings B1 dos times do Major")
    cli.add_argument("--stage1", type=Path)
    cli.add_argument("--stage2", type=Path)
    cli.add_argument("--matches-file", type=Path, default=MATCHES_PATH)
    cli.add_argument("--seeds-file", type=Path, default=SEEDS_PATH)
    cli.add_argument("--params-file", type=Path, default=PARAMS_PATH)
    cli.add_argument("--out", type=Path, default=OUTPUT_PATH)
    args = cli.parse_args(argv)
    try:
        params = load_params(args.params_file)
        stages = {
            number: read_results(path)
            for number, path in ((1, args.stage1), (2, args.stage2))
            if path is not None
        }
        table = major_ratings(
            pd.read_parquet(args.matches_file),
            load_seeds(args.seeds_file),
            config_from(params["chosen"]),
            stages,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False, encoding="utf-8")
    print(f"Configuração: {json.dumps(params['chosen'])}; beta = {params['final_beta']:.4f}")
    print(table.to_string(index=False, float_format="%.1f"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
