"""Gera os dados prontos do site (``app/index.html``). O site não calcula nada.

Uso::

    python -m sim.export_site

Para o modo Simulador, use o servidor local (``python -m sim.site_server``), que também
regenera estes dados a cada recarga.

Grava em ``data/processed/`` (fora do git):

* ``site_data.js``: tudo o que o site mostra;
* ``stage2_seeds.csv``: seeds do Stage 2 com a origem de cada time;
* ``stage2_prediction/``: cópia da pasta oficial da previsão do Stage 2.

Emparelhamentos, cartéis, Difficulty e seeds vêm da engine; a avaliação vem de
``backtest.v3_evaluation``; as probabilidades do Stage 2 vêm da pasta oficial congelada.
O Stage 2 ao vivo lê ``data/manual/stage2_results.csv`` (se existir) e a atualização mais
recente em ``predictions/stage2/round<N>/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backtest.v3_evaluation import commit_info, evaluate, match_metrics, summarize_matches
from ingest.seeds import SEEDS_PATH, load_seeds
from ingest.vrs import PROJECT_ROOT
from swiss import StageState, buchholz, records, standings
from swiss.rules import FINAL_RECORD_LABELS, N_ADVANCING

from .common import MANUAL_DIR, PREDICTIONS_DIR, write_csv, write_text
from .format_config import DEFAULT_FORMAT
from .live import OfficialModel, apply_picks, official_model, stage_view
from .official import OFFICIAL_DIR, OFFICIAL_PUSH_UTC
from .results import ResultRow, build_state, pairing_report, read_results
from .stages import entrants_by_seed, stage2_names

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STAGE2_CSV = MANUAL_DIR / "stage2_results.csv"


def round_matches(
    state: StageState, rows: Sequence[ResultRow], predictions: dict
) -> list[list[dict]]:
    """Partidas por rodada, na orientação "melhor seed primeiro", com a previsão."""
    seed = {team.name: team.seed for team in state.teams}
    rounds: list[list[dict]] = []
    for number in sorted({r.round for r in rows}):
        before = records(state.before_round(number))
        matches = []
        for row in (r for r in rows if r.round == number):
            a, b = sorted((row.team_a, row.team_b), key=seed.__getitem__)
            score = {row.team_a: row.score_a, row.team_b: row.score_b}
            prediction = predictions.get((number, frozenset((a, b))))
            if prediction is not None:
                kind, p = prediction
                prediction = {
                    "tipo": kind,
                    "p_a": p["p_a"] if p["time_a"] == a else 1 - p["p_a"],
                    "acertou": p["acertou"],
                    "log_loss": p["log_loss"],
                    "brier": p["brier"],
                }
            matches.append(
                {
                    "rodada": number,
                    "a": a,
                    "b": b,
                    "cartel": list(before[a]),
                    "bo": row.best_of,
                    "placar_a": score[a],
                    "placar_b": score[b],
                    "vencedor": row.winner,
                    "previsao": prediction,
                }
            )
        matches.sort(key=lambda m: (-m["cartel"][0], m["cartel"][1], seed[m["a"]]))
        rounds.append(matches)
    return rounds


def final_table(state: StageState) -> list[dict]:
    """Classificação final do stage com Difficulty e seed no stage seguinte."""
    record = records(state)
    difficulty = buchholz(state)
    rows = []
    for rank, name in enumerate(standings(state), start=1):
        opponents = [
            {
                "rodada": m.round,
                "adversario": m.team_b if m.team_a == name else m.team_a,
                "venceu": m.winner == name,
            }
            for m in sorted(state.matches, key=lambda m: m.round)
            if m.decided and name in m.pair
        ]
        advanced = rank <= N_ADVANCING
        rows.append(
            {
                "posicao": rank,
                "time": name,
                "seed_inicial": state.seed_of(name),
                "cartel": "{}-{}".format(*record[name]),
                "difficulty": difficulty[name],
                "avancou": advanced,
                "seed_seguinte": N_ADVANCING + rank if advanced else None,
                "caminho": opponents,
            }
        )
    return rows


def stage2_seed_table(seeds: pd.DataFrame, stage1: StageState) -> pd.DataFrame:
    """Seeds 1-16 do Stage 2: convidados pelo pré-evento, classificados pelo seed final."""
    info = seeds.set_index("name")
    finals = {row["time"]: row for row in final_table(stage1)}
    rows = []
    for seed, name in enumerate(stage2_names(seeds, stage1), start=1):
        qualified = name in finals
        rows.append(
            {
                "seed": seed,
                "time": name,
                "origem": "Stage 1" if qualified else "convidado",
                "seed_pre_evento": int(info.loc[name, "pre_event_seed"]),
                "vrs_pontos": int(info.loc[name, "vrs_points"]),
                "stage1_cartel": finals[name]["cartel"] if qualified else "",
                "stage1_difficulty": finals[name]["difficulty"] if qualified else "",
                "stage1_seed_inicial": finals[name]["seed_inicial"] if qualified else "",
            }
        )
    return pd.DataFrame(rows)


def latest_update(base: Path) -> dict | None:
    """Atualização ao vivo mais recente (``round<N>/`` ou ``final/``), se houver."""
    found = []
    for meta_path in base.glob("*/*/meta.json"):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("kind") == "atualizacao_ao_vivo":
            found.append((meta["generated_at_utc"], str(meta_path.parent), meta))
    if not found:
        return None
    _, name, meta = max(found, key=lambda item: item[:2])
    folder = Path(name)
    table = pd.read_csv(folder / "probabilities.csv")
    try:
        commit = commit_info(folder / "probabilities.csv")
    except (ValueError, subprocess.CalledProcessError):
        commit = None
    return {
        "pasta": f"{folder.parent.name}/{folder.name}",
        "rodada": meta["round"],
        "gerado_em": meta["generated_at_utc"],
        "parcial": len(meta["decided_in_current_round"]),
        "commit": commit,
        "times": [
            {
                "seed": int(r["seed"]),
                "time": r["time"],
                "cartel_atual": r["cartel_atual"],
                "cartoes": [float(r[f"P({label})"]) for label in FINAL_RECORD_LABELS],
                "p_avancar": float(r["P(avançar)"]),
                "p_oficial": float(r["P(avançar) na oficial"]),
            }
            for r in table.to_dict("records")
        ],
    }


def stage2_live(names: Sequence[str], rows: Sequence[ResultRow], model: OfficialModel) -> dict:
    """Chave do Stage 2 com os resultados reais e a próxima rodada pela engine."""
    real = build_state(DEFAULT_FORMAT.stage_state(2, names), rows)
    state, _, _ = apply_picks(real, ())
    view = stage_view(state, rows, model.prob_fn)
    played = [m for matches in view["rodadas"] for m in matches if m["vencedor"]]
    summary = None
    if played:
        # Probabilidades do B0 oficial, congelado antes da primeira partida.
        predictions = pd.DataFrame(
            [
                {"rodada": m["rodada"], "time_a": m["a"], "time_b": m["b"],
                 "best_of": m["bo"], "P(time_a vence)": m["p_a"]}
                for m in played
            ]  # fmt: skip
        )
        scored = match_metrics(predictions, rows)
        by_key = {(r["rodada"], r["time_a"]): r for r in scored.to_dict("records")}
        for m in played:
            r = by_key[(m["rodada"], m["a"])]
            m["previsao"] = {
                "tipo": "oficial", "p_a": m["p_a"], "acertou": r["acertou"],
                "log_loss": r["log_loss"], "brier": r["brier"],
            }  # fmt: skip
        summary = summarize_matches(scored)
    return view | {
        "partidas_jogadas": len(played),
        "resumo": summary,
        "divergencias_engine": pairing_report(real),
    }


def stage2_data(folder: Path, seed_table: pd.DataFrame) -> dict:
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    if meta["stage2_seeds"] != seed_table["time"].tolist():
        raise ValueError(
            f"{folder.name}: os seeds da previsão não são os calculados a partir do CSV"
        )
    table = pd.read_csv(folder / "probabilities.csv").set_index("time")
    opening = pd.read_csv(folder / "opening_round.csv")
    try:
        commit = commit_info(folder / "probabilities.csv")
    except (ValueError, subprocess.CalledProcessError):
        commit = None
    teams = []
    for row in seed_table.to_dict("records"):
        p = table.loc[row["time"]]
        teams.append(
            row
            | {
                "cartoes": [float(p[f"P({label})"]) for label in FINAL_RECORD_LABELS],
                "p_avancar": float(p["P(avançar)"]),
                "p_avancar_w0": float(p["P(avançar) w=0"]),
                "p_avancar_w1": float(p["P(avançar) w=1"]),
            }
        )
    return {
        "pasta": folder.name,
        "gerado_em": meta["generated_at_utc"],
        "simulacoes": meta["n_sims"],
        "commit": commit,
        "abertura": [
            {
                "seed_a": int(r["seed_a"]),
                "a": r["time_a"],
                "seed_b": int(r["seed_b"]),
                "b": r["time_b"],
                "bo": int(r["best_of"]),
                "p_a": float(r["P(time_a vence)"]),
            }
            for r in opening.to_dict("records")
        ],
        "times": teams,
    }


def build(
    results_path: Path,
    prediction: Path = OFFICIAL_DIR,
    seeds_path: Path = SEEDS_PATH,
    stage2_path: Path = STAGE2_CSV,
    updates_dir: Path = PREDICTIONS_DIR / "stage2",
) -> dict:
    # Calculada antes de ler: uma mudança durante a leitura provoca nova atualização.
    version = data_version(results_path, stage2_path, updates_dir)
    seeds = load_seeds(seeds_path)
    rows = read_results(results_path)
    stage1 = build_state(DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1)), rows)
    evaluation = evaluate(results_path, seeds_path)
    predictions = {
        (m["rodada"], frozenset((m["time_a"], m["time_b"]))): (kind, m)
        for kind, key in (("retrospectivo", "retrospectivo"), ("previo", "previo_r5"))
        for m in evaluation[key]["partidas"]
    }
    seed_table = stage2_seed_table(seeds, stage1)
    info = seeds.set_index("name")
    rows2 = read_results(stage2_path) if stage2_path.exists() else []
    live = stage2_live(seed_table["time"].tolist(), rows2, official_model(seeds, prediction))
    summaries = round_summaries(live, round_predictions(updates_dir, prediction))
    live |= {
        "tem_csv": stage2_path.exists(),
        "atualizacao": latest_update(updates_dir),
        "rodadas_resumo": summaries,
        "ultima_rodada": max((s["rodada"] for s in summaries if s["jogadas"]), default=None),
        "rodada_pendente": next(
            (s["rodada"] for s in summaries if s["jogadas"] < s["total"]), None
        ),
    }
    return {
        "versao": version,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cartoes": list(FINAL_RECORD_LABELS),
        "times": {
            name: {"vrs": int(info.loc[name, "vrs_points"])} for name in info.index
        },
        "stage1": {
            "rodadas": round_matches(stage1, rows, predictions),
            "classificacao": final_table(stage1),
            "divergencias_engine": pairing_report(stage1),
        },
        "avaliacao": evaluation,
        "stage2": stage2_data(prediction, seed_table),
        "stage2_ao_vivo": live,
    }


def _commit_or_none(path: Path) -> dict | None:
    try:
        return commit_info(path)
    except (ValueError, subprocess.CalledProcessError):
        return None


def _pairs(path: Path) -> set[frozenset[str]]:
    table = pd.read_csv(path)
    return {frozenset(p) for p in zip(table["time_a"], table["time_b"])}


def round_predictions(updates_dir: Path, official_dir: Path) -> dict[int, dict]:
    """A previsão gravada para cada rodada do Stage 2.

    Rodada 1: a oficial. Demais: a atualização gerada **sem nenhum resultado da própria
    rodada**; entre várias, a commitada mais recente (senão, a mais recente). Isto não
    prova que ela foi enviada antes do primeiro jogo: só o horário do push prova.
    """
    official = official_dir / "opening_round.csv"
    found = {
        1: {
            "origem": "oficial",
            "pasta": official_dir.name,
            "gerado_em": None,
            "commit": _commit_or_none(official),
            "push": OFFICIAL_PUSH_UTC if official_dir.resolve() == OFFICIAL_DIR.resolve() else None,
            "pares": _pairs(official),
        }
    }
    candidates: dict[int, list[dict]] = {}
    for meta_path in sorted(updates_dir.glob("round*/*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("kind") != "atualizacao_ao_vivo" or meta["decided_in_current_round"]:
            continue
        folder = meta_path.parent
        candidates.setdefault(int(meta["round"]), []).append(
            {
                "origem": "atualizacao",
                "pasta": f"{folder.parent.name}/{folder.name}",
                "gerado_em": meta["generated_at_utc"],
                "commit": _commit_or_none(folder / "pairings.csv"),
                "push": None,
                "pares": _pairs(folder / "pairings.csv"),
            }
        )
    for number, entries in candidates.items():
        committed = [e for e in entries if e["commit"]]
        found[number] = max(committed or entries, key=lambda e: e["gerado_em"])
    return found


def round_summaries(view: dict, predictions: dict[int, dict]) -> list[dict]:
    """Acerto de cada rodada e qual previsão existia para ela."""
    out = []
    for number, matches in enumerate(view["rodadas"], start=1):
        played = [m["previsao"] for m in matches if "previsao" in m]
        prediction = predictions.get(number)
        if prediction is not None:
            actual = {frozenset((m["a"], m["b"])) for m in matches}
            prediction = {k: v for k, v in prediction.items() if k != "pares"} | {
                "confrontos_iguais": prediction["pares"] == actual
            }
        out.append(
            {
                "rodada": number,
                "jogadas": len(played),
                "total": len(matches),
                "resumo": summarize_matches(pd.DataFrame(played)) if played else None,
                "previsao": prediction,
            }
        )
    return out


def data_version(stage1_path: Path, stage2_path: Path, updates_dir: Path) -> str:
    """Assinatura das entradas; a página recarrega quando ela muda (modo servidor)."""
    head = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    parts = [head]
    for path in (stage1_path, stage2_path, *sorted(updates_dir.glob("*/*/meta.json"))):
        if path.exists():
            stat = path.stat()
            parts.append(f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def site_script(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False)
    return f"window.SITE_DATA = {payload};\n"


def write_site_data(data: dict, folder: Path) -> Path:
    """Grava ``site_data.js`` de uma vez (a página nunca lê um arquivo pela metade)."""
    path = folder / "site_data.js"
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder / "site_data.js.tmp"
    write_text(temporary, site_script(data))
    temporary.replace(path)
    return path


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Dados do site")
    cli.add_argument("--stage1", type=Path, default=MANUAL_DIR / "stage1_results.csv")
    cli.add_argument("--stage2", type=Path, default=STAGE2_CSV)
    cli.add_argument("--prediction", type=Path, default=OFFICIAL_DIR,
                     help="pasta da previsão oficial do Stage 2")  # fmt: skip
    cli.add_argument("--out", type=Path, default=PROCESSED_DIR)
    args = cli.parse_args(argv)
    try:
        folder = args.prediction.resolve()
        data = build(args.stage1, folder, stage2_path=args.stage2)
        seeds = load_seeds(SEEDS_PATH)
        stage1 = build_state(
            DEFAULT_FORMAT.stage_state(1, entrants_by_seed(seeds, 1)), read_results(args.stage1)
        )
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERRO: {exc}")
        return 1
    path = write_site_data(data, args.out)
    write_csv(args.out / "stage2_seeds.csv", stage2_seed_table(seeds, stage1))
    shutil.copytree(folder, args.out / "stage2_prediction", dirs_exist_ok=True)
    print(f"Gravado em {path} (previsão oficial {folder.name})")
    print(f"Abra {PROJECT_ROOT / 'app' / 'index.html'} no navegador")
    print("ou, para o Simulador: python -m sim.site_server")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
