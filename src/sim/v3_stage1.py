"""V3 RETROSPECTIVO: B0 contra o Stage 1 já (parcialmente) jogado.

Uso::

    python -m sim.v3_stage1 --results data/manual/stage1_results.csv [--no-b1]

Também confere os seeds (rodada 1) e os emparelhamentos das rodadas 2-5 (V2) e compara
B0 e B1 lado a lado (``backtest.v3_compare``).
Nenhum parâmetro é ajustado aqui: tudo vem de calibrações anteriores ao Stage 1.
``matches.csv`` e ``teams.csv`` seguem sendo o B0 com ``w=0``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.b0_calibration import PARAMS_PATH
from backtest.b1_selection import PARAMS_PATH as B1_PARAMS_PATH
from backtest.h10_format import PARAMS_PATH as MODEL_PATH
from backtest.metrics import brier_each, log_loss_each
from backtest.v3_compare import compare, comparison_lines
from ingest.seeds import SEEDS_PATH, load_seeds
from ingest.vrs_matches import MATCHES_PATH
from swiss import StageState, best_of, current_round, records, simulate_stage
from swiss.rules import FINAL_RECORD_COUNTS, FINAL_RECORD_LABELS, N_TEAMS

from .b1_ratings import config_from
from .common import (
    MANUAL_DIR,
    PREDICTIONS_DIR,
    b0_from,
    freeze_inputs,
    load_params,
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
from .results import ResultRow, build_state, file_sha256, format_notes, pairing_report, read_results
from .stages import entrants_by_seed


def match_table(state: StageState, rows: list[ResultRow], model) -> pd.DataFrame:
    """Probabilidade pré-evento de cada partida decidida, no formato em que foi jogada."""
    prob_fn = model.prob_fn()
    out = []
    for row in sorted(rows, key=lambda r: r.round):
        if row.winner is None:
            continue
        current = records(state.before_round(row.round))
        fmt = row.best_of or best_of(*current[row.team_a], state.all_best_of_three)
        p = prob_fn(row.team_a, row.team_b, fmt)
        a_won = row.winner == row.team_a
        out.append(
            {
                "rodada": row.round,
                "time_a": row.team_a,
                "time_b": row.team_b,
                "best_of": fmt,
                "P(time_a vence)": p,
                "vencedor": row.winner,
                "P(vencedor)": p if a_won else 1 - p,
                "log_loss": float(log_loss_each(p, a_won)),
                "brier": float(brier_each(p, a_won)),
                "vrs_a": model.ratings[row.team_a],
                "vrs_b": model.ratings[row.team_b],
            }
        )
    return pd.DataFrame(out)


def team_table(state: StageState, result) -> pd.DataFrame:
    """Distribuição prevista desde a rodada 1 contra o cartel observado."""
    probs = result.record_probabilities()
    advance = result.advance_probabilities()
    current = records(state)
    rows = []
    for team in state.names:
        wins, losses = current[team]
        label = f"{wins}-{losses}"
        finished = label in FINAL_RECORD_LABELS
        rows.append(
            {
                "seed": state.seed_of(team),
                "time": team,
                **{f"P({k})": v for k, v in probs[team].items()},
                "P(avançar)": advance[team],
                "cartel_observado": label,
                "encerrado": finished,
                "P(cartel observado)": probs[team][label] if finished else np.nan,
            }
        )
    return pd.DataFrame(rows)


def scores(matches: pd.DataFrame, teams: pd.DataFrame) -> dict:
    """Métricas agregadas, com referências sem informação."""
    out: dict = {"partidas": len(matches)}
    if len(matches):
        loss = matches["log_loss"]
        diff = np.sign(matches["vrs_a"] - matches["vrs_b"])
        a_won = (matches["vencedor"] == matches["time_a"]).to_numpy()
        out |= {
            "log_loss": float(loss.mean()),
            "log_loss_erro_padrao": float(loss.std(ddof=1) / np.sqrt(len(loss)))
            if len(loss) > 1 else None,
            "log_loss_50": float(np.log(2)),
            "brier": float(matches["brier"].mean()),
            "brier_50": 0.25,
            "brier_maior_vrs_vence": float(brier_each(0.5 + 0.5 * diff, a_won).mean()),
            "acerto_do_favorito": float((matches["P(vencedor)"] > 0.5).mean()),
        }  # fmt: skip
    finished = teams[teams["encerrado"]]
    # Só com o stage completo: antes disso, os times encerrados são selecionados pelo
    # resultado (após a rodada 3, apenas 3-0 e 0-3).
    if len(finished) == len(teams):
        # Referência sem informação: todo time com a frequência de cada cartel no formato.
        baseline = dict(zip(FINAL_RECORD_LABELS, np.array(FINAL_RECORD_COUNTS) / N_TEAMS))
        advanced = finished["cartel_observado"].str.startswith("3-").to_numpy()
        out |= {
            "times_encerrados": len(finished),
            "log_score_cartel": float(
                -np.log(np.maximum(finished["P(cartel observado)"], 1e-12)).mean()
            ),
            "log_score_cartel_sem_informacao": float(
                -np.log(finished["cartel_observado"].map(baseline)).mean()
            ),
            "brier_avanco": float(brier_each(finished["P(avançar)"], advanced).mean()),
            "brier_avanco_sem_informacao": 0.25,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="V3 retrospectivo do Stage 1 (B0)")
    cli.add_argument("--results", type=Path, default=MANUAL_DIR / "stage1_results.csv")
    cli.add_argument("--sims", type=int, default=200_000)
    cli.add_argument("--seed", type=int, default=20261124)
    cli.add_argument("--seeds-file", type=Path, default=SEEDS_PATH)
    cli.add_argument("--params-file", type=Path, default=PARAMS_PATH)
    cli.add_argument("--out", type=Path, default=PREDICTIONS_DIR / "v3_stage1")
    cli.add_argument("--no-b1", action="store_true", help="só o B0, sem a comparação")
    cli.add_argument("--matches-file", type=Path, default=MATCHES_PATH)
    cli.add_argument("--b1-params-file", type=Path, default=B1_PARAMS_PATH)
    cli.add_argument("--model-file", type=Path, default=MODEL_PATH)
    args = cli.parse_args(argv)

    if not args.results.exists():
        print(f"ERRO: falta o CSV de resultados do Stage 1: {args.results}")
        return 1
    try:
        seeds = load_seeds(args.seeds_file)
        params = load_params(args.params_file)
        base = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1))
        rows = read_results(args.results)
        state = build_state(base, rows)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1

    model = b0_from(seeds, params["beta"], params["transform"])
    result = simulate_stage(model.prob_fn(), base, args.sims, np.random.default_rng(args.seed))
    matches = match_table(state, rows, model)
    teams = team_table(state, result)
    summary_scores = scores(matches, teams)
    mismatches = pairing_report(state)
    round_one = [line for line in mismatches if line.startswith("rodada 1:")]
    later = [line for line in mismatches if not line.startswith("rodada 1:")]
    notes = format_notes(state, rows)
    last_round = max((r.round for r in rows), default=0)

    comparison = None
    if not args.no_b1:
        try:
            b0_model = load_stage2_model(args.model_file)
            b1_params = load_params(args.b1_params_file)
            comparison = compare(
                base, state, rows, seeds, b0_model["variants"], b0_model["transform"],
                pd.read_parquet(args.matches_file), config_from(b1_params["chosen"]),
                args.sims, args.seed, current_round(state) is None,
            )  # fmt: skip
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERRO na comparação com o B1 (use --no-b1 para só o B0): {exc}")
            return 1

    metadata = run_metadata() | {
        "label": "RETROSPECTIVO",
        "n_sims": args.sims,
        "rng_seed": args.seed,
        "beta": params["beta"],
        "transform": params["transform"],
        "results_csv_sha256": file_sha256(args.results),
        "scores": summary_scores,
        "pairing_mismatches": mismatches,
        "format_notes": notes,
    }
    if comparison:
        metadata["comparison"] = comparison[1]
    lines = [
        "# V3 — Stage 1 (RETROSPECTIVO)",
        "",
        "Gerado **depois** das partidas: não é previsão. O B0 usa só o VRS de 02/11/2026 e "
        f"beta calibrado em partidas até {params['train_last']}; nada foi ajustado com o "
        "Stage 1. Com no máximo 33 partidas, o resultado NÃO permite comparar modelos.",
        "",
        "As seções de métricas e partidas logo abaixo são do **B0 com w=0**"
        + ("; a comparação com o B1 está no fim." if comparison else "."),
        "",
        f"Partidas decididas: {summary_scores['partidas']} de 33; "
        + ("stage encerrado." if current_round(state) is None
           else f"stage na rodada {current_round(state)}."),  # fmt: skip
        "",
        "## Validação das regras",
        "",
        "- Rodada 1 real = 1v9 ... 8v16 com os nossos seeds: "
        + ("**sem partidas no CSV**" if not rows else
           "**NÃO**" if round_one else "**sim**"),  # fmt: skip
        *[f"  - {line}" for line in round_one],
        f"- V2, rodadas 2 a {max(last_round, 2)}: "
        + ("não há partidas." if last_round < 2 else
           f"{len(later)} rodada(s) com divergência." if later else "**sem divergências**."),
        *[f"  - {line}" for line in later],
        *[f"- Formato: {note}" for note in notes],
        "",
        "## Métricas",
        "",
        *markdown_table(
            ["Métrica", "Valor"],
            [[k, f"{v:.4f}" if isinstance(v, float) else v] for k, v in summary_scores.items()],
        ),
        "",
        "## Previsto desde a rodada 1 x observado",
        "",
        *markdown_table(
            ["Seed", "Time", *[f"P({k})" for k in FINAL_RECORD_LABELS], "P(avançar)",
             "Observado", "P(observado)"],  # fmt: skip
            [
                [r.seed, r.time, *[percent(r[f"P({k})"]) for k in FINAL_RECORD_LABELS],
                 percent(r["P(avançar)"]),
                 r.cartel_observado + ("" if r.encerrado else " (em jogo)"),
                 percent(r["P(cartel observado)"]) if r.encerrado else "-"]  # fmt: skip
                for _, r in teams.iterrows()
            ],
        ),
        "",
        "## Partidas",
        "",
        *markdown_table(
            ["R", "Time A", "Time B", "Bo", "P(A)", "Vencedor", "log loss"],
            [
                [r.rodada, r.time_a, r.time_b, r.best_of, percent(r["P(time_a vence)"]),
                 r.vencedor, f"{r.log_loss:.3f}"]  # fmt: skip
                for _, r in matches.iterrows()
            ],
        ),
        "",
    ]
    if comparison:
        lines += comparison_lines(*comparison)
    out = new_output_dir(args.out, metadata)
    metadata |= freeze_inputs(out, args.seeds_file, args.params_file)
    if comparison:
        write_csv(out / "comparison.csv", comparison[0])
    write_csv(out / "matches.csv", matches)
    write_csv(out / "teams.csv", teams)
    write_text(out / "summary.md", "\n".join(lines))
    write_json(out / "meta.json", metadata)
    print("\n".join(lines))
    print(f"Gravado em {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
