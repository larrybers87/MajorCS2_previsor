"""Previsão do Stage 3 (fase suíça), antes da primeira partida.

Uso, depois da checagem de desastre::

    python -m sim.predict_stage3

Modelo oficial: o que a checagem mandar (média 50/50 de B0 e B1, ou B0 puro), **sem
desconto**. Publica o resultado oficial e, por time, a faixa mínima-máxima de P(avançar)
na grade de sensibilidade da emenda 4 (os cenários não são gravados). Os playoffs não
são calculados: o modelo deles fica para um adendo antes de 10/12. Não faz commit.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import pandas as pd

from ingest.seeds import load_seeds
from swiss import best_of, pair_round
from swiss.rules import FINAL_RECORD_LABELS

from .common import (
    PREDICTIONS_DIR,
    markdown_table,
    new_output_dir,
    percent,
    run_metadata,
    write_csv,
    write_json,
    write_text,
)
from .format_config import ACTIVE_FORMAT, DEFAULT_FORMAT
from .stage3_check import CHECK_DIR, CONSEQUENCES, add_input_arguments, input_hashes
from .stage3_model import (
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
from .stages import stage3_names

# Não fixados no pré-registro; confirmados pelo Larry em 27/11, antes dos seeds do Stage 3.
SIMULATIONS = 200_000
RNG_SEED = 20261202


def load_check(path: Path | None, base: Path = CHECK_DIR) -> tuple[Path, dict]:
    if path is None:
        folders = sorted(p for p in base.glob("*") if (p / "check.json").exists())
        if len(folders) != 1:
            raise ValueError(
                f"esperava uma checagem de desastre em {base}, há {len(folders)}; "
                "rode antes: python -m sim.stage3_check"
            )
        path = folders[0]
    return path, json.loads((path / "check.json").read_text(encoding="utf-8"))


def sensitivity_range(
    points, ratings, models, base, simulations: int, seed: int
) -> tuple[pd.DataFrame, list]:
    """Faixa de P(avançar) por time na grade; devolve também a célula sem desconto."""
    teams = list(SENSITIVITY_GRID)
    advances, zero = [], None
    for values in itertools.product(*(SENSITIVITY_GRID[t] for t in teams)):
        discounts = dict(zip(teams, values))
        fns = list(prob_fns(points, ratings, models, discounts).values())
        records, _ = simulate_average(fns, base, simulations, seed)
        advance = records[:, :3].sum(axis=1)
        advances.append(advance)
        if not any(values):
            zero = advance
    frame = pd.DataFrame(advances, columns=list(base.names))
    return pd.DataFrame({"min": frame.min(), "max": frame.max()}), list(zero)


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Previsão do Stage 3")
    add_input_arguments(cli)
    cli.add_argument("--check", type=Path, help="pasta da checagem de desastre")
    cli.add_argument("--sims", type=int, default=SIMULATIONS)
    cli.add_argument("--seed", type=int, default=RNG_SEED)
    cli.add_argument("--out", type=Path, default=PREDICTIONS_DIR / "stage3")
    args = cli.parse_args(argv)
    try:
        assert_frozen_b1_code()
        config = load_b1_config(args.b1_params_file)
        check_path, check = load_check(args.check, args.out / "disaster_check")
        hashes = input_hashes(args)
        different = [k for k, v in hashes.items() if check[k] != v]
        if different:
            raise ValueError(f"entradas diferentes das da checagem de desastre: {different}")
        seeds = load_seeds(args.seeds_file)
        stage1, rows1, stage2, rows2 = load_stages(seeds, args.stage1, args.stage2)
        ratings = b1_ratings_at(
            pd.read_parquet(args.matches_file), seeds, config, {1: rows1, 2: rows2}
        )
        names = stage3_names(seeds, stage2)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1

    result = check["resultado"]
    models = result["modelos"]
    points = vrs_points(seeds)
    base = DEFAULT_FORMAT.stage_state(3, names)
    fns = list(prob_fns(points, ratings, models).values())
    records, positions = simulate_average(fns, base, args.sims, args.seed)
    spread, zero = sensitivity_range(points, ratings, models, base, args.sims, args.seed)
    advance = records[:, :3].sum(axis=1)
    if list(advance) != zero:
        raise RuntimeError("a célula sem desconto não reproduziu a previsão oficial")

    columns = [f"P({label})" for label in FINAL_RECORD_LABELS]
    table = pd.DataFrame(records, columns=columns)
    table.insert(0, "seed", range(1, 17))
    table.insert(1, "time", names)
    table.insert(2, "vrs_pontos", [int(points[n]) for n in names])
    table["P(avançar)"] = advance
    table["P(avançar) mín"] = spread.loc[names, "min"].to_numpy()
    table["P(avançar) máx"] = spread.loc[names, "max"].to_numpy()
    table = table.sort_values(["P(avançar)", "seed"], ascending=[False, True], ignore_index=True)
    position_table = pd.DataFrame(positions, columns=[f"P(posição {i})" for i in range(1, 17)])
    position_table.insert(0, "seed", range(1, 17))
    position_table.insert(1, "time", names)
    official = mean_prob_fn(fns)
    seed_of = {team.name: team.seed for team in base.teams}
    opening = pd.DataFrame(
        [
            {
                "seed_a": seed_of[p.team_a], "time_a": p.team_a,
                "seed_b": seed_of[p.team_b], "time_b": p.team_b,
                "best_of": best_of(0, 0, base.all_best_of_three),
                "P(time_a vence)": official(p.team_a, p.team_b, p.best_of),
            }
            for p in pair_round(base)
        ]  # fmt: skip
    )
    rating_table = pd.DataFrame(
        {"seed": range(1, 17), "time": names, "b1": [ratings[n] for n in names]}
    )

    model_name = "B0 puro" if models == ["B0"] else "média 50/50 de B0 e B1"
    metadata = run_metadata() | hashes | {
        "kind": "previsao_stage3",
        "model": model_name,
        "decision": result["decisao"],
        "disaster_check": check_path.name,
        "n_sims": args.sims,
        "rng_seed": args.seed,
        "format": ACTIVE_FORMAT,
        "format_officially_confirmed": False,
        "stage3_seeds": names,
        "sensitivity_grid_vrs": {k: list(v) for k, v in SENSITIVITY_GRID.items()},
    }
    text = "\n".join(
        [
            "# Previsão do Stage 3 — PGL Major Singapore 2026",
            "",
            f"- Gerada em {metadata['generated_at_utc']} (UTC); commit do código "
            f"`{metadata['git_commit'][:10]}`"
            + (" com alterações não commitadas" if metadata["git_uncommitted_code"] else "")
            + ".",
            f"- Modelo oficial: **{model_name}**, sem desconto. Checagem de desastre "
            f"({check_path.name}): {CONSEQUENCES[result['decisao']]}.",
            f"- {args.sims} simulações por variante, semente {args.seed}. Formato "
            f"`{ACTIVE_FORMAT}` (**não confirmado oficialmente**).",
            "- Faixa mín.–máx.: sensibilidade da emenda 4 (Vitality 0, −25, −50; Legacy 0, "
            "−50, −100 pontos VRS; valores arbitrários). **Não é a previsão oficial.** A troca "
            "de titular não foi confirmada pela PGL; ksloks não tem partida com a Legacy no "
            "histórico.",
            "- Playoffs não calculados (adendo antes de 10/12).",
            "- Limites: sem mapas, veto ou jogadores; probabilidades fixas dentro de cada "
            "simulação; o desempenho de B0 e B1 no Stage 1 era conhecido.",
            "",
            "## Fase suíça",
            "",
            *markdown_table(
                ["Seed", "Time", *columns, "P(avançar)", "mín", "máx"],
                [
                    [r["seed"], r["time"], *[percent(r[c]) for c in columns],
                     percent(r["P(avançar)"]), percent(r["P(avançar) mín"]),
                     percent(r["P(avançar) máx"])]  # fmt: skip
                    for r in table.to_dict("records")
                ],
            ),
            "",
            "## Rodada de abertura",
            "",
            *markdown_table(
                ["Seeds", "Time A", "Time B", "Bo", "P(A vence)"],
                [
                    [f"{r.seed_a}v{r.seed_b}", r.time_a, r.time_b, r.best_of,
                     percent(r["P(time_a vence)"])]  # fmt: skip
                    for _, r in opening.iterrows()
                ],
            ),
            "",
            "Posição final na suíça: `positions.csv`.",
            "",
        ]
    )
    out = new_output_dir(args.out, metadata)
    write_csv(out / "probabilities.csv", table)
    write_csv(out / "positions.csv", position_table)
    write_csv(out / "opening_round.csv", opening)
    write_csv(out / "b1_ratings.csv", rating_table)
    write_text(out / "summary.md", text)
    write_json(out / "meta.json", metadata)
    print(text)
    print(f"Gravado em {out}")
    print("Nada foi commitado. Commit e push ANTES do primeiro jogo do Stage 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
