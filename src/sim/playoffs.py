"""Playoffs (eliminação simples com 8 times) e simulação do Stage 3 até o título.

Do rulebook ("Single Elimination Bracket" e "Stage Seeding"):

* os 8 primeiros do Stage 3, com o seed final dele (cartel, Difficulty, seed inicial);
* quartas: chave A com 1v8 e 4v5; chave B com 2v7 e 3v6.

HIPÓTESE H7: cada semifinal reúne os vencedores da mesma chave, a final reúne os das
duas chaves e não há reordenação de seeds. A disputa de 3º lugar (perdedores das
semifinais) e os formatos vêm de ``sim.format_config``.

``prob_fn(team_a, team_b, best_of)`` recebe como ``team_a`` o melhor seed (H9).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from swiss import ProbFn, StageState
from swiss.rules import FINAL_RECORDS, N_ADVANCING, N_TEAMS
from swiss.simulate import final_order, probability_table, simulate_chunk

from .format_config import DEFAULT_FORMAT, TournamentFormat

# Pares de seeds das quartas, em ordem: QF1 e QF2 (chave A), QF3 e QF4 (chave B).
QUARTERFINALS = ((1, 8), (4, 5), (2, 7), (3, 6))
# Cada jogo posterior é alimentado por dois anteriores: (nome, origem a, origem b, tipo).
LATER_MATCHES = (
    ("SF1", "QF1", "QF2", "winner"),
    ("SF2", "QF3", "QF4", "winner"),
    ("3º", "SF1", "SF2", "loser"),
    ("Final", "SF1", "SF2", "winner"),
)
# Colocações contadas, na ordem das colunas de ``placing_counts``.
PLACINGS = ("campeão", "vice", "3º", "4º", "semifinal (3º-4º)", "quartas (5º-8º)")
STAGES_REACHED = ("quartas", "semifinal", "final", "título")


@dataclass(frozen=True)
class PlayoffMatch:
    name: str
    seed_a: int
    seed_b: int
    team_a: str
    team_b: str
    best_of: int
    winner: str | None = None


def match_names(fmt: TournamentFormat) -> list[str]:
    names = [f"QF{i}" for i in range(1, 5)] + [name for name, *_ in LATER_MATCHES]
    return names if fmt.third_place_match else [n for n in names if n != "3º"]


def match_best_of(name: str, fmt: TournamentFormat) -> int:
    if name == "Final":
        return fmt.final_best_of
    if name == "3º":
        return fmt.third_place_best_of
    return fmt.playoff_best_of


def bracket(
    names_by_seed: Sequence[str],
    results: Mapping[frozenset[str], str] | None = None,
    fmt: TournamentFormat = DEFAULT_FORMAT,
) -> list[PlayoffMatch]:
    """Jogos já definidos pelos resultados conhecidos (``{par: vencedor}``).

    Um jogo só aparece quando os dois participantes são conhecidos. Um resultado cujo
    confronto não existe na chave é um erro.
    """
    _check_names(names_by_seed)
    results = dict(results or {})
    seed = {name: i for i, name in enumerate(names_by_seed, start=1)}
    played: dict[str, PlayoffMatch] = {}

    def add(name: str, first: str, second: str) -> None:
        a, b = sorted((first, second), key=seed.__getitem__)
        winner = results.pop(frozenset((a, b)), None)
        if winner is not None and winner not in (a, b):
            raise ValueError(f"vencedor {winner!r} não joga {a} x {b}")
        played[name] = PlayoffMatch(
            name, seed[a], seed[b], a, b, match_best_of(name, fmt), winner
        )

    for i, (high, low) in enumerate(QUARTERFINALS, start=1):
        add(f"QF{i}", names_by_seed[high - 1], names_by_seed[low - 1])
    wanted = match_names(fmt)
    for name, source_a, source_b, kind in LATER_MATCHES:
        if name not in wanted:
            continue
        sources = [played.get(source_a), played.get(source_b)]
        if any(m is None or m.winner is None for m in sources):
            continue
        teams = [
            m.winner if kind == "winner" else (m.team_b if m.winner == m.team_a else m.team_a)
            for m in sources
        ]
        add(name, *teams)
    if results:
        unknown = ", ".join(" x ".join(sorted(pair)) for pair in results)
        raise ValueError(f"resultados fora da chave: {unknown}")
    return list(played.values())


def _check_names(names_by_seed: Sequence[str]) -> None:
    if len(names_by_seed) != N_ADVANCING or len(set(names_by_seed)) != N_ADVANCING:
        raise ValueError("os playoffs têm 8 times distintos, em ordem de seed")


def _playoff_table(prob_fn: ProbFn, names: Sequence[str], formats: set[int]) -> dict:
    """``{formato: matriz P(linha vence coluna)}``."""
    tables = {}
    for best_of in formats:
        table = np.full((len(names), len(names)), np.nan)
        for i, a in enumerate(names):
            for j, b in enumerate(names):
                if i != j:
                    p = float(prob_fn(a, b, best_of))
                    if not 0.0 <= p <= 1.0:
                        raise ValueError(f"prob_fn({a!r}, {b!r}, {best_of}) = {p}")
                    table[i, j] = p
        tables[best_of] = table
    return tables


def simulate_bracket(
    tables: Mapping[int, np.ndarray],
    ids: np.ndarray,
    rng: np.random.Generator,
    fmt: TournamentFormat = DEFAULT_FORMAT,
    fixed: np.ndarray | None = None,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Joga a chave em lote. ``ids[n, k]`` = índice do time com seed k+1 nos playoffs.

    ``fixed[a, b]`` verdadeiro significa que ``a`` já venceu ``b`` (fato). Devolve, por
    jogo, ``(vencedor, perdedor)`` como posições de seed (0..7).
    """
    n = ids.shape[0]
    rows = np.arange(n)
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    def play(name: str, x: np.ndarray, y: np.ndarray) -> None:
        a, b = np.minimum(x, y), np.maximum(x, y)  # a = melhor seed
        team_a, team_b = ids[rows, a], ids[rows, b]
        a_wins = rng.random(n) < tables[match_best_of(name, fmt)][team_a, team_b]
        if fixed is not None:
            a_wins = np.where(fixed[team_a, team_b], True, a_wins)
            a_wins = np.where(fixed[team_b, team_a], False, a_wins)
        out[name] = (np.where(a_wins, a, b), np.where(a_wins, b, a))

    for i, (high, low) in enumerate(QUARTERFINALS, start=1):
        play(f"QF{i}", np.full(n, high - 1), np.full(n, low - 1))
    wanted = match_names(fmt)
    for name, source_a, source_b, kind in LATER_MATCHES:
        if name in wanted:
            side = 0 if kind == "winner" else 1
            play(name, out[source_a][side], out[source_b][side])
    return out


