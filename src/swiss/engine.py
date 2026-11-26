"""Funções puras e determinísticas da fase suíça (implementação de referência).

``swiss.simulate`` tem uma versão vetorizada do emparelhamento; os testes comparam
as duas.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .rules import (
    LOSSES_TO_ELIMINATE,
    MATCHES_PER_ROUND,
    N_ADVANCING,
    N_ROUNDS,
    ROUND_ONE_SEED_PAIRS,
    SIX_TEAM_PRIORITY,
    TABLE_ROUNDS,
    WINS_TO_ADVANCE,
    best_of,
)
from .state import Match, StageState


class NoValidPairingError(RuntimeError):
    """Não existe emparelhamento sem rematch.

    O rulebook diz "if possible" e não define o que fazer quando é impossível; em vez
    de inventar uma regra, a engine interrompe.
    """


@dataclass(frozen=True)
class Pairing:
    """Emparelhamento gerado pela engine. ``team_a`` é o melhor ordenado na rodada."""

    team_a: str
    team_b: str
    best_of: int

    @property
    def pair(self) -> frozenset[str]:
        return frozenset((self.team_a, self.team_b))


@dataclass(frozen=True)
class PairingMismatch:
    """Divergência entre as partidas registradas numa rodada e as da engine."""

    round: int
    expected: tuple[frozenset[str], ...]
    actual: tuple[frozenset[str], ...]


def records(state: StageState) -> dict[str, tuple[int, int]]:
    """Cartel (vitórias, derrotas) de cada time, considerando as partidas decididas."""
    wins = dict.fromkeys(state.names, 0)
    losses = dict.fromkeys(state.names, 0)
    for match in state.matches:
        if match.winner is None:
            continue
        loser = match.team_b if match.winner == match.team_a else match.team_a
        wins[match.winner] += 1
        losses[loser] += 1
    return {name: (wins[name], losses[name]) for name in state.names}


def buchholz(state: StageState) -> dict[str, int]:
    """Difficulty Score: soma de (vitórias - derrotas) atuais dos adversários enfrentados.

    Só partidas decididas contam como "enfrentadas".
    """
    current = records(state)
    scores = dict.fromkeys(state.names, 0)
    for match in state.matches:
        if match.winner is None:
            continue
        for team, opponent in ((match.team_a, match.team_b), (match.team_b, match.team_a)):
            wins, losses = current[opponent]
            scores[team] += wins - losses
    return scores


def standings(state: StageState) -> list[str]:
    """Times ordenados pelo "Mid-stage Seed Calculation".

    1) cartel (mais vitórias, depois menos derrotas); 2) Buchholz maior;
    3) seed inicial do stage.
    """
    current = records(state)
    scores = buchholz(state)
    return sorted(
        state.names,
        key=lambda n: (-current[n][0], current[n][1], -scores[n], state.seed_of(n)),
    )


def current_round(state: StageState) -> int | None:
    """Primeira rodada ainda não completa e decidida; ``None`` se o stage terminou."""
    for round_number in range(1, N_ROUNDS + 1):
        decided = sum(m.decided for m in state.round_matches(round_number))
        if decided < MATCHES_PER_ROUND[round_number - 1]:
            return round_number
    return None


def pair_round(state: StageState) -> list[Pairing]:
    """Emparelhamentos da rodada atual segundo o rulebook.

    Usa somente as rodadas anteriores: resultados parciais da própria rodada e
    partidas já anunciadas são ignorados. Retorna lista vazia se o stage terminou.
    """
    round_number = current_round(state)
    if round_number is None:
        return []
    history = state.before_round(round_number)

    if round_number == 1:
        by_seed = {team.seed: team.name for team in history.teams}
        return [
            Pairing(by_seed[a], by_seed[b], best_of(0, 0, state.all_best_of_three))
            for a, b in ROUND_ONE_SEED_PAIRS
        ]

    current = records(history)
    ordered = standings(history)
    played = {m.pair for m in history.matches}
    groups: dict[tuple[int, int], list[str]] = {}
    for name in ordered:
        wins, losses = current[name]
        if wins < WINS_TO_ADVANCE and losses < LOSSES_TO_ELIMINATE:
            groups.setdefault((wins, losses), []).append(name)

    pairings: list[Pairing] = []
    for (wins, losses), group in groups.items():
        if round_number in TABLE_ROUNDS:
            pairs = _pair_by_table(group, played)
        else:
            pairs = _pair_high_low(group, played)
        if pairs is None:
            raise NoValidPairingError(
                f"rodada {round_number}, grupo {wins}-{losses}: não há emparelhamento "
                f"sem rematch para {group}"
            )
        fmt = best_of(wins, losses, state.all_best_of_three)
        pairings.extend(Pairing(a, b, fmt) for a, b in pairs)
    return pairings


def _pair_high_low(
    group: Sequence[str], played: set[frozenset[str]]
) -> list[tuple[str, str]] | None:
    """Rodadas 2 e 3: o melhor ordenado enfrenta o pior ordenado sem rematch.

    HIPÓTESE H1 (docs/duvidas_abertas.md): se essa escolha gulosa deixar os times
    restantes sem emparelhamento possível, volta-se atrás e tenta-se o próximo pior.
    O rulebook não descreve esse caso.
    """
    if not group:
        return []
    top, rest = group[0], group[1:]
    for index in range(len(rest) - 1, -1, -1):
        opponent = rest[index]
        if frozenset((top, opponent)) in played:
            continue
        remaining = _pair_high_low([*rest[:index], *rest[index + 1 :]], played)
        if remaining is not None:
            return [(top, opponent), *remaining]
    return None


def _pair_by_table(
    group: Sequence[str], played: set[frozenset[str]]
) -> list[tuple[str, str]] | None:
    """Rodadas 4 e 5: primeira linha da tabela de prioridade sem rematch."""
    if len(group) != 6:
        raise ValueError(f"a tabela de prioridade exige grupos de 6 times, recebidos {len(group)}")
    for row in SIX_TEAM_PRIORITY:
        pairs = [(group[a - 1], group[b - 1]) for a, b in row]
        if all(frozenset(p) not in played for p in pairs):
            return pairs
    return None


def announce_pairings(state: StageState, pairs: Sequence[tuple[str, str]]) -> StageState:
    """Registra o emparelhamento oficial completo da rodada atual, ainda sem resultados.

    Serve para tratar o chaveamento publicado como fato, mesmo que difira da engine.
    """
    round_number = current_round(state)
    if round_number is None:
        raise ValueError("o stage já terminou")
    if state.round_matches(round_number):
        raise ValueError(f"a rodada {round_number} já tem partidas registradas")
    expected = MATCHES_PER_ROUND[round_number - 1]
    if len(pairs) != expected:
        raise ValueError(f"a rodada {round_number} exige {expected} partidas, recebidas {len(pairs)}")
    new = tuple(Match(round_number, a, b) for a, b in pairs)
    return state.with_matches(state.matches + new)


def apply_results(state: StageState, results: Iterable[tuple[str, str]]) -> StageState:
    """Aplica resultados ``(vencedor, perdedor)``, em ordem cronológica de rodadas.

    Cada resultado é aplicado à rodada atual: preenche uma partida anunciada ou, se a
    rodada não está totalmente anunciada, precisa constar no emparelhamento da engine.
    """
    for winner, loser in results:
        round_number = current_round(state)
        if round_number is None:
            raise ValueError("o stage já terminou")
        pair = frozenset((winner, loser))
        listed = state.round_matches(round_number)
        existing = next((m for m in listed if m.pair == pair), None)
        if existing is not None:
            if existing.decided:
                raise ValueError(f"resultado de {winner!r} x {loser!r} já registrado")
            updated = Match(round_number, existing.team_a, existing.team_b, winner)
            state = state.with_matches(updated if m == existing else m for m in state.matches)
            continue
        if len(listed) == MATCHES_PER_ROUND[round_number - 1]:
            raise ValueError(
                f"{winner!r} x {loser!r} não está entre as partidas anunciadas da "
                f"rodada {round_number}"
            )
        expected = next((p for p in pair_round(state) if p.pair == pair), None)
        if expected is None:
            raise ValueError(
                f"{winner!r} x {loser!r} não está no emparelhamento da engine para a rodada "
                f"{round_number}; se for o confronto oficial, use announce_pairings"
            )
        new = Match(round_number, expected.team_a, expected.team_b, winner)
        state = state.with_matches((*state.matches, new))
    return state


def check_pairings(state: StageState) -> list[PairingMismatch]:
    """Compara, rodada a rodada, as partidas registradas com as da engine (validação V2).

    Rodadas completas precisam coincidir como conjunto de pares; rodadas parciais
    precisam estar contidas no emparelhamento da engine. A ordem A/B não é comparada.
    """
    mismatches: list[PairingMismatch] = []
    for round_number in range(1, N_ROUNDS + 1):
        listed = state.round_matches(round_number)
        if not listed:
            break
        expected = {p.pair for p in pair_round(state.before_round(round_number))}
        actual = {m.pair for m in listed}
        complete = len(listed) == MATCHES_PER_ROUND[round_number - 1]
        if (actual != expected) if complete else not actual <= expected:
            mismatches.append(
                PairingMismatch(
                    round_number,
                    tuple(sorted(expected, key=sorted)),
                    tuple(sorted(actual, key=sorted)),
                )
            )
    return mismatches


def advancing_teams(state: StageState) -> list[str]:
    """Os 8 classificados de um stage encerrado, na ordem do seed final.

    No stage seguinte eles são os seeds 9 a 16, nesta ordem (HIPÓTESE H3).
    """
    if current_round(state) is not None:
        raise ValueError("o stage ainda não terminou")
    return standings(state)[:N_ADVANCING]
