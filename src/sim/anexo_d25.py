"""Anexo de sensibilidade D25 (``docs/anexo_d25_protocolo.md``). NÃO é a previsão oficial.

Uso (mesmas entradas de ``predict_stage2``)::

    python -m sim.anexo_d25 --stage1 data/manual/stage1_results.csv --official <pasta oficial>
    python -m sim.anexo_d25 --conditioned --official <pasta oficial>

Reduz os pontos VRS de FUT e Astralis só nas probabilidades de partida; os seeds não
mudam. O cenário 0 precisa reproduzir a previsão oficial.
"""

from __future__ import annotations

import argparse
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
TOLERANCE = 1.5e-6  # as saídas oficiais têm 6 casas


def adjusted_seeds(seeds: pd.DataFrame, delta: int) -> pd.DataFrame:
    """Cópia dos seeds com os pontos VRS alterados; as colunas de seed não mudam."""
    out = seeds.copy()
    chosen = out["name"].isin(ADJUSTED_TEAMS)
    if chosen.sum() != len(ADJUSTED_TEAMS):
        raise ValueError(f"times {ADJUSTED_TEAMS} não encontrados nos seeds")
    out.loc[chosen, "vrs_points"] = out.loc[chosen, "vrs_points"] + delta
    return out


def compare_with_official(table: pd.DataFrame, folder: Path) -> float:
    """Maior diferença entre o cenário 0 e ``probabilities.csv`` da pasta oficial."""
    official = pd.read_csv(folder / "probabilities.csv").set_index("time")
    baseline = table[table["delta"] == 0].set_index("time")
    if set(official.index) != set(baseline.index):
        raise ValueError("a pasta oficial tem outro conjunto de times (modo diferente?)")
    columns = [*RECORD_COLUMNS, "P(avançar)"]
    difference = (baseline.loc[official.index, columns] - official[columns]).abs()
    return float(difference.to_numpy().max())


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
    for delta in DELTAS:
        scenario = adjusted_seeds(seeds, delta)
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
        table.insert(1, "delta", delta)
        tables.append(table)
        bo = 3 if (complete and stage2.all_best_of_three) else 1
        matches += [
            {
                "delta": delta,
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
            print(f"ERRO: o cenário 0 difere da previsão oficial em até {check:.6f}")
            return 1

    advance = table.pivot(index="time", columns="delta", values="P(avançar)")
    advance = advance.sort_values(0, ascending=False)
    advance = advance[advance[0] > 0]
    lines = [
        "# Anexo D25: sensibilidade aos substitutos de FUT e Astralis",
        "",
        "**Não é a previsão oficial.** Os valores -50 e -100 pontos VRS são **arbitrários**: "
        "não foram estimados e não medem o efeito real de um substituto. Os seeds não mudam.",
        "",
        "Modo: " + ("Stage 1 completo." if complete else "condicionado (Stage 1 incompleto).")
        + f" Simulações: {args.sims} por extremo de w.",
        "",
        (
            f"Cenário 0 conferido com `{args.official.name}`: maior diferença {check:.6f}."
            if check is not None
            else "Cenário 0 NÃO conferido com uma previsão oficial (sem `--official`)."
        ),
        "",
        "## P(avançar no Stage 2)",
        "",
        *markdown_table(
            ["Time", *[f"{d} pts" for d in DELTAS]],
            [
                [("**" + t + "**") if t in ADJUSTED_TEAMS else t,
                 *[percent(row[d]) for d in DELTAS]]
                for t, row in advance.iterrows()
            ],  # fmt: skip
        ),
        "",
        "## Abertura de FUT e Astralis (três confrontos mais prováveis)",
        "",
        *markdown_table(
            ["Pts", "Time", "Adversário", "Formato", "P(confronto)", "P(vence)"],
            [
                [r.delta, r.time, r.adversario, f"Bo{r.best_of}",
                 percent(r["P(confronto)"]), percent(r["P(time vence)"])]  # fmt: skip
                for _, r in match_table.groupby(["delta", "time"], sort=False).head(3).iterrows()
            ],
        ),
    ]
    metadata = run_metadata() | {
        "kind": "anexo_d25",
        "official": False,
        "deltas": list(DELTAS),
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
