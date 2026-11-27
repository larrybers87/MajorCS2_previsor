"""Anexo de sensibilidade D25. NÃO é a previsão oficial.

Protocolo: ``docs/anexo_d25_protocolo.md`` e ``docs/anexo_d25_emenda_01.md``.

Uso (mesmas entradas de ``predict_stage2``)::

    python -m sim.anexo_d25 --stage1 data/manual/stage1_results.csv --official <pasta oficial>
    python -m sim.anexo_d25 --conditioned --official <pasta oficial>

Reduz os pontos VRS de FUT e de Astralis, cada um separadamente (grade 3x3), só nas
probabilidades de partida; os seeds não mudam. O cenário (0, 0) precisa reproduzir a
previsão oficial.
"""

from __future__ import annotations

import argparse
import itertools
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.h10_format import PARAMS_PATH
from ingest.seeds import SEEDS_PATH, load_seeds
from swiss import current_round, simulate_stage

from .chain import simulate_chained
from .common import (
    MANUAL_DIR,
    PREDICTIONS_DIR,
    b0_from,
    freeze_inputs,
    load_stage2_model,
    markdown_table,
    new_output_dir,
    percent,
    run_metadata,
    write_csv,
    write_json,
    write_text,
)
from .format_config import DEFAULT_FORMAT
from .predict_stage2 import RECORD_COLUMNS, _load_stage, _mean_prob_fn, _record_frame
from .results import file_sha256
from .stages import entrants_by_seed, stage2_names

ADJUSTED_TEAMS = ("FUT", "Astralis")
DELTAS = (0, -50, -100)  # valores ARBITRÁRIOS, pré-registrados
SCENARIOS = tuple(itertools.product(DELTAS, DELTAS))  # (delta FUT, delta Astralis)
DELTA_COLUMNS = ["delta_fut", "delta_astralis"]
TOLERANCE = 1.5e-6  # as saídas oficiais têm 6 casas


def adjusted_seeds(seeds: pd.DataFrame, deltas: Mapping[str, int]) -> pd.DataFrame:
    """Cópia dos seeds com os pontos VRS alterados; as colunas de seed não mudam."""
    out = seeds.copy()
    for team, delta in deltas.items():
        chosen = out["name"] == team
        if chosen.sum() != 1:
            raise ValueError(f"time {team!r} não encontrado nos seeds")
        out.loc[chosen, "vrs_points"] = out.loc[chosen, "vrs_points"] + delta
    return out


def compare_with_official(table: pd.DataFrame, folder: Path) -> float:
    """Maior diferença entre o cenário (0, 0) e ``probabilities.csv`` da pasta oficial."""
    official = pd.read_csv(folder / "probabilities.csv").set_index("time")
    baseline = table[(table["delta_fut"] == 0) & (table["delta_astralis"] == 0)]
    baseline = baseline.set_index("time")
    if set(official.index) != set(baseline.index):
        raise ValueError("a pasta oficial tem outro conjunto de times (modo diferente?)")
    columns = [*RECORD_COLUMNS, "P(avançar)"]
    difference = (baseline.loc[official.index, columns] - official[columns]).abs()
    return float(difference.to_numpy().max())


def _grid(table: pd.DataFrame, team: str) -> list[str]:
    """P(avançar) de ``team`` nas nove combinações."""
    own = table[table["time"] == team].set_index(DELTA_COLUMNS)["P(avançar)"]
    return markdown_table(
        ["FUT \\ Astralis", *[f"{d} pts" for d in DELTAS]],
        [[f"{f} pts", *[percent(own[(f, a)]) for a in DELTAS]] for f in DELTAS],
    )


