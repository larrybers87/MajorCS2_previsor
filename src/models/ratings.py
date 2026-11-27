"""B1: ratings que mudam a cada partida (Elo e Glicko-1), com identidade por elenco.

Definições em ``docs/protocolo_sessao_03.md``. Nenhuma previsão de um dia usa resultados
do próprio dia: as diferenças de rating são tiradas antes das atualizações.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

INITIAL_RATING = 1500.0
VRS_REFERENCE = 1000.0
PROVISIONAL_GAMES = 10
MIN_SHARED_PLAYERS = 3
_Q = math.log(10) / 400


@dataclass(frozen=True)
class Side:
    team: int  # identificador do ``TeamRegistry``
    points: float | None  # pontos VRS vigentes (snapshot anterior ao dia)


@dataclass(frozen=True)
class Game:
    a: Side
    b: Side
    a_won: bool


@dataclass(frozen=True)
class EloConfig:
    s: float  # peso do prior VRS
    k: float
    half_life: float | None  # dias; None = sem decaimento
    provisional: float  # multiplicador de K nas primeiras partidas

    @property
    def label(self) -> str:
        h = "sem" if self.half_life is None else f"{self.half_life:g}"
        return f"elo s={self.s:g} K={self.k:g} H={h} m={self.provisional:g}"


@dataclass(frozen=True)
class GlickoConfig:
    rd0: float
    c: float  # crescimento do RD por raiz de dia
    s: float

    @property
    def label(self) -> str:
        return f"glicko RD={self.rd0:g} c={self.c:g} s={self.s:g}"


def prior_rating(s: float, points: float | None) -> float:
    if points is None:
        return INITIAL_RATING
    return INITIAL_RATING + s * (points - VRS_REFERENCE)


class TeamRegistry:
    """Identifica times pelo elenco (3 jogadores em comum com o elenco mais recente)."""

    def __init__(self) -> None:
        self._rosters: list[frozenset[str]] = []
        self._names: list[str] = []
        self._by_player: dict[str, set[int]] = {}
        self._by_name: dict[str, int] = {}

    def find(self, name: str, roster: frozenset[str]) -> int | None:
        key = name.strip().casefold()
        if not roster:
            return self._by_name.get(key)
        candidates: set[int] = set()
        for player in roster:
            candidates |= self._by_player.get(player, set())
        scored = [
            (len(roster & self._rosters[i]), self._names[i] == key, i)
            for i in candidates
            if len(roster & self._rosters[i]) >= MIN_SHARED_PLAYERS
        ]
        return max(scored)[2] if scored else None

    def resolve(self, name: str, roster: frozenset[str]) -> int:
        """Como ``find``, criando o time se preciso e atualizando elenco e nome."""
        found = self.find(name, roster)
        if found is None:
            found = len(self._rosters)
            self._rosters.append(frozenset())
            self._names.append("")
        key = name.strip().casefold()
        self._names[found] = key
        self._by_name[key] = found
        if roster:
            for player in self._rosters[found] - roster:
                self._by_player[player].discard(found)
            self._rosters[found] = roster
            for player in roster:
                self._by_player.setdefault(player, set()).add(found)
        return found


def elo_expected(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(rating_a - rating_b) / 400))


class Elo:
    def __init__(self, config: EloConfig) -> None:
        self.config = config
        self._state: dict[int, tuple[float, date, int]] = {}  # rating, último dia, partidas

    def rating(self, side: Side, day: date) -> float:
        """Rating no início de ``day`` (com decaimento), sem alterar o estado."""
        prior = prior_rating(self.config.s, side.points)
        if side.team not in self._state:
            return prior
        value, last, _ = self._state[side.team]
        if self.config.half_life is None:
            return value
        factor = 0.5 ** ((day - last).days / self.config.half_life)
        return prior + (value - prior) * factor

    def process_day(self, day: date, games: Sequence[Game]) -> list[float]:
        """Devolve ``rating_a - rating_b`` de cada partida ANTES do dia e atualiza."""
        sides = {side.team: side for g in games for side in (g.a, g.b)}
        before = {team: self.rating(side, day) for team, side in sides.items()}
        played = {team: self._state.get(team, (0.0, day, 0))[2] for team in sides}
        delta = dict.fromkeys(sides, 0.0)
        count = dict.fromkeys(sides, 0)
        for g in games:
            expected = elo_expected(before[g.a.team], before[g.b.team])
            for team, score, exp in (
                (g.a.team, float(g.a_won), expected),
                (g.b.team, 1.0 - g.a_won, 1.0 - expected),
            ):
                k = self.config.k
                if played[team] + count[team] < PROVISIONAL_GAMES:
                    k *= self.config.provisional
                delta[team] += k * (score - exp)
                count[team] += 1
        for team in sides:
            self._state[team] = (before[team] + delta[team], day, played[team] + count[team])
        return [before[g.a.team] - before[g.b.team] for g in games]


def glicko_update(
    rating: float, rd: float, results: Sequence[tuple[float, float, float]]
) -> tuple[float, float]:
    """Um período Glicko-1. ``results``: (rating do adversário, RD dele, placar 0 ou 1)."""
    information, total = 0.0, 0.0
    for opponent, opponent_rd, score in results:
        g = 1.0 / math.sqrt(1 + 3 * _Q**2 * opponent_rd**2 / math.pi**2)
        expected = 1.0 / (1 + 10 ** (-g * (rating - opponent) / 400))
        information += _Q**2 * g**2 * expected * (1 - expected)
        total += g * (score - expected)
    precision = 1 / rd**2 + information
    return rating + _Q / precision * total, math.sqrt(1 / precision)


class Glicko:
    def __init__(self, config: GlickoConfig) -> None:
        self.config = config
        self._state: dict[int, tuple[float, float, date]] = {}  # rating, RD, último dia

    def _current(self, side: Side, day: date) -> tuple[float, float]:
        if side.team not in self._state:
            return prior_rating(self.config.s, side.points), self.config.rd0
        value, rd, last = self._state[side.team]
        grown = math.sqrt(rd**2 + self.config.c**2 * (day - last).days)
        return value, min(grown, self.config.rd0)

    def rating(self, side: Side, day: date) -> float:
        return self._current(side, day)[0]

    def process_day(self, day: date, games: Sequence[Game]) -> list[float]:
        sides = {side.team: side for g in games for side in (g.a, g.b)}
        now = {team: self._current(side, day) for team, side in sides.items()}
        differences = [now[g.a.team][0] - now[g.b.team][0] for g in games]
        for g in games:  # uma partida por período
            a, b = now[g.a.team], now[g.b.team]
            now[g.a.team] = glicko_update(*a, [(*b, float(g.a_won))])
            now[g.b.team] = glicko_update(*b, [(*a, 1.0 - g.a_won)])
        for team, (value, rd) in now.items():
            self._state[team] = (value, rd, day)
        return differences


def build_system(config: EloConfig | GlickoConfig) -> Elo | Glicko:
    return Elo(config) if isinstance(config, EloConfig) else Glicko(config)
