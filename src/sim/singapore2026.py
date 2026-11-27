"""Dados fixos do PGL Major Singapore 2026.

A atribuição dos times por stage veio do Larry, citando a Wikipedia (fonte
SECUNDÁRIA). ``THE ONE`` é o elenco da 1win e ``GOSH`` o da BC.Game no VRS (D15,
fechada pelo Larry com base na PGL e na imprensa). A ligação com o VRS é feita pelo
ELENCO (``ROSTERS``), nunca só pelo nome.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

SEEDING_SNAPSHOT = date(2026, 11, 2)
# Corte EXCLUSIVO da calibração. O VRS grava datas no fuso America/Los_Angeles
# (``model/report.js`` do repositório): partidas de 24/11 em Singapura podem aparecer
# como 23/11, então o dia 23 também fica de fora.
DATA_CUTOFF = date(2026, 11, 23)
# Commit do clone do VRS usado no modelo congelado (snapshot de 02/11/2026).
PINNED_VRS_COMMIT = "f8c55f250fdef796d708aa32814587932154fa04"


@dataclass(frozen=True)
class Entrant:
    name: str  # nome usado no evento e nas saídas
    stage: int  # stage em que entra
    vrs_name: str  # nome desse elenco no VRS de 02/11/2026 (informativo e apelido)
    aliases: tuple[str, ...] = ()


def _e(name, stage, vrs_name=None, *aliases) -> Entrant:
    return Entrant(name, stage, vrs_name or name, aliases)


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
    _e("GOSH", 1, "BC.Game"),
    _e("FlyQuest", 1),
    _e("Chinggis Warriors", 1, "Chinggis Warriors", "Chinggis"),
    _e("Lynn Vision", 1, "Lynn Vision", "Lynn Vision Gaming"),
    _e("FUT", 2, "FUT", "FUT Esports"),
    _e("The MongolZ", 2, "The MongolZ", "MongolZ"),
    _e("Nemiga", 2, "Nemiga", "Nemiga Gaming"),
    _e("Natus Vincere", 2, "Natus Vincere", "NaVi"),
    _e("G2", 2, "G2", "G2 Esports"),
    _e("THE ONE", 2, "1win"),
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


# Elencos no VRS de 02/11/2026. A identidade de um participante é o ELENCO (3 jogadores
# em comum), não o nome: o roster que o VRS chama de "the ONE" (#318) é outro time.
ROSTERS: dict[str, tuple[str, ...]] = {
    "PVISION": ("FL1T", "HObbit", "Jame", "xiELO", "zweih"),
    "Liquid": ("EliGE", "Jorko", "JT", "malbsMd", "NAF"),
    "NiP": ("adamb", "Krimbo", "sjuush", "stavn", "xKacpersky"),
    "HEROIC": ("Brollan", "Chr1zN", "MartinezSa", "nilo", "susp"),
    "FaZe": ("frozen", "JBOEN", "jcobbb", "Neityu", "Twistzz"),
    "100 Thieves": ("device", "Gizmy", "poiii", "rain", "sirah"),
    "Eternal Fire": ("jottAAA", "Kvem", "MisteM", "regali", "soulfly"),
    "M80": ("JBa", "Lake", "s1n", "slaxz-", "Swisher"),
    "9z": ("dgt", "HUASOPEEK", "luchov", "max", "meyern"),
    "DENDELE": ("doc", "gafolo", "koala", "maxxkor", "rdnzao"),
    "Imperial": ("chelo", "decenty", "noway", "saadzin", "VINI"),
    "Wildcard": ("Cxzi", "fr3nd", "HexT", "nEMANHA", "reck"),
    "GOSH": ("asap", "Magisk", "mzinho", "s1mple", "Senzu"),
    "FlyQuest": ("aliStair", "INS", "jks", "nettik", "Vexite"),
    "Chinggis Warriors": ("cool4st", "fury5k", "ROUX", "sk0R", "tikuak"),
    "Lynn Vision": ("C4LLM3SU3", "EmiliaQAQ", "Starry", "Westmelon", "z4KR"),
    "FUT": ("cmtry", "dem0n", "dziugss", "Krabeni", "xfl0ud"),
    "The MongolZ": ("910", "bLitz", "cobrazera", "nin9", "Techno"),
    "Nemiga": ("KaiR0N-", "khaN", "robo", "syph0", "Xant3r"),
    "Natus Vincere": ("Aleksib", "b1t", "iM", "makazze", "w0nderful"),
    "G2": ("HeavyGod", "huNter-", "MATYS", "NertZ", "r1nkle"),
    "THE ONE": ("ArtFr0st", "Ax1Le", "BELCHONOKK", "fame", "nafany"),
    "Astralis": ("jabbi", "phzy", "ryu", "siuhy", "Staehr"),
    "MIBR": ("insani", "LNZ", "nqz", "tomaszin", "venomzera"),
    "MOUZ": ("PR", "Spinx", "torzsi", "xelex", "xertioN"),
    "Vitality": ("flameZ", "jL", "mezii", "ropz", "ZywOo"),
    "Aurora": ("Jimpphat", "kyxsan", "Wicadia", "woxic", "XANTARES"),
    "Spirit": ("donk", "magixx", "sh1ro", "tN1R", "zont1x"),
    "BB Team": ("Boombl4", "d1Ledez", "Magnojez", "S1ren", "zorte"),
    "Falcons": ("karrigan", "kyousuke", "m0NESY", "NiKo", "TeSeS"),
    "FURIA": ("FalleN", "KSCERATO", "molodoy", "YEKINDAR", "yuurih"),
    "Legacy": ("arT", "dumau", "latto", "n1ssim", "try"),
}


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
