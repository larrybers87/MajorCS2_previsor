"""Estado imutável de um stage suíço."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .rules import LOSSES_TO_ELIMINATE, MATCHES_PER_ROUND, N_ROUNDS, N_TEAMS, WINS_TO_ADVANCE


@dataclass(frozen=True)
class Team:
    """Time e seu seed inicial no stage (1 = melhor)."""

    name: str
    seed: int


@dataclass(frozen=True)
class Match:
    """Partida (série) de um stage. ``winner=None`` indica partida anunciada e não decidida."""

    round: int
    team_a: str
    team_b: str
    winner: str | None = None

    @property
    def decided(self) -> bool:
        return self.winner is not None

    @property
    def pair(self) -> frozenset[str]:
        return frozenset((self.team_a, self.team_b))


@dataclass(frozen=True)
class StageState:
    """Times, seeds iniciais e partidas (jogadas ou anunciadas) de um stage.

    Cartéis e Buchholz são derivados das partidas (ver ``swiss.engine``).

    As partidas são tratadas como fatos: não se exige que coincidam com o que a engine
    emparelharia (use ``check_pairings`` para isso), mas elas precisam ser coerentes
    com o formato (mesmo cartel, uma partida por time por rodada, rodadas em ordem).

    ``all_best_of_three`` não está no rulebook; ver ``rules.best_of``.
    """

    teams: tuple[Team, ...]
    matches: tuple[Match, ...] = ()
    all_best_of_three: bool = False

    def __post_init__(self) -> None:
        teams = tuple(sorted(self.teams, key=lambda team: team.seed))
        object.__setattr__(self, "teams", teams)
        object.__setattr__(
            self, "matches", tuple(sorted(self.matches, key=lambda match: match.round))
        )
        _validate_teams(teams)
        _validate_matches(teams, self.matches)

    @classmethod
    def new(cls, names_by_seed: Sequence[str], all_best_of_three: bool = False) -> StageState:
        """Cria um stage sem partidas; ``names_by_seed[0]`` é o seed 1."""
        teams = tuple(Team(name, seed) for seed, name in enumerate(names_by_seed, start=1))
        return cls(teams=teams, all_best_of_three=all_best_of_three)

    @property
    def names(self) -> tuple[str, ...]:
        """Nomes em ordem de seed inicial."""
        return tuple(team.name for team in self.teams)

    def seed_of(self, name: str) -> int:
        for team in self.teams:
            if team.name == name:
                return team.seed
        raise KeyError(name)

    def round_matches(self, round_number: int) -> tuple[Match, ...]:
        return tuple(m for m in self.matches if m.round == round_number)

    def before_round(self, round_number: int) -> StageState:
        """Estado contendo apenas as rodadas anteriores a ``round_number``."""
        kept = tuple(m for m in self.matches if m.round < round_number)
        return StageState(self.teams, kept, self.all_best_of_three)

    def with_matches(self, matches: Iterable[Match]) -> StageState:
        return StageState(self.teams, tuple(matches), self.all_best_of_three)


def _validate_teams(teams: tuple[Team, ...]) -> None:
    if len(teams) != N_TEAMS:
        raise ValueError(f"um stage suíço tem {N_TEAMS} times, recebidos {len(teams)}")
    if [t.seed for t in teams] != list(range(1, N_TEAMS + 1)):
        raise ValueError("os seeds iniciais devem ser exatamente 1..16, sem repetição")
    if len({t.name for t in teams}) != N_TEAMS:
        raise ValueError("há nomes de times repetidos")


def _validate_matches(teams: tuple[Team, ...], matches: tuple[Match, ...]) -> None:
    wins = {t.name: 0 for t in teams}
    losses = {t.name: 0 for t in teams}
    previous_complete = True
    last_round = max((m.round for m in matches), default=0)
    for match in matches:
        if not 1 <= match.round <= N_ROUNDS:
            raise ValueError(f"rodada inválida: {match.round}")

    for round_number in range(1, last_round + 1):
        in_round = [m for m in matches if m.round == round_number]
        if not previous_complete:
            raise ValueError(
                f"há partidas na rodada {round_number} ou posterior, mas a rodada "
                f"{round_number - 1} não está completa e decidida"
            )
        expected = MATCHES_PER_ROUND[round_number - 1]
        if len(in_round) > expected:
            raise ValueError(f"rodada {round_number} tem mais de {expected} partidas")
        seen: set[str] = set()
        for m in in_round:
            for name in (m.team_a, m.team_b):
                if name not in wins:
                    raise ValueError(f"time desconhecido: {name!r}")
                if name in seen:
                    raise ValueError(f"{name!r} aparece duas vezes na rodada {round_number}")
                seen.add(name)
                if wins[name] >= WINS_TO_ADVANCE or losses[name] >= LOSSES_TO_ELIMINATE:
                    raise ValueError(f"{name!r} já encerrou o stage antes da rodada {round_number}")
            if m.team_a == m.team_b:
                raise ValueError(f"partida de {m.team_a!r} contra si mesmo")
            if (wins[m.team_a], losses[m.team_a]) != (wins[m.team_b], losses[m.team_b]):
                raise ValueError(
                    f"rodada {round_number}: {m.team_a!r} e {m.team_b!r} têm cartéis diferentes"
                )
            if m.winner is not None and m.winner not in (m.team_a, m.team_b):
                raise ValueError(f"vencedor {m.winner!r} não participa da partida")
        for m in in_round:
            if m.winner is not None:
                loser = m.team_b if m.winner == m.team_a else m.team_a
                wins[m.winner] += 1
                losses[loser] += 1
        previous_complete = len(in_round) == expected and all(m.decided for m in in_round)
