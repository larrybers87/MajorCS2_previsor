"""Dados fixos do PGL Major Singapore 2026.

A atribuição dos times por stage veio do Larry, citando a Wikipedia (fonte
SECUNDÁRIA). O nome no VRS de ``THE ONE`` e ``GOSH`` é HIPÓTESE (ver
``docs/duvidas_abertas.md``, D15): sem ela a ordem de convites por região do VRS é
violada.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

SEEDING_SNAPSHOT = date(2026, 11, 2)
# Início do Stage 1 segundo a imprensa; dados a partir daqui ficam fora da calibração.
DATA_CUTOFF = date(2026, 11, 24)


@dataclass(frozen=True)
class Entrant:
    name: str  # nome usado no evento e nas saídas
    stage: int  # stage em que entra
    vrs_name: str  # nome no VRS de 02/11/2026
    aliases: tuple[str, ...] = ()
    vrs_name_is_hypothesis: bool = False


def _e(name, stage, vrs_name=None, *aliases, hypothesis=False) -> Entrant:
    return Entrant(name, stage, vrs_name or name, aliases, hypothesis)


ENTRANTS: tuple[Entrant, ...] = (
    _e("PVISION", 1, "PARIVISION"),
    _e("Liquid", 1, "Liquid", "Team Liquid"),
    _e("NiP", 1, "Ninjas in Pyjamas"),
    _e("HEROIC", 1),
    _e("FaZe", 1, "FaZe", "FaZe Clan"),
    _e("100 Thieves", 1, "100 Thieves", "100T"),
    _e("Eternal Fire", 1),
    _e("M80", 1),
    _e("9z", 1, "9z", "9z Team"),
    _e("DENDELE", 1),
    _e("Imperial", 1, "Imperial", "Imperial Esports"),
    _e("Wildcard", 1),
    _e("GOSH", 1, "BC.Game", hypothesis=True),
    _e("FlyQuest", 1),
    _e("Chinggis Warriors", 1, "Chinggis Warriors", "Chinggis"),
    _e("Lynn Vision", 1, "Lynn Vision", "Lynn Vision Gaming"),
    _e("FUT", 2, "FUT", "FUT Esports"),
    _e("The MongolZ", 2, "The MongolZ", "MongolZ"),
    _e("Nemiga", 2, "Nemiga", "Nemiga Gaming"),
    _e("Natus Vincere", 2, "Natus Vincere", "NaVi"),
    _e("G2", 2, "G2", "G2 Esports"),
    _e("THE ONE", 2, "1win", hypothesis=True),
    _e("Astralis", 2),
    _e("MIBR", 2),
    _e("MOUZ", 3),
    _e("Vitality", 3, "Vitality", "Team Vitality"),
    _e("Aurora", 3, "Aurora", "Aurora Gaming"),
    _e("Spirit", 3, "Spirit", "Team Spirit"),
    _e("BB Team", 3, "BETBOOM", "BB", "BetBoom Team"),
    _e("Falcons", 3, "Falcons", "Team Falcons"),
    _e("FURIA", 3, "FURIA", "FURIA Esports"),
    _e("Legacy", 3),
)


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for entrant in ENTRANTS:
        for alias in (entrant.name, entrant.vrs_name, *entrant.aliases):
            previous = index.setdefault(_key(alias), entrant.name)
            if previous != entrant.name:
                raise ValueError(f"apelido {alias!r} ambíguo: {previous} e {entrant.name}")
    return index


_ALIASES = _alias_index()


def canonical_name(text: str) -> str:
    """Converte um nome de time (qualquer apelido conhecido) no nome usado no evento."""
    try:
        return _ALIASES[_key(text)]
    except KeyError:
        known = ", ".join(sorted(e.name for e in ENTRANTS))
        raise ValueError(f"time desconhecido: {text!r}. Times do Major: {known}") from None
