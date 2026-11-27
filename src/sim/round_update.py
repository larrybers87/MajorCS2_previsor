"""Atualização do Stage 2 antes de cada rodada (2 a 5).

Uso, depois de completar no CSV a rodada anterior::

    python -m sim.round_update --stage2 data/manual/stage2_results.csv [--wiki <wikitext>]

Faz, nesta ordem: V2 (confrontos reais x engine), ratings do B1 só com rodadas anteriores
(D33), confrontos da próxima rodada, probabilidade por partida e Monte Carlo condicional
com o **B0 da previsão oficial** (modelo do Stage 2), e grava uma pasta nova em
``predictions/stage2/round<N>/<carimbo>/``. **Não faz commit** e não altera a previsão
oficial. O B1 não entra nas probabilidades: fica salvo para o Stage 3. Ao final atualiza
os dados do site (``data/processed/site_data.js``).

Se a rodada já tiver confrontos anunciados diferentes dos da engine, liste a rodada
inteira no CSV, com placar vazio nas pendentes.
"""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.b1_selection import PARAMS_PATH as B1_PARAMS_PATH
from ingest.seeds import SEEDS_PATH, load_seeds
from ingest.vrs_matches import MATCHES_PATH
from swiss import StageState, best_of, current_round, records, simulate_stage, standings
from swiss.rules import FINAL_RECORD_LABELS

from .b1_ratings import config_from, major_ratings
from .common import (
    MANUAL_DIR,
    PREDICTIONS_DIR,
    load_params,
    markdown_table,
    new_output_dir,
    percent,
    run_metadata,
    write_csv,
    write_json,
    write_text,
)
from .export_site import PROCESSED_DIR, STAGE2_CSV, build, write_site_data
from .format_config import DEFAULT_FORMAT
from .live import OfficialModel, full_round, official_model
from .official import OFFICIAL_COMMIT, OFFICIAL_DIR, OFFICIAL_RELATIVE
from .results import (
    ResultRow,
    build_state,
    file_sha256,
    format_notes,
    pairing_report,
    read_results,
)
from .stages import entrants_by_seed, stage2_names, stage3_names
from .wiki_check import compare_with_csv, parse_matches

RECORD_COLUMNS = [f"P({label})" for label in FINAL_RECORD_LABELS]


def load_states(
    seeds: pd.DataFrame, stage1_rows: Sequence[ResultRow], stage2_rows: Sequence[ResultRow],
    official: OfficialModel,
) -> tuple[StageState, StageState]:  # fmt: skip
    base1 = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1))
    stage1 = build_state(base1, stage1_rows)
    if current_round(stage1) is not None:
        raise ValueError("o CSV do Stage 1 está incompleto")
    names = stage2_names(seeds, stage1)
    if names != official.meta["stage2_seeds"]:
        raise ValueError("os seeds do Stage 2 não são os da previsão oficial; confira o CSV")
    stage2 = build_state(DEFAULT_FORMAT.stage_state(2, names), stage2_rows)
    return stage1, stage2


def next_matches(state: StageState, official: OfficialModel) -> pd.DataFrame:
    """Partidas pendentes da rodada atual, com a probabilidade do melhor seed."""
    number = current_round(state)
    listed = {m.pair for m in state.round_matches(number)}
    seed = {team.name: team.seed for team in state.teams}
    current = records(state.before_round(number))
    rows = []
    for match in full_round(state):
        if match.winner is not None:
            continue
        a, b = sorted(match.pair, key=seed.__getitem__)
        fmt = best_of(*current[a], state.all_best_of_three)
        row = {
            "rodada": number, "seed_a": seed[a], "time_a": a, "seed_b": seed[b], "time_b": b,
            "cartel": "{}-{}".format(*current[a]), "best_of": fmt,
            "P(time_a vence)": official.prob_fn(a, b, fmt),
        }  # fmt: skip
        for variant, fn in zip(official.variants, official.prob_fns):
            row[f"P(time_a vence) w={variant['w']:g}"] = fn(a, b, fmt)
        row["origem"] = "anunciada" if match.pair in listed else "engine"
        rows.append(row)
    order = ["cartel", "seed_a"]
    return pd.DataFrame(rows).sort_values(order, ascending=[False, True], ignore_index=True)


