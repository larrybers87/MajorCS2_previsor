"""Previsão do Stage 2.

Com o Stage 1 completo::

    predict_stage2 --stage1 data/manual/stage1_results.csv

A cada resultado do Stage 2 (condiciona nos fatos)::

    predict_stage2 --stage1 data/manual/stage1_results.csv --stage2 data/manual/stage2_results.csv

Antes de o Stage 1 terminar (simula o restante e encadeia o Stage 2)::

    predict_stage2 --conditioned [--stage1 <CSV parcial>]

O modelo é o B0 com o formato histórico tratado pela regra pré-registrada de H10
(``backtest.h10_format``): se a fração de Bo1 não é identificável, roda-se com ``w=0`` e
``w=1`` e o número principal é a média das probabilidades dos dois.

Cada execução grava uma pasta nova em ``predictions/stage2/<carimbo UTC>/``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.h10_format import PARAMS_PATH
from ingest.seeds import SEEDS_PATH, load_seeds
from swiss import ProbFn, StageState, best_of, current_round, pair_round, records, simulate_stage
from swiss.rules import FINAL_RECORD_LABELS, WINS_TO_ADVANCE

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
from .results import build_state, file_sha256, format_notes, pairing_report, read_results
from .stages import entrants_by_seed, stage2_names

ADVANCE_LABELS = [label for label in FINAL_RECORD_LABELS if label.startswith(f"{WINS_TO_ADVANCE}-")]
RECORD_COLUMNS = [f"P({label})" for label in FINAL_RECORD_LABELS]
ADVANCE_COLUMNS = [f"P({label})" for label in ADVANCE_LABELS]


def _load_stage(path: Path | None, base: StageState, notes: list[str], label: str):
    """Lê o CSV (se houver) e registra as divergências com as regras."""
    if path is None:
        return base, []
    rows = read_results(path)
    state = build_state(base, rows)
    notes += [f"{label}: {note}" for note in format_notes(state, rows)]
    notes += [f"{label} (emparelhamento): {line}" for line in pairing_report(state)]
    return state, rows


def _mean_prob_fn(prob_fns: list[ProbFn]) -> ProbFn:
    def prob_fn(team_a: str, team_b: str, fmt: int) -> float:
        return float(np.mean([f(team_a, team_b, fmt) for f in prob_fns]))

    return prob_fn


def _record_frame(teams, probabilities: np.ndarray, seeds: pd.DataFrame) -> pd.DataFrame:
    info = seeds.set_index("name")
    frame = pd.DataFrame(probabilities, columns=RECORD_COLUMNS)
    frame.insert(0, "time", list(teams))
    frame.insert(1, "vrs_pontos", [int(info.loc[t, "vrs_points"]) for t in teams])
    frame["P(avançar)"] = frame[ADVANCE_COLUMNS].sum(axis=1)
    return frame


def _add_extremes(table, results, labels, seeds) -> None:
    """Colunas ``P(avançar) w=...`` de cada variante, quando há mais de uma."""
    if len(results) < 2:
        return
    for label, result in zip(labels, results):
        frame = _record_frame(result.teams, result.record_counts / result.n_sims, seeds)
        by_team = dict(zip(frame["time"], frame["P(avançar)"]))
        table[f"P(avançar) {label}"] = [by_team[t] for t in table["time"]]


def _next_round(state: StageState, prob_fn: ProbFn) -> pd.DataFrame:
    """Partidas ainda não decididas da rodada atual (anunciadas ou geradas pela engine)."""
    round_number = current_round(state)
    if round_number is None:
        return pd.DataFrame()
    listed = {m.pair: m for m in state.round_matches(round_number)}
    seed = {team.name: team.seed for team in state.teams}
    engine = pair_round(state)
    rows = []
    pairs = [(m.team_a, m.team_b) for m in listed.values() if not m.decided]
    if len(listed) < len(engine):
        pairs += [(p.team_a, p.team_b) for p in engine if p.pair not in listed]
    current = records(state.before_round(round_number))
    for a, b in pairs:
        a, b = sorted((a, b), key=seed.__getitem__)
        fmt = best_of(*current[a], state.all_best_of_three)
        rows.append(
            {
                "rodada": round_number,
                "seed_a": seed[a],
                "time_a": a,
                "seed_b": seed[b],
                "time_b": b,
                "best_of": fmt,
                "P(time_a vence)": prob_fn(a, b, fmt),
                "origem": "anunciada" if frozenset((a, b)) in listed else "engine",
            }
        )
    return pd.DataFrame(rows).sort_values("seed_a", ignore_index=True)


def _probability_rows(frame: pd.DataFrame, first_columns: list[str]) -> list[list[str]]:
    percent_columns = [c for c in frame.columns if c.startswith("P(")]
    return [
        [str(row[c]) for c in first_columns] + [percent(row[c]) for c in percent_columns]
        for _, row in frame.iterrows()
    ]


def _pairing_table(frame: pd.DataFrame) -> list[str]:
    return markdown_table(
        ["Seeds", "Time A", "Time B", "Formato", "P(A vence)"],
        [
            [
                f"{r.seed_a}v{r.seed_b}", r.time_a, r.time_b, f"Bo{r.best_of}",
                percent(r["P(time_a vence)"]),
            ]
            for _, r in frame.iterrows()
        ],  # fmt: skip
    )


def _summary_header(metadata: dict, model: dict, mode: str) -> list[str]:
    betas = ", ".join(f"w={v['w']:g}: beta {v['beta']:.4f}" for v in model["variants"])
    if model["mode"] == "faixa":
        format_line = (
            f"- Formato das partidas históricas (H10): a fração de Bo1 não é identificável (IC "
            f"[{model['ci'][0]:.2f}; {model['ci'][1]:.2f}]). Número principal = **média** das "
            f"probabilidades dos dois extremos ({betas}); as colunas `w=0` e `w=1` mostram a faixa."
        )
    else:
        format_line = f"- Formato das partidas históricas (H10): fração de Bo1 estimada ({betas})."
    return [
        "# Previsão do Stage 2 — PGL Major Singapore 2026",
        "",
        f"- Gerado em {metadata['generated_at_utc']} (UTC); commit do código "
        f"`{metadata['git_commit'][:10]}`"
        + (" com alterações não commitadas" if metadata["git_uncommitted_code"] else "")
        + ".",
        f"- Modo: **{mode}**. Simulações: {metadata['n_sims']} por variante.",
        f"- Modelo **B0**: só pontos VRS de 02/11/2026 ({model['transform']}), calibrado em "
        f"partidas até {model['train_last']}.",
        format_line,
        "- Limites: ignora forma recente, mapas, elencos, substitutos e a força mostrada neste "
        "Major (o B0 não atualiza ratings; os resultados entram só como fatos). No teste, o B0 "
        "foi confiante demais acima de 80% (n pequeno). Hipóteses de regras em "
        "`docs/duvidas_abertas.md`.",
        "",
    ]


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(prog="predict_stage2", description="Previsão do Stage 2 (B0)")
    cli.add_argument("--stage1", type=Path, help="CSV de resultados do Stage 1")
    cli.add_argument("--stage2", type=Path, help="CSV de resultados/confrontos do Stage 2")
    cli.add_argument("--conditioned", action="store_true",
                     help="simula o restante do Stage 1 e encadeia o Stage 2")  # fmt: skip
    cli.add_argument("--sims", type=int, default=200_000)
    cli.add_argument("--seed", type=int, default=20261127)
    cli.add_argument("--seeds-file", type=Path, default=SEEDS_PATH)
    cli.add_argument("--params-file", type=Path, default=PARAMS_PATH)
    cli.add_argument("--out", type=Path, default=PREDICTIONS_DIR / "stage2")
    args = cli.parse_args(argv)

    stage1_path = args.stage1
    default_stage1 = MANUAL_DIR / "stage1_results.csv"
    if stage1_path is None and default_stage1.exists():
        stage1_path = default_stage1
    if stage1_path is None and not args.conditioned:
        cli.error(f"falta o CSV do Stage 1 ({default_stage1}); ou use --conditioned")

    try:
        seeds = load_seeds(args.seeds_file)
        model = load_stage2_model(args.params_file)
        notes: list[str] = []
        base1 = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1))
        stage1, rows1 = _load_stage(stage1_path, base1, notes, "Stage 1")
        complete = current_round(stage1) is None
        if not complete and not args.conditioned:
            cli.error(
                f"Stage 1 incompleto (rodada atual: {current_round(stage1)}); "
                "complete o CSV ou use --conditioned"
            )
        if args.stage2 and not complete:
            cli.error("resultados do Stage 2 exigem o Stage 1 completo")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1

    labels = [f"w={v['w']:g}" for v in model["variants"]]
    prob_fns = [
        b0_from(seeds, v["beta"], model["transform"]).prob_fn() for v in model["variants"]
    ]
    prob_fn = _mean_prob_fn(prob_fns)
    metadata = run_metadata() | {
        "n_sims": args.sims,
        "rng_seed": args.seed,
        "model": "B0",
        "format_rule": model["mode"],
        "variants": model["variants"],
        "transform": model["transform"],
        "stage1_csv_sha256": file_sha256(stage1_path) if stage1_path else None,
        "stage2_csv_sha256": file_sha256(args.stage2) if args.stage2 else None,
        "stage1_matches_decided": sum(r.winner is not None for r in rows1),
    }
    invited = entrants_by_seed(seeds, 2)
    files: dict[str, pd.DataFrame] = {}

    if complete:
        mode = "Stage 1 completo"
        base2 = DEFAULT_FORMAT.stage_state(2, stage2_names(seeds, stage1))
        stage2, rows2 = _load_stage(args.stage2, base2, notes, "Stage 2")
        metadata["stage2_matches_decided"] = sum(r.winner is not None for r in rows2)
        metadata["stage2_seeds"] = list(stage2.names)
        if rows2:
            mode += f" + {metadata['stage2_matches_decided']} resultados do Stage 2"
        results = [
            simulate_stage(f, stage2, args.sims, np.random.default_rng(args.seed))
            for f in prob_fns
        ]
        mean = np.mean([r.record_counts / args.sims for r in results], axis=0)
        table = _record_frame(results[0].teams, mean, seeds)
        table.insert(0, "seed", range(1, 17))
        _add_extremes(table, results, labels, seeds)
        table = table.sort_values("P(avançar)", ascending=False, ignore_index=True)

        opening = _next_round(base2, prob_fn)
        files = {"probabilities.csv": table, "opening_round.csv": opening}
        upcoming = _next_round(stage2, prob_fn)
        if rows2 and not upcoming.empty:
            files["next_round.csv"] = upcoming

        body = ["## Probabilidades por time", ""]
        body += markdown_table(
            ["Time", "Seed", *table.columns[3:]],
            _probability_rows(table, ["time", "seed"]),
        )
        body += ["", "## Rodada de abertura (1v9 ... 8v16, pela engine)", ""]
        body += _pairing_table(opening)
        if "next_round.csv" in files:
            body += ["", f"## Próximas partidas (rodada {upcoming['rodada'].iloc[0]})", ""]
            body += _pairing_table(upcoming)
    else:
        mode = (
            f"condicionado: Stage 1 com {metadata['stage1_matches_decided']} partidas "
            "decididas, restante simulado"
        )
        results = [
            simulate_chained(f, stage1, invited, args.sims, np.random.default_rng(args.seed))
            for f in prob_fns
        ]
        teams = results[0].teams
        mean = np.mean([r.record_counts / args.sims for r in results], axis=0)
        participation = np.mean([r.participation_counts / args.sims for r in results], axis=0)
        table = _record_frame(teams, mean, seeds)
        table.insert(2, "P(participa)", participation)
        table["P(avançar | participa)"] = np.divide(
            table["P(avançar)"], participation,
            out=np.full(len(table), np.nan), where=participation > 0,
        )  # fmt: skip
        _add_extremes(table, results, labels, seeds)
        table = table.sort_values(
            ["P(avançar)", "P(participa)"], ascending=False, ignore_index=True
        )

        opening_counts = np.mean([r.opening_counts / args.sims for r in results], axis=0)
        opening_rows = []
        for i, team in enumerate(invited):
            for j in np.argsort(-opening_counts[i], kind="stable"):
                share = opening_counts[i, j]
                if share == 0:
                    break
                opening_rows.append(
                    {
                        "seed_a": i + 1,
                        "time_a": team,
                        "seed_b": i + 9,
                        "time_b": teams[j],
                        "P(confronto)": share,
                        "P(time_a vence)": prob_fn(team, teams[j], 1),
                    }
                )
        opening = pd.DataFrame(opening_rows)
        files = {"probabilities.csv": table, "opening_round.csv": opening}
        pending = _next_round(stage1, prob_fn)
        files["stage1_next_round.csv"] = pending

        body = [f"## Stage 1: partidas pendentes da rodada {pending['rodada'].iloc[0]}", ""]
        body += _pairing_table(pending)
        body += [
            "",
            "## Probabilidades por time no Stage 2",
            "",
            "As colunas de cartel e P(avançar) já incluem a chance de o time chegar ao "
            "Stage 2.",
            "",
        ]
        body += markdown_table(["Time", *table.columns[2:]], _probability_rows(table, ["time"]))
        body += ["", "## Rodada de abertura: três adversários mais prováveis (Bo1)", ""]
        top = opening.groupby("seed_a").head(3)
        body += markdown_table(
            ["Confronto", "Time", "Adversário", "P(confronto)", "P(vitória do convidado)"],
            [
                [
                    f"{r.seed_a}v{r.seed_b}", r.time_a, r.time_b,
                    percent(r["P(confronto)"]), percent(r["P(time_a vence)"]),
                ]
                for _, r in top.iterrows()
            ],  # fmt: skip
        )

    metadata["mode"] = mode
    metadata["rule_notes"] = notes
    out = new_output_dir(args.out, metadata)
    metadata |= freeze_inputs(out, args.seeds_file, args.params_file)
    for name, frame in files.items():
        write_csv(out / name, frame)
    summary = _summary_header(metadata, model, mode)
    if notes:
        summary += ["## Atenção: divergências entre o CSV e as regras", ""]
        summary += [f"- {note}" for note in notes] + [""]
    write_text(out / "summary.md", "\n".join(summary + body) + "\n")
    write_json(out / "meta.json", metadata)

    print("\n".join(summary + body))
    print(f"\nGravado em {out}")
    print("Para registrar: git add, git commit e git push ANTES da próxima partida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
