"""Checagem de desastre do Stage 3 (pré-registro, emendas 1 e 2).

Uso, depois do fim do Stage 2 e antes do primeiro jogo do Stage 3::

    python -m sim.stage3_check

Partidas dos Stages 1 e 2 juntas; cada probabilidade usa só rodadas anteriores. Volta ao
B0 puro somente se (a) a média 50/50 for pior que o 50% com significância unilateral de
95% **e** (b) o B1 for pior que o B0. Calculada **uma vez**: recusa se já houver uma pasta
em ``predictions/stage3/disaster_check/``. Não faz commit.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.b1_selection import PARAMS_PATH as B1_PARAMS_PATH
from backtest.metrics import log_loss_each
from ingest.seeds import SEEDS_PATH, load_seeds
from ingest.vrs_matches import MATCHES_PATH
from swiss import StageState, best_of, records

from .common import (
    MANUAL_DIR,
    PREDICTIONS_DIR,
    markdown_table,
    new_output_dir,
    percent,
    run_metadata,
    write_csv,
    write_json,
    write_text,
)
from .results import ResultRow, file_sha256
from .stage3_model import (
    MODELS,
    assert_frozen_b1_code,
    b1_ratings_at,
    load_b1_config,
    load_stages,
    prob_fns,
    vrs_points,
)

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20261202
CHECK_DIR = PREDICTIONS_DIR / "stage3" / "disaster_check"

BACK_TO_B0 = "voltar_ao_b0"
BOTH_FAILED = "falha_dos_dois"
KEEP = "manter_media"
CONSEQUENCES = {
    BACK_TO_B0: "voltar ao **B0 puro**",
    BOTH_FAILED: "**falha dos dois modelos**: relatar e não trocar nada (média 50/50)",
    KEEP: "**manter a média 50/50**",
}


def check_table(
    seeds: pd.DataFrame,
    matches: pd.DataFrame,
    config,
    stages: Sequence[tuple[int, StageState, Sequence[ResultRow]]],
) -> pd.DataFrame:
    """Uma linha por partida, ordenada por stage, rodada e melhor seed inicial."""
    points = vrs_points(seeds)
    all_rows = {number: list(rows) for number, _, rows in stages}
    out = []
    for number, state, rows in stages:
        seed = {team.name: team.seed for team in state.teams}
        for round_number in sorted({r.round for r in rows}):
            # D33: rodadas anteriores (e stages anteriores); nada da própria rodada.
            previous = {
                s: [r for r in all_rows[s] if s < number or r.round < round_number]
                for s in all_rows
                if s <= number
            }
            fns = prob_fns(points, b1_ratings_at(matches, seeds, config, previous))
            current = records(state.before_round(round_number))
            for row in (r for r in rows if r.round == round_number and r.winner):
                a, b = sorted((row.team_a, row.team_b), key=seed.__getitem__)
                fmt = row.best_of or best_of(*current[a], state.all_best_of_three)
                entry = {
                    "stage": number, "rodada": round_number, "seed_a": seed[a],
                    "time_a": a, "time_b": b, "best_of": fmt, "vencedor": row.winner,
                }  # fmt: skip
                for (model, w), fn in fns.items():
                    entry[f"p_{model}_w{w:g}"] = fn(a, b, fmt)
                for model in MODELS:
                    entry[f"p_{model}"] = (entry[f"p_{model}_w0"] + entry[f"p_{model}_w1"]) / 2
                entry["p_media"] = (entry["p_B0"] + entry["p_B1"]) / 2
                for name in (*MODELS, "media"):
                    entry[f"log_loss_{name}"] = float(
                        log_loss_each(entry[f"p_{name}"], row.winner == a)
                    )
                out.append(entry)
    table = pd.DataFrame(out)
    return table.sort_values(["stage", "rodada", "seed_a"], ignore_index=True)


def decide(table: pd.DataFrame) -> dict:
    """Aplica a emenda 1 à tabela (já na ordem fixada pela emenda 2)."""
    d = table["log_loss_media"].to_numpy() - np.log(2)
    n = len(d)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = d[rng.integers(0, n, size=(BOOTSTRAP_REPS, n))].mean(axis=1)
    low = float(np.quantile(means, 0.05))
    worse_than_coin = low > 0
    b1_minus_b0 = float(table["log_loss_B1"].mean() - table["log_loss_B0"].mean())
    b1_worse = b1_minus_b0 > 0
    if worse_than_coin:
        decision = BACK_TO_B0 if b1_worse else BOTH_FAILED
    else:
        decision = KEEP
    return {
        "n": n,
        "log_loss": {m: float(table[f"log_loss_{m}"].mean()) for m in (*MODELS, "media")},
        "a_media_menos_ln2": float(d.mean()),
        "a_quantil_5": low,
        "a_vale": bool(worse_than_coin),
        "b_b1_menos_b0": b1_minus_b0,
        "b_vale": bool(b1_worse),
        "decisao": decision,
        "modelos": ["B0"] if decision == BACK_TO_B0 else list(MODELS),
    }


def summary(result: dict, table: pd.DataFrame, metadata: dict) -> str:
    yes = {True: "sim", False: "não"}
    losses = result["log_loss"]
    lines = [
        "# Checagem de desastre do Stage 3",
        "",
        f"Gerada em {metadata['generated_at_utc']} (UTC). Regras: pré-registro e emendas 1 e "
        "2. Parte das partidas (Stage 1) já era conhecida antes: não é teste prospectivo "
        "para elas.",
        "",
        f"Partidas: {result['n']}. log loss: média 50/50 {losses['media']:.4f}; B0 "
        f"{losses['B0']:.4f}; B1 {losses['B1']:.4f}; 50% {np.log(2):.4f}.",
        "",
        *markdown_table(
            ["Condição", "Valor", "Vale?"],
            [
                [
                    "(a) média − ln 2 > 0 no quantil de 5% (10.000 réplicas, semente 20261202)",
                    f"média {result['a_media_menos_ln2']:+.4f}; quantil "
                    f"{result['a_quantil_5']:+.4f}",
                    yes[result["a_vale"]],
                ],
                [
                    "(b) B1 − B0 > 0", f"{result['b_b1_menos_b0']:+.4f}",
                    yes[result["b_vale"]],
                ],
            ],  # fmt: skip
        ),
        "",
        f"**Resultado:** {CONSEQUENCES[result['decisao']]}.",
        "",
        "## Partidas",
        "",
        *markdown_table(
            ["Stage", "R", "Partida", "Bo", "B0", "B1", "Média", "Vencedor"],
            [
                [
                    r["stage"], r["rodada"], f"{r['time_a']} x {r['time_b']}", r["best_of"],
                    percent(r["p_B0"]), percent(r["p_B1"]), percent(r["p_media"]), r["vencedor"],
                ]
                for r in table.to_dict("records")
            ],  # fmt: skip
        ),
        "",
    ]
    return "\n".join(lines)


def input_hashes(args) -> dict:
    return {
        "stage1_csv_sha256": file_sha256(args.stage1),
        "stage2_csv_sha256": file_sha256(args.stage2),
        "matches_file_sha256": file_sha256(args.matches_file),
        "seeds_file_sha256": file_sha256(args.seeds_file),
        "b1_params_sha256": file_sha256(args.b1_params_file),
    }


def add_input_arguments(cli: argparse.ArgumentParser) -> None:
    cli.add_argument("--stage1", type=Path, default=MANUAL_DIR / "stage1_results.csv")
    cli.add_argument("--stage2", type=Path, default=MANUAL_DIR / "stage2_results.csv")
    cli.add_argument("--matches-file", type=Path, default=MATCHES_PATH)
    cli.add_argument("--seeds-file", type=Path, default=SEEDS_PATH)
    cli.add_argument("--b1-params-file", type=Path, default=B1_PARAMS_PATH)


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Checagem de desastre do Stage 3")
    add_input_arguments(cli)
    cli.add_argument("--out", type=Path, default=CHECK_DIR)
    args = cli.parse_args(argv)
    if args.out.exists() and any(args.out.iterdir()):
        print(
            f"ERRO: já existe uma checagem em {args.out}; ela é calculada uma única vez. "
            "Se uma entrada estava errada, registre o motivo em docs/ antes de refazer."
        )
        return 1
    try:
        assert_frozen_b1_code()
        config = load_b1_config(args.b1_params_file)
        seeds = load_seeds(args.seeds_file)
        stage1, rows1, stage2, rows2 = load_stages(seeds, args.stage1, args.stage2)
        table = check_table(
            seeds, pd.read_parquet(args.matches_file), config,
            [(1, stage1, rows1), (2, stage2, rows2)],
        )  # fmt: skip
        hashes = input_hashes(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1
    result = decide(table)
    metadata = run_metadata() | {"kind": "checagem_de_desastre"} | hashes | {"resultado": result}
    out = new_output_dir(args.out, metadata)
    write_csv(out / "matches.csv", table)
    text = summary(result, table, metadata)
    write_text(out / "summary.md", text)
    write_json(out / "check.json", metadata)
    print(text.split("## Partidas")[0])
    print(f"Gravado em {out}")
    print("Nada foi commitado. Resultado e decisão têm de ir em commit antes do Stage 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