def conditional_table(
    state: StageState, official: OfficialModel, n_sims: int, seed: int
) -> pd.DataFrame:
    """Cartéis finais condicionados aos resultados já informados."""
    results = [
        simulate_stage(fn, state, n_sims, np.random.default_rng(seed))
        for fn in official.prob_fns
    ]
    probs = [r.record_counts / n_sims for r in results]
    table = pd.DataFrame(np.mean(probs, axis=0), columns=RECORD_COLUMNS)
    current = records(state)
    table.insert(0, "seed", range(1, 17))
    table.insert(1, "time", list(state.names))
    table.insert(2, "cartel_atual", ["{}-{}".format(*current[n]) for n in state.names])
    table["P(avançar)"] = table[RECORD_COLUMNS[:3]].sum(axis=1)
    for variant, p in zip(official.variants, probs):
        table[f"P(avançar) w={variant['w']:g}"] = p[:, :3].sum(axis=1)
    before = dict(
        zip(official.probabilities["time"], official.probabilities["P(avançar)"])
    )
    table["P(avançar) na oficial"] = [before[n] for n in table["time"]]
    return table.sort_values(["P(avançar)", "seed"], ascending=[False, True], ignore_index=True)


def _summary(meta: dict, pairings: pd.DataFrame, table: pd.DataFrame) -> str:
    number = meta["round"]
    title = (
        "Stage 2 encerrado" if number is None else f"Stage 2: antes da rodada {number}"
    )
    lines = [
        f"# {title} (atualização ao vivo, NÃO é a previsão oficial)",
        "",
        f"- Gerado em {meta['generated_at_utc']} (UTC). Vale como previsão anterior à rodada "
        "só se o commit for **enviado antes do primeiro jogo dela**.",
        f"- Modelo B0 da oficial ({OFFICIAL_RELATIVE}, commit `{OFFICIAL_COMMIT[:7]}`), "
        f"{meta['n_sims']} simulações por extremo de w.",
        f"- B1 atualizado só com as rodadas {meta['b1_rounds'] or 'anteriores ao Stage 2'} "
        "do Stage 2 (não entra nas probabilidades).",
        "",
    ]
    if meta["decided_in_current_round"]:
        lines += [
            f"> **PARCIAL:** {len(meta['decided_in_current_round'])} partida(s) desta rodada "
            "já estavam decididas. Entraram como fato na simulação e **não** nos ratings.",
            "",
        ]
    checks = meta["v2_mismatches"] + meta["format_notes"]
    lines += ["## V2 (confrontos reais x engine)", ""]
    lines += [f"- **ATENÇÃO:** {c}" for c in checks] or ["Sem divergências."]
    if meta["wiki_notes"] is not None:
        lines += ["", "## Conferência secundária com a Wikipedia", ""]
        lines += [f"- {n}" for n in meta["wiki_notes"]] or ["Sem diferenças."]
    if number is not None:
        lines += ["", f"## Rodada {number}", ""]
        lines += markdown_table(
            ["Cartel", "Seeds", "Time A", "Time B", "Bo", "P(A vence)", "Origem"],
            [
                [
                    r["cartel"], f"{r['seed_a']}v{r['seed_b']}", r["time_a"], r["time_b"],
                    r["best_of"], percent(r["P(time_a vence)"]), r["origem"],
                ]
                for r in pairings.to_dict("records")
            ],  # fmt: skip
        )
        if (pairings["origem"] == "engine").any():
            lines += [
                "",
                "Confrontos com origem `engine` ainda não foram confirmados pelo anúncio "
                "oficial; se diferirem, liste a rodada no CSV e rode de novo.",
            ]
    percent_columns = [c for c in table.columns if c.startswith("P(")]
    lines += ["", "## Times", ""]
    lines += markdown_table(
        ["Seed", "Time", "Cartel", *percent_columns],
        [
            [r["seed"], r["time"], r["cartel_atual"], *[percent(r[c]) for c in percent_columns]]
            for r in table.to_dict("records")
        ],
    )
    if meta.get("stage3_seeds"):
        lines += ["", "## Seeds do Stage 3", ""]
        lines += [f"{i}. {name}" for i, name in enumerate(meta["stage3_seeds"], start=1)]
    return "\n".join(lines) + "\n"


def site_target(args: argparse.Namespace) -> Path | None:
    """Pasta dos dados do site; ``None`` = não exportar.

    Sem ``--site-dir``, só uma execução com o CSV e a saída padrão mexe no site real:
    um ensaio com caminhos próprios não o contamina.
    """
    if args.no_site:
        return None
    if args.site_dir is not None:
        return args.site_dir
    real = (
        args.stage2.resolve() == STAGE2_CSV.resolve()
        and args.out.resolve() == (PREDICTIONS_DIR / "stage2").resolve()
    )
    return PROCESSED_DIR if real else None


