"""Avaliação da previsão oficial do Stage 2 (protocolo e emendas 1, 2 e 3).

Uso, depois do fim do Stage 2::

    python -m backtest.stage2_evaluation

Regras (``docs/avaliacao_stage2*.md``), na ordem do relatório:

* probabilidade por partida: média de w=0 e w=1 da pasta oficial, no formato jogado;
* referências: 50% e "maior VRS fixo" (0,595137 para quem tem mais pontos);
* diferenças pareadas com bootstrap por partidas (10.000, semente 20261128);
* cartel final: soma dos log scores marginais; referências pelo mesmo simulador
  (200.000 cada, semente 20261127); probabilidade zero vira 1/(2 x simulações);
* teste de consistência: torneios simulados pelo próprio modelo (200.000 por extremo de
  w, semente 20261127); percentil = fração com score menor ou igual ao observado;
* leitura (emenda 3): melhor se d < -2 EP, pior se d > +2 EP, senão inconclusivo.

Nada aqui altera a previsão. Grava ``docs/resultado_stage2.md`` (não sobrescreve sem
``--force``) e ``data/processed/stage2_evaluation.json``.
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
from sim.common import MANUAL_DIR, markdown_table, percent, run_metadata, write_text
from sim.format_config import DEFAULT_FORMAT
from sim.live import OfficialModel, official_model
from sim.official import (
    DEADLINE_UTC,
    OFFICIAL_COMMIT,
    OFFICIAL_DIR,
    OFFICIAL_PUSH_UTC,
    OFFICIAL_RELATIVE,
)
from sim.results import (
    ResultRow,
    build_state,
    file_sha256,
    format_notes,
    pairing_report,
    read_results,
)
from sim.stages import entrants_by_seed, stage2_names
from sim.wiki_check import compare_with_csv, parse_matches
from swiss import (
    ProbFn,
    StageState,
    advancing_teams,
    best_of,
    current_round,
    pair_round,
    records,
    simulate_stage,
)
from swiss.rules import FINAL_RECORD_LABELS, FINAL_RECORDS, N_ROUNDS, N_TEAMS
from swiss.simulate import _pair_round_batch, probability_table

from .metrics import brier_each, log_loss_each

# Parâmetros fixados antes dos resultados (emenda 2).
VRS_FAVORITE_P = 0.595137
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20261128
SIMULATIONS = 200_000
SIMULATION_SEED = 20261127

MODEL = "B0 oficial"
REFERENCES = ("50%", "maior VRS fixo")
BETTER = "melhor que a referência"
WORSE = "pior que a referência"
INCONCLUSIVE = "inconclusivo"

REPORT_PATH = PROJECT_ROOT / "docs" / "resultado_stage2.md"
JSON_PATH = PROJECT_ROOT / "data" / "processed" / "stage2_evaluation.json"
STAGE2_CSV = MANUAL_DIR / "stage2_results.csv"


def reference_prob_fns(vrs_points: dict[str, float]) -> dict[str, ProbFn]:
    def coin(team_a: str, team_b: str, fmt: int) -> float:
        return 0.5

    def vrs(team_a: str, team_b: str, fmt: int) -> float:
        a, b = vrs_points[team_a], vrs_points[team_b]
        if a == b:
            raise ValueError(f"pontos VRS iguais: {team_a} e {team_b}")
        return VRS_FAVORITE_P if a > b else 1 - VRS_FAVORITE_P

    return dict(zip(REFERENCES, (coin, vrs)))


def label(difference: float, standard_error: float) -> str:
    """Emenda 3: ``difference`` = log loss do modelo menos o da referência."""
    if difference < -2 * standard_error:
        return BETTER
    if difference > 2 * standard_error:
        return WORSE
    return INCONCLUSIVE


# ---------- por partida ----------


def match_table(
    state: StageState,
    rows: Sequence[ResultRow],
    model: OfficialModel,
    references: dict[str, ProbFn],
) -> pd.DataFrame:
    """Uma linha por partida, por rodada e pelo seed inicial do melhor time."""
    seed = {team.name: team.seed for team in state.teams}
    out = []
    for row in rows:
        if row.winner is None:
            continue
        a, b = sorted((row.team_a, row.team_b), key=seed.__getitem__)
        wins, losses = records(state.before_round(row.round))[a]
        fmt = row.best_of or best_of(wins, losses, state.all_best_of_three)
        a_won = row.winner == a
        entry = {
            "rodada": row.round, "seed_a": seed[a], "time_a": a, "time_b": b,
            "best_of": fmt, "vencedor": row.winner,
        }  # fmt: skip
        fns = {MODEL: model.prob_fn} | references
        for name, fn in fns.items():
            p = fn(a, b, fmt)
            entry[f"p {name}"] = p
            entry[f"log_loss {name}"] = float(log_loss_each(p, a_won))
            entry[f"brier {name}"] = float(brier_each(p, a_won))
        out.append(entry)
    table = pd.DataFrame(out)
    return table.sort_values(["rodada", "seed_a"], ignore_index=True)


def comparisons(table: pd.DataFrame) -> list[dict]:
    """Diferenças pareadas modelo - referência, com rótulo e IC por bootstrap."""
    n = len(table)
    if n < 2:
        raise ValueError("são necessárias pelo menos duas partidas")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = rng.integers(0, n, size=(BOOTSTRAP_REPS, n))  # as mesmas para tudo
    out = []
    for reference in REFERENCES:
        entry: dict = {"referencia": reference, "n": n}
        for metric in ("log_loss", "brier"):
            d = (table[f"{metric} {MODEL}"] - table[f"{metric} {reference}"]).to_numpy()
            low, high = np.quantile(d[draws].mean(axis=1), [0.025, 0.975])
            entry[metric] = float(d.mean())
            entry[f"{metric}_ic"] = [float(low), float(high)]
        d = (table[f"log_loss {MODEL}"] - table[f"log_loss {reference}"]).to_numpy()
        entry["erro_padrao"] = float(d.std(ddof=1) / np.sqrt(n))
        entry["leitura"] = label(entry["log_loss"], entry["erro_padrao"])
        out.append(entry)
    return out


# ---------- cartel final ----------


def record_columns(wins: np.ndarray, losses: np.ndarray) -> np.ndarray:
    """Índice do cartel final (ordem de ``FINAL_RECORD_LABELS``) de cada entrada."""
    lookup = np.full((4, 4), -1)
    for column, (w, l_) in enumerate(FINAL_RECORDS):
        lookup[w, l_] = column
    return lookup[wins, losses]


def surprise_table(probabilities: np.ndarray, simulations: int) -> np.ndarray:
    """``-ln P`` por time e cartel; zero vira ``1 / (2 x simulações)``."""
    return -np.log(np.where(probabilities > 0, probabilities, 1 / (2 * simulations)))


def record_probabilities(
    base: StageState, references: dict[str, ProbFn], simulations: int, seed: int
) -> dict[str, np.ndarray]:
    return {
        name: simulate_stage(fn, base, simulations, np.random.default_rng(seed)).record_counts
        / simulations
        for name, fn in references.items()
    }


# ---------- teste de consistência ----------


def play_tournaments(table: np.ndarray, base: StageState, n: int, rng: np.random.Generator):
    """Como ``swiss.simulate.simulate_chunk`` a partir do zero, guardando cada partida.

    Devolve ``(wins, losses, rodadas)``; cada rodada é ``(a, b, formato, a_venceu)``.
    Usa os mesmos sorteios na mesma ordem (há teste comparando as duas).
    """
    if base.matches:
        raise ValueError("o teste de consistência parte do stage sem partidas")
    index = {name: i for i, name in enumerate(base.names)}
    wins = np.zeros((n, N_TEAMS), dtype=np.int8)
    losses = np.zeros((n, N_TEAMS), dtype=np.int8)
    played = np.zeros((n, N_TEAMS, N_TEAMS), dtype=bool)
    rows = np.arange(n)[:, None]
    rounds = []
    for number in range(1, N_ROUNDS + 1):
        if number == 1:
            first = pair_round(base)
            a = np.tile([index[p.team_a] for p in first], (n, 1))
            b = np.tile([index[p.team_b] for p in first], (n, 1))
        else:
            a, b = _pair_round_batch(number, wins, losses, played)
        if base.all_best_of_three:
            fmt = np.ones_like(a)
        else:
            fmt = ((wins[rows, a] == 2) | (losses[rows, a] == 2)).astype(int)
        a_wins = rng.random(a.shape) < table[fmt, a, b]
        winner = np.where(a_wins, a, b)
        loser = np.where(a_wins, b, a)
        wins[rows, winner] += 1
        losses[rows, loser] += 1
        played[rows, a, b] = True
        played[rows, b, a] = True
        rounds.append((a, b, fmt, a_wins))
    return wins, losses, rounds


def simulated_metrics(
    base: StageState,
    generators: Sequence[ProbFn],
    scored: dict[str, ProbFn],
    surprises: dict[str, np.ndarray],
    simulations: int,
    seed: int,
    chunk_size: int = 50_000,
) -> dict[tuple[str, str], np.ndarray]:
    """``{(métrica, modelo): valores}`` em torneios gerados por cada extremo de w."""
    names = base.names
    bo3 = base.all_best_of_three
    tables = {name: probability_table(fn, names, bo3) for name, fn in scored.items()}
    metrics = ("log_loss", "brier", "cartel")
    out: dict = {(m, name): [] for m in metrics for name in scored}
    for generator in generators:
        source = probability_table(generator, names, bo3)
        rng = np.random.default_rng(seed)  # como na previsão oficial
        remaining = simulations
        while remaining:
            n = min(chunk_size, remaining)
            remaining -= n
            wins, losses, rounds = play_tournaments(source, base, n, rng)
            matches = sum(a.shape[1] for a, *_ in rounds)
            columns = record_columns(wins, losses)
            for name, table in tables.items():
                loss = np.zeros(n)
                brier = np.zeros(n)
                for a, b, fmt, a_wins in rounds:
                    p = table[fmt, a, b]
                    loss += log_loss_each(p, a_wins).sum(axis=1)
                    brier += brier_each(p, a_wins).sum(axis=1)
                out[("log_loss", name)].append(loss / matches)
                out[("brier", name)].append(brier / matches)
                surprise = surprises[name]
                out[("cartel", name)].append(
                    surprise[np.arange(N_TEAMS), columns].sum(axis=1)
                )
    return {key: np.concatenate(values) for key, values in out.items()}


def consistency(values: dict, observed: dict) -> list[dict]:
    """Intervalo de 95% e percentil do observado, para a métrica e para as diferenças."""
    out = []
    for metric in ("log_loss", "brier", "cartel"):
        for reference in (None, *REFERENCES):
            simulated = values[(metric, MODEL)]
            seen = observed[(metric, MODEL)]
            if reference is not None:
                simulated = simulated - values[(metric, reference)]
                seen = seen - observed[(metric, reference)]
            low, high = np.quantile(simulated, [0.025, 0.975])
            out.append(
                {
                    "metrica": metric,
                    "contra": reference,
                    "observado": float(seen),
                    "q2_5": float(low),
                    "q97_5": float(high),
                    "percentil": float(np.mean(simulated <= seen + 1e-12)),
                }
            )
    return out


# ---------- avaliação ----------


def evaluate(
    stage1_path: Path,
    stage2_path: Path,
    official_dir: Path = OFFICIAL_DIR,
    seeds_path: Path = SEEDS_PATH,
    simulations: int = SIMULATIONS,
) -> dict:
    seeds = load_seeds(seeds_path)
    model = official_model(seeds, official_dir)
    base1 = DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1))
    stage1 = build_state(base1, read_results(stage1_path))
    names = stage2_names(seeds, stage1)
    if names != model.meta["stage2_seeds"]:
        raise ValueError("os seeds do Stage 2 não são os da previsão oficial")
    if "condicionado" in model.meta.get("mode", ""):
        raise ValueError("a pontuação de previsão condicionada não foi implementada")
    base = DEFAULT_FORMAT.stage_state(2, names)
    rows = read_results(stage2_path)
    state = build_state(base, rows)
    if current_round(state) is not None:
        raise ValueError(
            f"o Stage 2 não terminou (rodada {current_round(state)}): nada é avaliado antes"
        )
    vrs = {n: float(p) for n, p in zip(seeds["name"], seeds["vrs_points"])}
    references = reference_prob_fns({n: vrs[n] for n in names})
    table = match_table(state, rows, model, references)

    official_table = model.probabilities.set_index("time").loc[list(names)]
    probabilities = {
        MODEL: official_table[[f"P({k})" for k in FINAL_RECORD_LABELS]].to_numpy()
    } | record_probabilities(base, references, simulations, SIMULATION_SEED)
    # A tabela oficial é a média de um número igual de simulações por extremo de w.
    model_sims = int(model.meta["n_sims"]) * len(model.prob_fns)
    surprises = {
        name: surprise_table(p, model_sims if name == MODEL else simulations)
        for name, p in probabilities.items()
    }
    current = records(state)
    columns = record_columns(
        np.array([current[n][0] for n in names]), np.array([current[n][1] for n in names])
    )
    advanced = set(advancing_teams(state))
    teams = [
        {
            "seed": i + 1,
            "time": name,
            "cartel": FINAL_RECORD_LABELS[columns[i]],
            "p_cartel": float(probabilities[MODEL][i, columns[i]]),
            "log_score": float(surprises[MODEL][i, columns[i]]),
            "p_avancar": float(official_table.loc[name, "P(avançar)"]),
            "avancou": name in advanced,
        }
        for i, name in enumerate(names)
    ]
    record_score = {
        name: float(surprise[np.arange(N_TEAMS), columns].sum())
        for name, surprise in surprises.items()
    }
    observed = {("cartel", name): score for name, score in record_score.items()}
    for name in (MODEL, *REFERENCES):
        for metric in ("log_loss", "brier"):
            observed[(metric, name)] = float(table[f"{metric} {name}"].mean())
    simulated = simulated_metrics(
        base, model.prob_fns, {MODEL: model.prob_fn} | references, surprises,
        simulations, SIMULATION_SEED,
    )  # fmt: skip
    return {
        "simulacoes": simulations,
        "por_partida": {
            name: {m: observed[(m, name)] for m in ("log_loss", "brier")}
            for name in (MODEL, *REFERENCES)
        },
        "comparacoes": comparisons(table),
        "cartel": record_score,
        "times": teams,
        "consistencia": consistency(simulated, observed),
        "partidas": table.to_dict("records"),
        "v2": pairing_report(state),
        "formato": format_notes(state, rows),
        "zeros_substituidos": [
            t["time"] for t in teams if t["p_cartel"] == 0
        ],
    }


def _live_updates(base: Path = PROJECT_ROOT / "predictions" / "stage2") -> list[list[str]]:
    rows = []
    for meta in sorted(base.glob("*/*/meta.json")):
        folder = meta.parent.relative_to(PROJECT_ROOT).as_posix()
        git = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "log", "--diff-filter=A", "--format=%h %cI",
             "--", folder],
            capture_output=True, text=True,
        )  # fmt: skip
        added = git.stdout.split("\n")[-2] if git.stdout.strip() else "não commitada"
        rows.append([folder, added, "⟨horário do push⟩", "⟨primeiro jogo da rodada⟩"])
    return rows


def official_integrity(folder: Path = OFFICIAL_DIR) -> str:
    """Compara a pasta local com o commit oficial (quebras de linha normalizadas)."""
    for path in sorted(folder.iterdir()):
        blob = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "cat-file", "blob",
             f"{OFFICIAL_COMMIT}:{OFFICIAL_RELATIVE}/{path.name}"],
            capture_output=True,
        )  # fmt: skip
        if blob.returncode != 0:
            raise ValueError(f"não foi possível ler {path.name} no commit oficial")
        if blob.stdout.replace(b"\r\n", b"\n") != path.read_bytes().replace(b"\r\n", b"\n"):
            raise ValueError(f"{path.name} difere do commit oficial")
    return "idêntica ao commit"


def report(data: dict, header: dict) -> str:
    def f(value: float, sign: str = "") -> str:
        return f"{value:{sign}.4f}"

    names = {"log_loss": "log loss", "brier": "Brier", "cartel": "log score dos cartéis"}
    lines = [
        "# Avaliação da previsão oficial do Stage 2",
        "",
        f"Gerado por `python -m backtest.stage2_evaluation` em {header['gerado_em']} (UTC), "
        f"commit do código `{header['commit'][:10]}`"
        + (" com alterações não commitadas" if header["sujo"] else "")
        + ". Regras: [avaliacao_stage2.md](avaliacao_stage2.md) e emendas "
        "[1](avaliacao_stage2_emenda_01.md), [2](avaliacao_stage2_emenda_02.md) e "
        "[3](avaliacao_stage2_emenda_03.md).",
        "",
        "## 0. Conferências",
        "",
        *markdown_table(
            ["Item", "Valor"],
            [
                ["Previsão avaliada", f"`{OFFICIAL_RELATIVE}`, commit `{OFFICIAL_COMMIT[:7]}`"],
                ["Push", f"{OFFICIAL_PUSH_UTC} (prazo {DEADLINE_UTC})"],
                ["Pasta local x commit", header["integridade"]],
                ["Pasta mais recente do último push anterior ao prazo (D28)",
                 "⟨conferir na API do GitHub⟩"],
                ["CSV dos resultados (SHA-256)", f"`{header['csv_sha256']}`"],
                ["Partidas decididas", f"{len(data['partidas'])} de 33"],
                ["V2 (confrontos reais x engine)", "; ".join(data["v2"]) or "sem divergências"],
                ["Formato jogado x regra", "; ".join(data["formato"]) or "sem divergências"],
                ["Conferência secundária", header["wiki"]],
                ["W.O., desistências, substituições", "⟨registrar o que houve e a fonte⟩"],
            ],
        ),
        "",
        "## 1. Por partida (log loss primária; Brier secundária)",
        "",
        *markdown_table(
            ["Modelo ou referência", "log loss", "Brier"],
            [[k, f(v["log_loss"]), f(v["brier"])] for k, v in data["por_partida"].items()],
        ),
        "",
        "Diferença pareada, modelo − referência (negativo favorece o modelo), com IC 95% "
        f"por bootstrap de partidas ({BOOTSTRAP_REPS} réplicas, semente {BOOTSTRAP_SEED}):",
        "",
        *markdown_table(
            ["Contra", "log loss", "IC 95%", "Brier", "IC 95%"],
            [
                [
                    c["referencia"], f(c["log_loss"], "+"),
                    f"[{f(c['log_loss_ic'][0], '+')}; {f(c['log_loss_ic'][1], '+')}]",
                    f(c["brier"], "+"),
                    f"[{f(c['brier_ic'][0], '+')}; {f(c['brier_ic'][1], '+')}]",
                ]
                for c in data["comparacoes"]
            ],  # fmt: skip
        ),
        "",
        "## 2. Cartel final",
        "",
        "Soma, nos 16 times, de `-ln P(cartel observado)`. Referências pelo mesmo simulador "
        f"({data['simulacoes']} cada, semente {SIMULATION_SEED}). A soma das marginais não é "
        "o log score da distribuição conjunta.",
        "",
        *markdown_table(
            ["Modelo ou referência", "log score (soma)", "modelo − referência"],
            [
                [k, f(v), "" if k == MODEL else f(data["cartel"][MODEL] - v, "+")]
                for k, v in data["cartel"].items()
            ],
        ),
        "",
        *(
            [f"Probabilidade zero substituída: {', '.join(data['zeros_substituidos'])}.", ""]
            if data["zeros_substituidos"]
            else []
        ),
        *markdown_table(
            ["Seed", "Time", "Cartel", "P(cartel)", "-ln P", "P(avançar)", "Avançou"],
            [
                [
                    t["seed"], t["time"], t["cartel"], percent(t["p_cartel"]),
                    f"{t['log_score']:.3f}", percent(t["p_avancar"]),
                    "sim" if t["avancou"] else "não",
                ]
                for t in data["times"]
            ],  # fmt: skip
        ),
        "",
        "## 3. Teste de consistência (não mede qualidade)",
        "",
        f"Torneios simulados pelo próprio modelo: {data['simulacoes']} por extremo de w, "
        f"semente {SIMULATION_SEED}. Percentil = fração com valor menor ou igual ao "
        "observado.",
        "",
        *markdown_table(
            ["Métrica", "Observado", "quantil 2,5%", "quantil 97,5%", "percentil"],
            [
                [
                    names[c["metrica"]] + (f" − {c['contra']}" if c["contra"] else ""),
                    f(c["observado"]), f(c["q2_5"]), f(c["q97_5"]), percent(c["percentil"]),
                ]
                for c in data["consistencia"]
            ],  # fmt: skip
        ),
        "",
        "## 4. Partidas",
        "",
        *markdown_table(
            ["R", "Partida", "Bo", "P(melhor seed)", "Vencedor", "log loss", "Brier"],
            [
                [
                    m["rodada"], f"{m['time_a']} x {m['time_b']}", m["best_of"],
                    percent(m[f"p {MODEL}"]), m["vencedor"],
                    f"{m[f'log_loss {MODEL}']:.3f}", f"{m[f'brier {MODEL}']:.3f}",
                ]
                for m in data["partidas"]
            ],  # fmt: skip
        ),
        "",
        "## 5. Leitura (emenda 3)",
        "",
        "Só o log loss recebe rótulo: melhor se `d < −2 EP`, pior se `d > +2 EP`, "
        "inconclusivo se `|d| ≤ 2 EP`.",
        "",
        *markdown_table(
            ["Contra", "n", "d", "EP", "2 x EP", "Leitura"],
            [
                [
                    c["referencia"], c["n"], f(c["log_loss"], "+"), f(c["erro_padrao"]),
                    f(2 * c["erro_padrao"]), f"**{c['leitura']}**",
                ]
                for c in data["comparacoes"]
            ],  # fmt: skip
        ),
        "",
    ]
    for c in data["comparacoes"]:
        low, high = c["log_loss_ic"]
        by_interval = BETTER if high < 0 else WORSE if low > 0 else INCONCLUSIVE
        if by_interval != c["leitura"]:
            lines.append(
                f"- Contra {c['referencia']}: o IC por bootstrap sugeriria \"{by_interval}\"; "
                "vale o rótulo da emenda 3."
            )
    lines += [
        "- O percentil só diz se o observado é compatível com o modelo.",
        "- O EP trata as partidas como independentes, o que não são. Um torneio: o rótulo "
        "vale só para este stage e não ordena modelos.",
        "",
        "⟨observações⟩",
        "",
        "## 6. Fora desta avaliação",
        "",
    ]
    if header["atualizacoes"]:
        lines += markdown_table(
            ["Atualização ao vivo", "Commit", "Push", "Primeiro jogo"], header["atualizacoes"]
        )
    else:
        lines.append("Nenhuma pasta de atualização por rodada encontrada.")
    lines += ["", "- Anexo D25 (não oficial).", "- Ocorrências e limitações: ⟨⟩", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Avaliação oficial do Stage 2")
    cli.add_argument("--stage1", type=Path, default=MANUAL_DIR / "stage1_results.csv")
    cli.add_argument("--stage2", type=Path, default=STAGE2_CSV)
    cli.add_argument("--wiki", type=Path, help="wikitext salvo, para conferência secundária")
    cli.add_argument("--report", type=Path, default=REPORT_PATH)
    cli.add_argument("--json", type=Path, default=JSON_PATH)
    cli.add_argument("--force", action="store_true", help="sobrescreve o relatório")
    args = cli.parse_args(argv)
    if args.report.exists() and not args.force:
        print(f"ERRO: {args.report} já existe (pode ter anotações); use --force para refazer")
        return 1
    try:
        integrity = official_integrity()
        data = evaluate(args.stage1, args.stage2)
        wiki = "⟨fonte e diferenças⟩"
        if args.wiki:
            text = args.wiki.read_text(encoding="utf-8")
            notes = compare_with_csv(read_results(args.stage2), parse_matches(text, 2))
            wiki = "Wikipedia: " + ("; ".join(notes) or "sem diferenças")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERRO: {exc}")
        return 1
    metadata = run_metadata()
    header = {
        "gerado_em": metadata["generated_at_utc"],
        "commit": metadata["git_commit"],
        "sujo": metadata["git_uncommitted_code"],
        "integridade": integrity,
        "csv_sha256": file_sha256(args.stage2),
        "wiki": wiki,
        "atualizacoes": _live_updates(),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    write_text(args.json, json.dumps(header | data, indent=2, ensure_ascii=False) + "\n")
    text = report(data, header)
    write_text(args.report, text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
