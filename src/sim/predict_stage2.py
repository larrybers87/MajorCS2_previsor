"""Previsão do Stage 2.

Com o Stage 1 completo::

    predict_stage2 --stage1 data/manual/stage1_results.csv

A cada resultado do Stage 2 (condiciona nos fatos)::

    predict_stage2 --stage1 data/manual/stage1_results.csv --stage2 data/manual/stage2_results.csv

Antes de o Stage 1 terminar (simula o restante e encadeia o Stage 2)::

    predict_stage2 --conditioned [--stage1 <CSV parcial>]

Cada execução grava uma pasta nova em ``predictions/stage2/<carimbo UTC>/``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.b0_calibration import PARAMS_PATH
from ingest.seeds import SEEDS_PATH, load_seeds
from swiss import StageState, best_of, current_round, pair_round, records, simulate_stage
from swiss.rules import FINAL_RECORD_LABELS, WINS_TO_ADVANCE

from .chain import simulate_chained
from .common import (
    MANUAL_DIR,
    PREDICTIONS_DIR,
    b0_from,
    load_params,
    markdown_table,
    new_output_dir,
    percent,
    run_metadata,
    write_json,
)
from .format_config import DEFAULT_FORMAT
from .results import build_state, file_sha256, format_notes, pairing_report, read_results
from .stages import entrants_by_seed, stage2_names

ADVANCE_LABELS = [label for label in FINAL_RECORD_LABELS if label.startswith(f"{WINS_TO_ADVANCE}-")]
RECORD_COLUMNS = [f"P({label})" for label in FINAL_RECORD_LABELS]


def _load_stage(path: Path | None, base: StageState, notes: list[str], label: str):
    """Lê o CSV (se houver) e registra as divergências com as regras."""
    if path is None:
        return base, []
    rows = read_results(path)
    state = build_state(base, rows)
    notes += [f"{label}: {note}" for note in format_notes(state, rows)]
    notes += [f"{label} (emparelhamento): {line}" for line in pairing_report(state)]
    return state, rows


def _record_frame(teams, counts: np.ndarray, n_sims: int, seeds: pd.DataFrame) -> pd.DataFrame:
    info = seeds.set_index("name")
    frame = pd.DataFrame(counts / n_sims, columns=RECORD_COLUMNS)
    frame.insert(0, "time", list(teams))
    frame.insert(1, "vrs_pontos", [int(info.loc[t, "vrs_points"]) for t in teams])
    frame["P(avançar)"] = frame[[f"P({label})" for label in ADVANCE_LABELS]].sum(axis=1)
    return frame


def _next_round(state: StageState, prob_fn) -> pd.DataFrame:
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


def _summary_header(metadata: dict, params: dict, mode: str) -> list[str]:
    return [
        "# Previsão do Stage 2 — PGL Major Singapore 2026",
        "",
        f"- Gerado em {metadata['generated_at_utc']} (UTC); commit do código "
        f"`{metadata['git_commit'][:10]}`"
        + (" com alterações não commitadas" if metadata["git_uncommitted_code"] else "")
        + ".",
        f"- Modo: **{mode}**. Simulações: {metadata['n_sims']}.",
        f"- Modelo **B0**: só pontos VRS de 02/11/2026; beta = {params['beta']:.4f} "
        f"({params['transform']}), calibrado em partidas até {params['train_last']}.",
        "- Limites: ignora forma recente, mapas, elencos e resultados deste Major (o B0 não "
        "atualiza ratings); H10 (formato das partidas históricas) e as hipóteses de regras "
        "estão em `docs/duvidas_abertas.md`.",
        "- Os nomes THE ONE = 1win e GOSH = BC.Game no VRS são hipótese (D15).",
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
        params = load_params(args.params_file)
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

    model = b0_from(seeds, params["beta"], params["transform"])
    # Sensibilidade à hipótese H10: beta ajustado como se tudo fosse Bo1.
    alternative = b0_from(seeds, params["sensitivity_bo1"]["beta"], params["transform"])
    metadata = run_metadata() | {
        "n_sims": args.sims,
        "rng_seed": args.seed,
        "beta": params["beta"],
        "beta_alternative_bo1": params["sensitivity_bo1"]["beta"],
        "transform": params["transform"],
        "stage1_csv_sha256": file_sha256(stage1_path) if stage1_path else None,
        "stage2_csv_sha256": file_sha256(args.stage2) if args.stage2 else None,
        "stage1_matches_decided": sum(r.winner is not None for r in rows1),
        "seeds_file_sha256": file_sha256(args.seeds_file),
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
        result = simulate_stage(model.prob_fn(), stage2, args.sims, np.random.default_rng(args.seed))
        table = _record_frame(result.teams, result.record_counts, args.sims, seeds)
        table.insert(0, "seed", range(1, 17))
        other = simulate_stage(
            alternative.prob_fn(), stage2, args.sims, np.random.default_rng(args.seed)
        ).advance_probabilities()
        table["P(avançar) se H10=Bo1"] = [other[t] for t in table["time"]]
        table = table.sort_values("P(avançar)", ascending=False, ignore_index=True)

        opening = _next_round(base2, model.prob_fn())
        files = {"probabilities.csv": table, "opening_round.csv": opening}
        upcoming = _next_round(stage2, model.prob_fn())
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
        result = simulate_chained(
            model.prob_fn(), stage1, invited, args.sims, np.random.default_rng(args.seed)
        )
        other = simulate_chained(
            alternative.prob_fn(), stage1, invited, args.sims, np.random.default_rng(args.seed)
        )
        table = _record_frame(result.teams, result.record_counts, args.sims, seeds)
        participation = result.participation_counts / args.sims
        table.insert(2, "P(participa)", participation)
        table["P(avançar | participa)"] = np.divide(
            table["P(avançar)"], participation,
            out=np.full(len(table), np.nan), where=participation > 0,
        )  # fmt: skip
        advance_columns = [f"P({label})" for label in ADVANCE_LABELS]
        table["P(avançar) se H10=Bo1"] = (
            _record_frame(other.teams, other.record_counts, args.sims, seeds)[advance_columns]
            .sum(axis=1)
        )  # fmt: skip
        table = table.sort_values(
            ["P(avançar)", "P(participa)"], ascending=False, ignore_index=True
        )

        opening_rows = []
        for i, team in enumerate(invited):
            for j in np.argsort(-result.opening_counts[i], kind="stable"):
                share = result.opening_counts[i, j] / args.sims
                if share == 0:
                    break
                opponent = result.teams[j]
                opening_rows.append(
                    {
                        "seed_a": i + 1,
                        "time_a": team,
                        "seed_b": i + 9,
                        "time_b": opponent,
                        "P(confronto)": share,
                        "P(time_a vence)": model.prob_fn()(team, opponent, 1),
                    }
                )
        opening = pd.DataFrame(opening_rows)
        files = {"probabilities.csv": table, "opening_round.csv": opening}

        body = [
            "## Probabilidades por time",
            "",
            "As colunas de cartel e P(avançar) já incluem a chance de o time chegar ao "
            "Stage 2.",
            "",
        ]
        body += markdown_table(
            ["Time", *table.columns[2:]], _probability_rows(table, ["time"])
        )
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
    for name, frame in files.items():
        frame.to_csv(out / name, index=False, encoding="utf-8", float_format="%.6f")
    summary = _summary_header(metadata, params, mode)
    if notes:
        summary += ["## Atenção: divergências entre o CSV e as regras", ""]
        summary += [f"- {note}" for note in notes] + [""]
    (out / "summary.md").write_text("\n".join(summary + body) + "\n", encoding="utf-8")
    write_json(out / "meta.json", metadata)

    print("\n".join(summary + body))
    print(f"\nGravado em {out}")
    print("Para registrar a previsão: git add e commit desta pasta ANTES da próxima partida.")
    return 0


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


if __name__ == "__main__":
    raise SystemExit(main())
