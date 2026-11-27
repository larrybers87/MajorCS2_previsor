"""Avaliação diagnóstica do Stage 1 a partir de previsões JÁ COMMITADAS.

Uso::

    python -m backtest.v3_evaluation

Não calcula nenhuma probabilidade nova e não ajusta nada: lê as probabilidades que já
estavam no git e as compara com os resultados. Não existe previsão commitada antes do
primeiro jogo do Stage 1 (o primeiro commit do projeto é de 26/11), então há dois
conjuntos, que NÃO se somam porque usam variantes diferentes do B0:

* **retrospectivo** (rodadas 1 a 4 e cartéis): gerado depois dos jogos, B0 com w=0;
* **prévio da rodada 5**: três partidas, commitadas e enviadas antes de serem jogadas,
  B0 com a média de w=0 e w=1.

Grava ``docs/avaliacao_stage1.md`` e ``data/processed/v3_evaluation.json``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from ingest.seeds import SEEDS_PATH, load_seeds
from ingest.vrs import PROJECT_ROOT
from sim.common import MANUAL_DIR, markdown_table, percent, write_text
from sim.format_config import DEFAULT_FORMAT
from sim.results import ResultRow, build_state, read_results
from sim.stages import entrants_by_seed
from swiss import StageState, advancing_teams, current_round, records
from swiss.rules import FINAL_RECORD_COUNTS, FINAL_RECORD_LABELS, N_ADVANCING, N_TEAMS

from .metrics import brier_each, log_loss_each

RETRO_DIR = PROJECT_ROOT / "predictions" / "v3_stage1" / "20261127T001603Z"
PRIOR_R5_FILE = (
    PROJECT_ROOT / "predictions" / "stage2" / "20261127T001433Z" / "stage1_next_round.csv"
)
JSON_PATH = PROJECT_ROOT / "data" / "processed" / "v3_evaluation.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "avaliacao_stage1.md"

# Horários de push da API de atividade do GitHub e início da rodada 5 (14:00 SGT).
PUSH_TIMES = {"retrospectivo": "2026-11-27T00:19:20Z", "previo_r5": "2026-11-27T00:14:53Z"}
ROUND_FIVE_START = "2026-11-27T06:00:00Z"


def match_metrics(predictions: pd.DataFrame, results: Sequence[ResultRow]) -> pd.DataFrame:
    """Junta cada probabilidade commitada ao resultado da mesma partida."""
    index = {(r.round, frozenset((r.team_a, r.team_b))): r for r in results}
    rows = []
    for row in predictions.to_dict("records"):
        a, b, number = row["time_a"], row["time_b"], int(row["rodada"])
        result = index.get((number, frozenset((a, b))))
        if result is None or result.winner is None:
            raise ValueError(f"R{number} {a} x {b}: sem resultado no CSV")
        if result.best_of is not None and result.best_of != int(row["best_of"]):
            raise ValueError(f"R{number} {a} x {b}: formato difere do previsto")
        p = float(row["P(time_a vence)"])
        a_won = result.winner == a
        p_winner = p if a_won else 1 - p
        rows.append(
            {
                "rodada": number,
                "time_a": a,
                "time_b": b,
                "best_of": int(row["best_of"]),
                "p_a": p,
                "vencedor": result.winner,
                "p_vencedor": p_winner,
                "acertou": bool(p_winner > 0.5),
                "log_loss": float(log_loss_each(p, a_won)),
                "brier": float(brier_each(p, a_won)),
            }
        )
    return pd.DataFrame(rows).sort_values("rodada", kind="stable", ignore_index=True)


def summarize_matches(matches: pd.DataFrame) -> dict:
    n = len(matches)
    loss = matches["log_loss"]
    return {
        "n": n,
        "log_loss": float(loss.mean()),
        "log_loss_erro_padrao": float(loss.std(ddof=1) / np.sqrt(n)) if n > 1 else None,
        "log_loss_50": float(np.log(2)),
        "brier": float(matches["brier"].mean()),
        "brier_50": 0.25,
        "favoritos_que_venceram": int(matches["acertou"].sum()),
    }


def team_metrics(predicted: pd.DataFrame, final: StageState) -> tuple[pd.DataFrame, dict]:
    """Cartel final de cada time contra a distribuição prevista antes da rodada 1."""
    if current_round(final) is not None:
        raise ValueError("o stage precisa estar encerrado")
    observed = records(final)
    advanced = set(advancing_teams(final))
    # Empates em P(avançar) saem pelo seed, para o resultado ser determinístico.
    ranked = predicted.sort_values(["P(avançar)", "seed"], ascending=[False, True])
    picks = set(ranked["time"].head(N_ADVANCING))
    baseline = dict(zip(FINAL_RECORD_LABELS, np.array(FINAL_RECORD_COUNTS) / N_TEAMS))
    rows = []
    for row in predicted.to_dict("records"):
        team = row["time"]
        label = "{}-{}".format(*observed[team])
        p = float(row[f"P({label})"])
        rows.append(
            {
                "seed": int(row["seed"]),
                "time": team,
                "p_avancar": float(row["P(avançar)"]),
                "previsto_avanca": team in picks,
                "avancou": team in advanced,
                "cartel": label,
                "p_cartel": p,
                "log_score": float(-np.log(max(p, 1e-12))),
                "log_score_sem_informacao": float(-np.log(baseline[label])),
            }
        )
    table = pd.DataFrame(rows).sort_values("seed", ignore_index=True)
    p_adv = table["p_avancar"].to_numpy()
    summary = {
        "classificados_acertados": int((table["previsto_avanca"] & table["avancou"]).sum()),
        "classificados_total": N_ADVANCING,
        "classificados_esperados_ao_acaso": N_ADVANCING**2 / N_TEAMS,
        "log_score_cartel_soma": float(table["log_score"].sum()),
        "log_score_cartel_media": float(table["log_score"].mean()),
        "log_score_sem_informacao_soma": float(table["log_score_sem_informacao"].sum()),
        "log_score_sem_informacao_media": float(table["log_score_sem_informacao"].mean()),
        "brier_avanco": float(brier_each(p_adv, table["avancou"].to_numpy()).mean()),
        "brier_avanco_sem_informacao": 0.25,
    }
    return table, summary


def commit_info(path: Path) -> dict:
    """Commit que introduziu o arquivo e se a cópia local ainda é igual à versionada."""
    relative = path.relative_to(PROJECT_ROOT).as_posix()

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), *args],
            capture_output=True, text=True, check=True, encoding="utf-8",
        ).stdout.strip()  # fmt: skip

    added = git("log", "--diff-filter=A", "--format=%h %cI", "--", relative).splitlines()
    changes = git("log", "--format=%h", "--", relative).splitlines()
    if not added or len(changes) != 1 or git("status", "--porcelain", "--", relative):
        raise ValueError(f"{relative}: precisa estar commitado uma única vez e sem alterações")
    commit, when = added[-1].split()
    return {"arquivo": relative, "commit": commit, "data_commit": when}


def evaluate(results_path: Path, seeds_path: Path = SEEDS_PATH) -> dict:
    seeds = load_seeds(seeds_path)
    results = read_results(results_path)
    final = build_state(DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1)), results)

    retro_raw = pd.read_csv(RETRO_DIR / "matches.csv")
    retro = match_metrics(retro_raw, results)
    committed = dict(zip(zip(retro_raw["rodada"], retro_raw["time_a"]), retro_raw["vencedor"]))
    changed = [
        r for r in retro.itertuples() if committed[(r.rodada, r.time_a)] != r.vencedor
    ]
    if changed:
        raise ValueError(f"vencedores diferem dos registrados na pasta retrospectiva: {changed}")
    prior = match_metrics(pd.read_csv(PRIOR_R5_FILE), results)
    teams, team_summary = team_metrics(pd.read_csv(RETRO_DIR / "teams.csv"), final)

    by_format = {
        f"Bo{fmt}": summarize_matches(group) for fmt, group in retro.groupby("best_of")
    }
    return {
        "fontes": {
            "retrospectivo": [
                commit_info(RETRO_DIR / "matches.csv"),
                commit_info(RETRO_DIR / "teams.csv"),
            ],
            "previo_r5": [commit_info(PRIOR_R5_FILE)],
            "push": PUSH_TIMES,
            "inicio_rodada_5": ROUND_FIVE_START,
        },
        "retrospectivo": {
            "resumo": summarize_matches(retro),
            "por_formato": by_format,
            "partidas": retro.to_dict("records"),
        },
        "previo_r5": {
            "resumo": summarize_matches(prior),
            "partidas": prior.to_dict("records"),
        },
        "times": {"resumo": team_summary, "linhas": teams.to_dict("records")},
    }


def _match_table(rows: list[dict]) -> list[str]:
    return markdown_table(
        ["R", "Partida", "Formato", "P(A vence)", "Vencedor", "log loss", "Brier"],
        [
            [
                r["rodada"], f"{r['time_a']} x {r['time_b']}", f"Bo{r['best_of']}",
                percent(r["p_a"]), r["vencedor"], f"{r['log_loss']:.3f}", f"{r['brier']:.3f}",
            ]
            for r in rows
        ],  # fmt: skip
    )


def _summary_row(label: str, s: dict) -> list[str]:
    error = s["log_loss_erro_padrao"]
    return [
        label,
        str(s["n"]),
        f"{s['log_loss']:.4f}" + ("" if error is None else f" (EP {error:.3f})"),
        f"{s['brier']:.4f}",
        f"{s['favoritos_que_venceram']}/{s['n']}",
    ]


def report(data: dict) -> str:
    retro, prior, teams = data["retrospectivo"], data["previo_r5"], data["times"]
    t = teams["resumo"]
    sources = data["fontes"]["retrospectivo"] + data["fontes"]["previo_r5"]
    lines = [
        "# Avaliação do Stage 1 (diagnóstico)",
        "",
        "Gerado por `python -m backtest.v3_evaluation` (não editar à mão).",
        "",
        "## Leia antes dos números",
        "",
        "- **Não existe previsão commitada antes do primeiro jogo do Stage 1** (24/11). O "
        "primeiro commit do projeto é de 26/11. Nenhuma previsão retroativa foi criada aqui: "
        "só são lidas probabilidades que já estavam no git.",
        "- **Retrospectivo** (rodadas 1 a 4 e cartéis): gerado **depois** dos jogos. O B0 usa "
        "só o VRS de 02/11 e beta calibrado até 01/11, mas isto **não é teste prospectivo**.",
        "- **Prévio** (rodada 5): 3 partidas enviadas ao GitHub em "
        f"{data['fontes']['push']['previo_r5']}, antes do início "
        f"({data['fontes']['inicio_rodada_5']}). É previsão de verdade, mas com n = 3.",
        "- As duas partes usam variantes diferentes do B0 (w=0 no retrospectivo; média de "
        "w=0 e w=1 no prévio) e **não são somadas**.",
        "- Com n = 30 (ou 33) isto é **diagnóstico**. Não ordena modelos, e as partidas e os "
        "times de um torneio não são independentes.",
        "- O log loss do B1 e da média B0/B1 neste Major **não** foi calculado (reservado à "
        "checagem pré-registrada do Stage 3).",
        "",
        "## Por partida",
        "",
        *markdown_table(
            ["Conjunto", "n", "log loss", "Brier", "Favorito venceu"],
            [
                _summary_row("Retrospectivo, rodadas 1-4", retro["resumo"]),
                *[
                    _summary_row(f"Retrospectivo, só {k}", v)
                    for k, v in retro["por_formato"].items()
                ],
                _summary_row("Prévio, rodada 5", prior["resumo"]),
                ["Referência 50%", "-", f"{np.log(2):.4f}", "0.2500", "-"],
            ],
        ),
        "",
        "A vantagem sobre os 50% no retrospectivo é menor que um erro padrão. Na rodada 5, "
        "o favorito mais claro (HEROIC) perdeu, o que domina a média de 3 partidas.",
        "",
        "## Os 8 classificados (previsão desde a rodada 1, retrospectiva)",
        "",
        f"- Entre os 8 com maior P(avançar), **{t['classificados_acertados']} de 8** "
        f"avançaram (ao acaso, o esperado é {t['classificados_esperados_ao_acaso']:g}).",
        f"- Brier de avançar: {t['brier_avanco']:.4f} (sem informação: 0.2500).",
        f"- Log score do cartel final: soma {t['log_score_cartel_soma']:.3f}, média "
        f"{t['log_score_cartel_media']:.4f}. Sem informação (frequência de cada cartel no "
        f"formato): soma {t['log_score_sem_informacao_soma']:.3f}, média "
        f"{t['log_score_sem_informacao_media']:.4f}. Menor é melhor.",
        "- A soma das marginais não é o log score da distribuição conjunta.",
        "",
        *markdown_table(
            ["Seed", "Time", "P(avançar)", "Entre os 8", "Cartel", "P(cartel)", "log score",
             "sem informação"],  # fmt: skip
            [
                [
                    r["seed"], r["time"], percent(r["p_avancar"]),
                    "sim" if r["previsto_avanca"] else "não", r["cartel"], percent(r["p_cartel"]),
                    f"{r['log_score']:.3f}", f"{r['log_score_sem_informacao']:.3f}",
                ]
                for r in teams["linhas"]
            ],  # fmt: skip
        ),
        "",
        "## Partidas: prévio (rodada 5)",
        "",
        *_match_table(prior["partidas"]),
        "",
        "## Partidas: retrospectivo (rodadas 1-4)",
        "",
        *_match_table(retro["partidas"]),
        "",
        "## Procedência",
        "",
        *markdown_table(
            ["Arquivo", "Commit", "Data do commit"],
            [[s["arquivo"], s["commit"], s["data_commit"]] for s in sources],
        ),
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Avaliação diagnóstica do Stage 1")
    cli.add_argument("--results", type=Path, default=MANUAL_DIR / "stage1_results.csv")
    cli.add_argument("--json", type=Path, default=JSON_PATH)
    cli.add_argument("--report", type=Path, default=REPORT_PATH)
    args = cli.parse_args(argv)
    try:
        data = evaluate(args.results)
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERRO: {exc}")
        return 1
    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_text(args.json, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    text = report(data)
    write_text(args.report, text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