def _summary(table, match_table, complete: bool, args, check) -> list[str]:
    advance = table.pivot_table(index="time", columns=DELTA_COLUMNS, values="P(avançar)")
    baseline = advance[(0, 0)]
    others = [t for t in baseline.sort_values(ascending=False).index
              if baseline[t] > 0 and t not in ADJUSTED_TEAMS]  # fmt: skip
    # Abertura: depende só da redução do próprio time (não há FUT x Astralis na rodada 1).
    own_delta = np.where(match_table["time"] == "FUT", match_table["delta_fut"],
                         match_table["delta_astralis"])  # fmt: skip
    other_delta = np.where(match_table["time"] == "FUT", match_table["delta_astralis"],
                           match_table["delta_fut"])  # fmt: skip
    opening = match_table.assign(pontos=own_delta)[other_delta == 0]
    top = opening.groupby(["time", "pontos"], sort=False).head(3)
    return [
        "# Anexo D25: sensibilidade aos substitutos de FUT e Astralis",
        "",
        "**Não é a previsão oficial.** Os valores -50 e -100 pontos VRS são **arbitrários**: "
        "não foram estimados e não medem o efeito real de um substituto. Os seeds não mudam.",
        "",
        "Modo: " + ("Stage 1 completo." if complete else "condicionado (Stage 1 incompleto).")
        + f" Grade 3x3; {args.sims} simulações por cenário e extremo de w.",
        "",
        (
            f"Cenário (0, 0) conferido com `{args.official.name}`: maior diferença {check:.7f}."
            if check is not None
            else "Cenário (0, 0) NÃO conferido com uma previsão oficial (sem `--official`)."
        ),
        "",
        "## P(avançar) de FUT",
        "",
        *_grid(table, "FUT"),
        "",
        "## P(avançar) de Astralis",
        "",
        *_grid(table, "Astralis"),
        "",
        "## Demais times: manchete (0, 0) e faixa nos nove cenários",
        "",
        *markdown_table(
            ["Time", "(0, 0)", "menor", "maior"],
            [[t, percent(baseline[t]), percent(advance.loc[t].min()),
              percent(advance.loc[t].max())] for t in others],  # fmt: skip
        ),
        "",
        "## Abertura (redução do próprio time; três confrontos mais prováveis)",
        "",
        *markdown_table(
            ["Time", "Pts", "Adversário", "Formato", "P(confronto)", "P(vence)"],
            [
                [r.time, r.pontos, r.adversario, f"Bo{r.best_of}",
                 percent(r["P(confronto)"]), percent(r["P(time vence)"])]  # fmt: skip
                for _, r in top.iterrows()
            ],
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Anexo de sensibilidade D25 (substitutos)")
    cli.add_argument("--stage1", type=Path)
    cli.add_argument("--stage2", type=Path, help="só confrontos anunciados, se a oficial usar")
    cli.add_argument("--conditioned", action="store_true")
    cli.add_argument("--official", type=Path, help="pasta da previsão oficial, para conferir")
    cli.add_argument("--sims", type=int, default=200_000)
    cli.add_argument("--seed", type=int, default=20261127)
    cli.add_argument("--seeds-file", type=Path, default=SEEDS_PATH)
    cli.add_argument("--params-file", type=Path, default=PARAMS_PATH)
    cli.add_argument("--out", type=Path, default=PREDICTIONS_DIR / "anexo_d25")
    args = cli.parse_args(argv)

    stage1_path = args.stage1
    default_stage1 = MANUAL_DIR / "stage1_results.csv"
    if stage1_path is None and default_stage1.exists():
        stage1_path = default_stage1

    try:
        seeds = load_seeds(args.seeds_file)
        model = load_stage2_model(args.params_file)
        notes: list[str] = []
        base1 = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1))
        stage1, _ = _load_stage(stage1_path, base1, notes, "Stage 1")
        complete = current_round(stage1) is None
        if not complete and not args.conditioned:
            cli.error("Stage 1 incompleto; complete o CSV ou use --conditioned")
        stage2 = None
        if complete:
            base2 = DEFAULT_FORMAT.stage_state(2, stage2_names(seeds, stage1))
            stage2, rows2 = _load_stage(args.stage2, base2, notes, "Stage 2")
            if any(r.winner is not None for r in rows2):
                cli.error("o anexo é pré-jogo: o CSV do Stage 2 não pode ter resultados")
        elif args.stage2:
            cli.error("o CSV do Stage 2 exige o Stage 1 completo")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1

    invited = entrants_by_seed(seeds, 2)
    tables, matches = [], []
    for deltas in SCENARIOS:
        by_team = dict(zip(ADJUSTED_TEAMS, deltas))
        scenario = adjusted_seeds(seeds, by_team)
        prob_fns = [
            b0_from(scenario, v["beta"], model["transform"]).prob_fn() for v in model["variants"]
        ]
        prob_fn = _mean_prob_fn(prob_fns)
        if complete:
            results = [
                simulate_stage(f, stage2, args.sims, np.random.default_rng(args.seed))
                for f in prob_fns
            ]
            opponents = dict(zip(stage2.names[:8], stage2.names[8:]))
            listed = stage2.round_matches(1)
            if listed:  # confrontos oficiais anunciados prevalecem
                opponents = {}
                for m in listed:
                    opponents[m.team_a], opponents[m.team_b] = m.team_b, m.team_a
            openings = [(team, opponents[team], 1.0) for team in ADJUSTED_TEAMS]
        else:
            results = [
                simulate_chained(f, stage1, invited, args.sims, np.random.default_rng(args.seed))
                for f in prob_fns
            ]
            counts = np.mean([r.opening_counts / args.sims for r in results], axis=0)
            openings = [
                (team, results[0].teams[j], float(counts[invited.index(team), j]))
                for team in ADJUSTED_TEAMS
                for j in np.argsort(-counts[invited.index(team)], kind="stable")
                if counts[invited.index(team), j] > 0
            ]
        mean = np.mean([r.record_counts / args.sims for r in results], axis=0)
        table = _record_frame(results[0].teams, mean, scenario)
        if not complete:
            table["P(participa)"] = np.mean(
                [r.participation_counts / args.sims for r in results], axis=0
            )
        for position, (column, delta) in enumerate(zip(DELTA_COLUMNS, deltas), start=1):
            table.insert(position, column, delta)
        tables.append(table)
        bo = 3 if (complete and stage2.all_best_of_three) else 1
        matches += [
            {
                **dict(zip(DELTA_COLUMNS, deltas)),
                "time": team,
                "adversario": opponent,
                "P(confronto)": share,
                "best_of": bo,
                "P(time vence)": prob_fn(team, opponent, bo),
            }
            for team, opponent, share in openings
        ]
    table = pd.concat(tables, ignore_index=True)
    match_table = pd.DataFrame(matches)

    check = None
    if args.official:
        try:
            check = compare_with_official(table, args.official)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            print(f"ERRO ao comparar com a oficial: {exc}")
            return 1
        if check > TOLERANCE:
            print(f"ERRO: o cenário (0, 0) difere da previsão oficial em até {check:.6f}")
            return 1

    lines = _summary(table, match_table, complete, args, check)
    metadata = run_metadata() | {
        "kind": "anexo_d25",
        "official": False,
        "amendment": 1,
        "deltas": list(DELTAS),
        "scenarios": [list(s) for s in SCENARIOS],
        "teams": list(ADJUSTED_TEAMS),
        "n_sims": args.sims,
        "rng_seed": args.seed,
        "variants": model["variants"],
        "conditioned": not complete,
        "stage1_csv_sha256": file_sha256(stage1_path) if stage1_path else None,
        "stage2_csv_sha256": file_sha256(args.stage2) if args.stage2 else None,
        "checked_against": args.official.name if args.official else None,
        "check_max_difference": check,
        "rule_notes": notes,
    }
    if notes:
        lines += ["", "## Divergências entre o CSV e as regras", "", *[f"- {n}" for n in notes]]
    out = new_output_dir(args.out, metadata)
    metadata |= freeze_inputs(out, args.seeds_file, args.params_file)
    write_csv(out / "scenarios.csv", table)
    write_csv(out / "matches.csv", match_table)
    write_text(out / "summary.md", "\n".join(lines) + "\n")
    write_json(out / "meta.json", metadata)
    print("\n".join(lines))
    print(f"\nGravado em {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
