"""H10: fração de Bo1 (``w``) ajustada junto com beta, split aninhado e D21.

Uso::

    python -m backtest.h10_format

``P_série = w*p + (1-w)*p^2*(3-2p)``, ``p = logística(beta*x)``. Grava
``data/processed/h10_params.json`` e ``docs/h10_verossimilhanca.md``.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ingest.vrs import PROJECT_ROOT
from ingest.vrs_matches import MATCHES_PATH
from models.b0 import TRANSFORMS, features, fit_beta, logistic, series_win_probability
from swiss.probability import series_probability

from .b0_calibration import POPULATIONS, in_population, rated_matches
from .protocol import (
    PERIODS,
    favorite_calibration,
    paired_difference,
    period_mask,
    summarize,
    walk_forward,
)

PARAMS_PATH = PROJECT_ROOT / "data" / "processed" / "h10_params.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "h10_verossimilhanca.md"
RNG_SEED = 20261127
W_GRID = np.round(np.linspace(0, 1, 101), 2)
BOOT_GRID = np.round(np.linspace(0, 1, 21), 2)
N_BOOT = 400
MAX_WIDTH = 0.3  # regra do Larry
CHI2_95_1DF = 3.841458820694124
_EPSILON = 1e-12


def mixture_probability(w: float, beta: float, x) -> np.ndarray:
    p = logistic(beta * np.asarray(x, dtype=float))
    return w * p + (1 - w) * series_probability(p, 3)


def fit_beta_given_w(
    w: float, x: np.ndarray, won: np.ndarray, weights: np.ndarray, tolerance: float = 1e-6
) -> tuple[float, float]:
    """Beta de máxima verossimilhança para ``w`` fixo. Retorna (beta, log-verossimilhança)."""

    def log_likelihood(beta: float) -> float:
        q = np.clip(mixture_probability(w, beta, x), _EPSILON, 1 - _EPSILON)
        return float(np.dot(weights, np.where(won, np.log(q), np.log1p(-q))))

    ratio = (np.sqrt(5) - 1) / 2
    low, high = 0.0, 3.0
    c, d = high - ratio * (high - low), low + ratio * (high - low)
    fc, fd = log_likelihood(c), log_likelihood(d)
    while high - low > tolerance:
        if fc > fd:
            high, d, fd = d, c, fc
            c = high - ratio * (high - low)
            fc = log_likelihood(c)
        else:
            low, c, fc = c, d, fd
            d = low + ratio * (high - low)
            fd = log_likelihood(d)
    beta = (low + high) / 2
    if min(beta, 3.0 - beta) < 1e-3:
        raise RuntimeError(f"ótimo de beta na fronteira ({beta:.3f})")
    return beta, log_likelihood(beta)


def profile(x, won, weights=None, grid=W_GRID, tolerance=1e-6) -> tuple[np.ndarray, np.ndarray]:
    """Perfil de verossimilhança de ``w``: (betas, log-verossimilhanças) na grade."""
    weights = np.ones(len(x)) if weights is None else weights
    fits = [fit_beta_given_w(w, x, won, weights, tolerance) for w in grid]
    betas, values = zip(*fits)
    return np.array(betas), np.array(values)


def profile_interval(values: np.ndarray, grid=W_GRID) -> tuple[float, float]:
    accepted = grid[2 * (values.max() - values) <= CHI2_95_1DF]
    return float(accepted.min()), float(accepted.max())


def bootstrap_w(x, won, days, rng, n_boot=N_BOOT) -> tuple[float, float]:
    """IC percentil de ``w`` reamostrando dias."""
    _, index = np.unique(days, return_inverse=True)
    n_days = index.max() + 1
    estimates = []
    for _ in range(n_boot):
        day_weights = np.bincount(rng.integers(0, n_days, n_days), minlength=n_days)
        _, values = profile(x, won, day_weights[index].astype(float), BOOT_GRID, 1e-4)
        estimates.append(BOOT_GRID[values.argmax()])
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def format_rule(w_hat: float, intervals: list[tuple[float, float]], betas: np.ndarray) -> dict:
    """Regra de apresentação: o intervalo mais largo decide."""
    widest = max(intervals, key=lambda ci: ci[1] - ci[0])
    width = widest[1] - widest[0]
    if width <= MAX_WIDTH + 1e-9:
        chosen = [float(w_hat)]
        mode = "estimado"
    else:
        chosen = [0.0, 1.0]
        mode = "faixa"
    return {
        "mode": mode,
        "ci": list(widest),
        "width": float(width),
        "variants": [
            {"w": w, "beta": float(betas[int(np.argmin(np.abs(W_GRID - w)))])} for w in chosen
        ],
    }


def select_b0(data: pd.DataFrame) -> tuple[dict, dict]:
    """Escolhe transformação e população do B0 pelo log loss no desenvolvimento."""
    won = data["team_a_won"].to_numpy(bool)
    target = in_population(data, "top100")
    scores = {}
    for transform in TRANSFORMS:
        x = _x(data, transform)
        for population in POPULATIONS:
            p = walk_forward(
                data["date"], "dev", in_population(data, population),
                fit=lambda train: fit_beta(x[train], won[train], 3),
                predict=lambda beta, test: series_win_probability(beta, x[test], 3),
            )  # fmt: skip
            mask = period_mask(data["date"], "dev") & target
            q = np.clip(p[mask], _EPSILON, 1 - _EPSILON)
            loss = -np.where(won[mask], np.log(q), np.log1p(-q)).mean()
            scores[f"{population}/{transform}"] = float(loss)
    population, transform = min(scores, key=scores.get).split("/")
    return {"population": population, "transform": transform}, scores


def _x(data: pd.DataFrame, transform: str) -> np.ndarray:
    return features(data["points_a"].to_numpy(float), data["points_b"].to_numpy(float), transform)


def analyze(data: pd.DataFrame, seed: int = RNG_SEED, n_boot: int = N_BOOT) -> dict:
    rng = np.random.default_rng(seed)
    won = data["team_a_won"].to_numpy(bool)
    days = data["date"].to_numpy()
    target = in_population(data, "top100")
    config, dev_scores = select_b0(data)
    x = _x(data, config["transform"])
    train = in_population(data, config["population"])

    betas, values = profile(x[train], won[train])
    w_hat = float(W_GRID[values.argmax()])
    ci_profile = profile_interval(values)
    ci_boot = bootstrap_w(x[train], won[train], days[train], rng, n_boot)
    rule = format_rule(w_hat, [ci_profile, ci_boot], betas)

    # Teste aninhado: w = 0 (B0 atual), w = 1 e w estimado em cada mês anterior.
    test = period_mask(data["date"], "test") & target
    predictions, chosen_w = {}, []
    for label, w in (("w=0", 0.0), ("w=1", 1.0)):
        predictions[label] = walk_forward(
            data["date"], "test", train,
            fit=lambda mask, w=w: fit_beta_given_w(w, x[mask], won[mask], np.ones(mask.sum()))[0],
            predict=lambda beta, mask, w=w: mixture_probability(w, beta, x[mask]),
        )  # fmt: skip

    def fit_free(mask):
        monthly_betas, monthly_values = profile(x[mask], won[mask])
        best = int(monthly_values.argmax())
        chosen_w.append(float(W_GRID[best]))
        return float(W_GRID[best]), float(monthly_betas[best])

    predictions["w estimado"] = walk_forward(
        data["date"], "test", train, fit=fit_free,
        predict=lambda params, mask: mixture_probability(*params, x[mask]),
    )  # fmt: skip
    w_test, d_test = won[test], days[test]
    evaluation = {k: summarize(p[test], w_test, d_test, rng) for k, p in predictions.items()}
    differences = {
        k: paired_difference(predictions[k][test], predictions["w=0"][test], w_test, d_test, rng)
        for k in ("w=1", "w estimado")
    }
    grid_rows = [
        {"w": float(w), "beta": float(b), "delta_ll": float(v - values.max())}
        for w, b, v in zip(W_GRID, betas, values)
    ]
    return {
        "b0_config": config,
        "dev_scores": dev_scores,
        "n_train": int(train.sum()),
        "train_first": str(data["date"][train].min().date()),
        "train_last": str(data["date"][train].max().date()),
        "w_hat": w_hat,
        "beta_at_w_hat": float(betas[values.argmax()]),
        "ci_profile": list(ci_profile),
        "ci_bootstrap_days": list(ci_boot),
        "rule": rule,
        "profile": grid_rows,
        "test_period": [str(PERIODS["test"][0]), str(data["date"][test].max().date())],
        "test_evaluation": evaluation,
        "test_difference_vs_w0": differences,
        "test_monthly_w": chosen_w,
        "test_calibration": favorite_calibration(predictions["w=0"][test], w_test),
    }


def _ci(values) -> str:
    return f"[{values[0]:.4f}; {values[1]:.4f}]"


def render_report(r: dict) -> str:
    lines = [
        "# H10: formato das partidas e avaliação aninhada do B0",
        "",
        "Gerado por `python -m backtest.h10_format` (não editar à mão). Protocolo em "
        "[protocolo_sessao_03.md](protocolo_sessao_03.md).",
        "",
        "## Escolha do B0 só no desenvolvimento (D23)",
        "",
        "| População/transformação | log loss no desenvolvimento |",
        "|---|---:|",
        *[f"| {k} | {v:.4f} |" for k, v in r["dev_scores"].items()],
        "",
        f"Escolhido: **{r['b0_config']['population']} / {r['b0_config']['transform']}**.",
        "",
        "## Fração de Bo1 (w)",
        "",
        f"{r['n_train']} partidas, {r['train_first']} a {r['train_last']}.",
        "",
        f"- Estimativa conjunta: **w = {r['w_hat']:.2f}**, beta = {r['beta_at_w_hat']:.4f}.",
        f"- IC 95% pelo perfil de verossimilhança: [{r['ci_profile'][0]:.2f}; "
        f"{r['ci_profile'][1]:.2f}].",
        f"- IC 95% por bootstrap de dias: [{r['ci_bootstrap_days'][0]:.2f}; "
        f"{r['ci_bootstrap_days'][1]:.2f}].",
        f"- Regra (intervalo mais largo = {r['rule']['width']:.2f}): **{r['rule']['mode']}**; "
        + ", ".join(f"w = {v['w']:.2f} com beta {v['beta']:.4f}" for v in r["rule"]["variants"])
        + ".",
        "",
        "### Perfil de verossimilhança",
        "",
        "| w | beta | log-verossimilhança menos o máximo |",
        "|---:|---:|---:|",
        *[
            f"| {row['w']:.2f} | {row['beta']:.4f} | {row['delta_ll']:.3f} |"
            for row in r["profile"][::10]
        ],
        "",
        "## Teste aninhado",
        "",
        f"{r['test_evaluation']['w=0']['n']} partidas, {r['test_period'][0]} a "
        f"{r['test_period'][1]}, walk-forward mensal, ambos no top 100. IC 95% por dias.",
        "",
        "| Modelo | log loss | IC 95% | Brier | IC 95% |",
        "|---|---:|---|---:|---|",
    ]
    for name, s in r["test_evaluation"].items():
        lines.append(
            f"| B0, {name} | {s['log_loss']:.4f} | {_ci(s['log_loss_ci'])} | {s['brier']:.4f} | "
            f"{_ci(s['brier_ci'])} |"
        )
    lines += [
        "",
        "| Diferença para w = 0 | log loss | IC 95% |",
        "|---|---:|---|",
        *[
            f"| {name} | {d['log_loss']:+.5f} | [{d['log_loss_ci'][0]:+.5f}; "
            f"{d['log_loss_ci'][1]:+.5f}] |"
            for name, d in r["test_difference_vs_w0"].items()
        ],
        "",
        "w escolhido em cada mês do teste: "
        + ", ".join(f"{w:.2f}" for w in r["test_monthly_w"])
        + ".",
        "",
        "## D21: calibração do favorito no teste (B0, w = 0)",
        "",
        "Wilson 95% (supõe partidas independentes).",
        "",
        "| Faixa | n | previsto | observado | IC 95% |",
        "|---|---:|---:|---:|---|",
    ]
    for row in r["test_calibration"]:
        if row["n"]:
            lines.append(
                f"| {row['faixa']} | {row['n']} | {row['previsto']:.1%} | "
                f"{row['observado']:.1%} | [{row['ic'][0]:.1%}; {row['ic'][1]:.1%}] |"
            )
        else:
            lines.append(f"| {row['faixa']} | 0 | - | - | - |")
    return "\n".join(lines) + "\n"


def main() -> int:
    if not MATCHES_PATH.exists():
        print(f"{MATCHES_PATH} não existe; rode: python -m ingest.vrs_matches")
        return 1
    result = analyze(rated_matches(pd.read_parquet(MATCHES_PATH)))
    PARAMS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = render_report(result)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