def _count_placings(
    played: Mapping[str, tuple[np.ndarray, np.ndarray]],
    ids: np.ndarray,
    placing_counts: np.ndarray,
    fmt: TournamentFormat,
) -> None:
    rows = np.arange(ids.shape[0])
    total = placing_counts.shape[0]

    def add(label: str, position: np.ndarray) -> None:
        column = PLACINGS.index(label)
        placing_counts[:, column] += np.bincount(ids[rows, position], minlength=total)

    add("campeão", played["Final"][0])
    add("vice", played["Final"][1])
    if fmt.third_place_match:
        add("3º", played["3º"][0])
        add("4º", played["3º"][1])
    else:
        for semifinal in ("SF1", "SF2"):
            add("semifinal (3º-4º)", played[semifinal][1])
    for i in range(1, 5):
        add("quartas (5º-8º)", played[f"QF{i}"][1])


@dataclass(frozen=True)
class PlayoffResult:
    """Contagens por time. Linhas na ordem de ``teams``."""

    teams: tuple[str, ...]
    n_sims: int
    placing_counts: np.ndarray  # (times, len(PLACINGS))

    def placing_probabilities(self) -> dict[str, dict[str, float]]:
        probs = self.placing_counts / self.n_sims
        return {t: dict(zip(PLACINGS, map(float, probs[i]))) for i, t in enumerate(self.teams)}

    def reach_probabilities(self) -> dict[str, dict[str, float]]:
        """P de chegar às quartas, à semifinal, à final e de ser campeão."""
        out = {}
        for team, p in self.placing_probabilities().items():
            champion = p["campeão"]
            final = champion + p["vice"]
            semifinal = final + p["3º"] + p["4º"] + p["semifinal (3º-4º)"]
            quarterfinal = semifinal + p["quartas (5º-8º)"]
            out[team] = dict(zip(STAGES_REACHED, (quarterfinal, semifinal, final, champion)))
        return out