def update_site(args: argparse.Namespace) -> None:
    """Exporta os dados do site. Uma falha aqui não invalida a atualização já gravada."""
    folder = site_target(args)
    if folder is None:
        print("Dados do site não atualizados (--no-site ou caminhos próprios sem --site-dir).")
        return
    try:
        data = build(args.stage1, args.official_dir, args.seeds_file, args.stage2, args.out)
        path = write_site_data(data, folder)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"ATENÇÃO: o site NÃO foi atualizado: {exc}")
        print("  Depois de corrigir: python -m sim.export_site")
        return
    print(f"Site atualizado: {path}")


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Atualização do Stage 2 por rodada")
    cli.add_argument("--stage1", type=Path, default=MANUAL_DIR / "stage1_results.csv")
    cli.add_argument("--stage2", type=Path, default=MANUAL_DIR / "stage2_results.csv")
    cli.add_argument("--wiki", type=Path, help="wikitext salvo, para conferência secundária")
    cli.add_argument("--sims", type=int, default=200_000)
    cli.add_argument("--seed", type=int, default=20261127)
    cli.add_argument("--seeds-file", type=Path, default=SEEDS_PATH)
    cli.add_argument("--official-dir", type=Path, default=OFFICIAL_DIR)
    cli.add_argument("--matches-file", type=Path, default=MATCHES_PATH)
    cli.add_argument("--b1-params-file", type=Path, default=B1_PARAMS_PATH)
    cli.add_argument("--out", type=Path, default=PREDICTIONS_DIR / "stage2")
    cli.add_argument("--site-dir", type=Path,
                     help="onde gravar os dados do site (padrão: data/processed quando o CSV "
                          "e a saída são os padrões)")  # fmt: skip
    cli.add_argument("--no-site", action="store_true", help="não atualiza os dados do site")
    args = cli.parse_args(argv)

    try:
        seeds = load_seeds(args.seeds_file)
        official = official_model(seeds, args.official_dir)
        rows1, rows2 = read_results(args.stage1), read_results(args.stage2)
        stage1, stage2 = load_states(seeds, rows1, rows2, official)
        number = current_round(stage2)
        if number == 1:
            raise ValueError(
                "a rodada 1 é coberta pela previsão oficial; complete no CSV os oito "
                "resultados dela antes de atualizar (para só mostrar resultados parciais "
                "no site: python -m sim.export_site)"
            )
        previous = [r for r in rows2 if number is None or r.round < number]
        b1_params = load_params(args.b1_params_file)
        ratings = major_ratings(
            pd.read_parquet(args.matches_file), seeds, config_from(b1_params["chosen"]),
            {1: rows1, 2: previous},
        )  # fmt: skip
        ratings = ratings[ratings["time"].isin(stage2.names)].reset_index(drop=True)
        pairings = pd.DataFrame() if number is None else next_matches(stage2, official)
        table = conditional_table(stage2, official, args.sims, args.seed)
        wiki_notes = None
        if args.wiki:
            text = args.wiki.read_text(encoding="utf-8")
            wiki_notes = compare_with_csv(rows2, parse_matches(text, 2))
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1

    decided_now = [
        {"time_a": r.team_a, "time_b": r.team_b, "vencedor": r.winner}
        for r in rows2
        if r.round == number and r.winner is not None
    ]
    metadata = run_metadata() | {
        "kind": "atualizacao_ao_vivo",
        "round": number,
        "n_sims": args.sims,
        "rng_seed": args.seed,
        "official_commit": OFFICIAL_COMMIT,
        "model_params_sha256": file_sha256(args.official_dir / "model_params.json"),
        "stage1_csv_sha256": file_sha256(args.stage1),
        "stage2_csv_sha256": file_sha256(args.stage2),
        "matches_file_sha256": file_sha256(args.matches_file),
        "b1_config": b1_params["chosen"],
        "b1_rounds": sorted({r.round for r in previous if r.winner is not None}),
        "decided_in_current_round": decided_now,
        "facts": [
            {"rodada": r.round, "time_a": r.team_a, "time_b": r.team_b,
             "placar_a": r.score_a, "placar_b": r.score_b, "best_of": r.best_of}
            for r in rows2
            if r.winner is not None
        ],  # fmt: skip
        "v2_mismatches": pairing_report(stage2),
        "format_notes": format_notes(stage2, rows2),
        "wiki_notes": wiki_notes,
        "stage3_seeds": stage3_names(seeds, stage2) if number is None else None,
    }
    if number is None:
        order = standings(stage2)
        table = table.set_index("time").loc[order].reset_index()
        table = table[["seed", "time", *[c for c in table.columns if c not in ("seed", "time")]]]
    label = "final" if number is None else f"round{number}"
    out = new_output_dir(args.out / label, metadata)
    if number is not None:
        write_csv(out / "pairings.csv", pairings)
    write_csv(out / "probabilities.csv", table)
    write_csv(out / "b1_ratings.csv", ratings)
    text = _summary(metadata, pairings, table)
    write_text(out / "summary.md", text)
    write_json(out / "meta.json", metadata)

    print(text)
    print(f"Gravado em {out}")
    update_site(args)
    print("Nada foi commitado. Para registrar antes da rodada:")
    print(f"  git add \"{out}\"; git commit -m \"Stage 2: {label}\"; git push origin main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