def _fixed_matrix(names: Sequence[str], results: Mapping[frozenset[str], str]) -> np.ndarray:
    index = {name: i for i, name in enumerate(names)}
    fixed = np.zeros((len(names), len(names)), dtype=bool)
    for pair, winner in results.items():
        (loser,) = pair - {winner}
        fixed[index[winner], index[loser]] = True
    return fixed


def simulate_playoffs(
    prob_fn: ProbFn,
    names_by_seed: Sequence[str],
    n_sims: int,
    rng: np.random.Generator,
    results: Mapping[frozenset[str], str] | None = None,
    fmt: TournamentFormat = DEFAULT_FORMAT,
) -> PlayoffResult:
    """Simula o restante dos playoffs; ``results`` são fatos validados contra a chave."""
    if n_sims <= 0:
        raise ValueError("n_sims deve ser positivo")
    bracket(names_by_seed, results, fmt)  # valida times e resultados
    formats = {match_best_of(name, fmt) for name in match_names(fmt)}
    tables = _playoff_table(prob_fn, names_by_seed, formats)
    ids = np.tile(np.arange(N_ADVANCING), (n_sims, 1))
    fixed = _fixed_matrix(names_by_seed, results or {})
    played = simulate_bracket(tables, ids, rng, fmt, fixed)
    counts = np.zeros((N_ADVANCING, len(PLACINGS)), dtype=np.int64)
    _count_placings(played, ids, counts, fmt)
    return PlayoffResult(tuple(names_by_seed), n_sims, counts)


@dataclass(frozen=True)
class Stage3Result:
    """Stage 3 e playoffs juntos. Linhas na ordem de seed inicial do Stage 3."""

    teams: tuple[str, ...]
    n_sims: int
    record_counts: np.ndarray  # (16, 6)
    position_counts: np.ndarray  # (16, 16), posição final na suíça
    playoffs: PlayoffResult


def simulate_stage3(
    prob_fn: ProbFn,
    stage3: StageState,
    n_sims: int,
    rng: np.random.Generator,
    fmt: TournamentFormat = DEFAULT_FORMAT,
    chunk_size: int = 50_000,
) -> Stage3Result:
    """Em cada simulação, os 8 primeiros do Stage 3 jogam os playoffs.

    ``stage3`` traz os fatos já conhecidos do stage suíço e o formato dele. Resultados
    reais de playoffs só existem com o Stage 3 encerrado: use ``simulate_playoffs``.
    """
    if n_sims <= 0 or chunk_size <= 0:
        raise ValueError("n_sims e chunk_size devem ser positivos")
    swiss_table = probability_table(prob_fn, stage3.names, stage3.all_best_of_three)
    formats = {match_best_of(name, fmt) for name in match_names(fmt)}
    tables = _playoff_table(prob_fn, stage3.names, formats)
    records = np.zeros((N_TEAMS, len(FINAL_RECORDS)), dtype=np.int64)
    positions = np.zeros((N_TEAMS, N_TEAMS), dtype=np.int64)
    placings = np.zeros((N_TEAMS, len(PLACINGS)), dtype=np.int64)

    remaining = n_sims
    while remaining:
        n = min(chunk_size, remaining)
        remaining -= n
        wins, losses, played = simulate_chunk(swiss_table, stage3, n, rng)
        for column, (w, l_) in enumerate(FINAL_RECORDS):
            records[:, column] += ((wins == w) & (losses == l_)).sum(axis=0)
        order = final_order(wins, losses, played)
        for position in range(N_TEAMS):
            positions[:, position] += np.bincount(order[:, position], minlength=N_TEAMS)
        ids = order[:, :N_ADVANCING]
        _count_placings(simulate_bracket(tables, ids, rng, fmt), ids, placings, fmt)

    return Stage3Result(
        stage3.names, n_sims, records, positions, PlayoffResult(stage3.names, n_sims, placings)
    )
