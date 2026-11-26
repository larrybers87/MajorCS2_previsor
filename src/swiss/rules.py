"""Constantes e regras fixas da fase suíça.

Fonte: ``docs/major-supplemental-rulebook.md`` (ver ``docs/regras_suica.md`` para as
citações e para a separação entre o que é VERIFICADO e o que é HIPÓTESE).
"""

from __future__ import annotations

N_TEAMS = 16
N_ROUNDS = 5
WINS_TO_ADVANCE = 3
LOSSES_TO_ELIMINATE = 3
N_ADVANCING = 8

# Consequência aritmética do formato (16 times, sem empates, pareamento por cartel).
MATCHES_PER_ROUND = (8, 8, 8, 6, 3)

# Tamanho dos grupos de mesmo cartel por rodada, do melhor cartel para o pior.
GROUP_SIZES = {1: (16,), 2: (8, 8), 3: (4, 8, 4), 4: (6, 6), 5: (6,)}

# Ordem dos cartéis finais usada nas saídas (do melhor para o pior).
FINAL_RECORDS = ((3, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 3))
FINAL_RECORD_LABELS = tuple(f"{w}-{losses}" for w, losses in FINAL_RECORDS)
FINAL_RECORD_COUNTS = (2, 3, 3, 3, 3, 2)

# Rodada 1 ("Initial Swiss Match-ups"): pares de seeds iniciais.
ROUND_ONE_SEED_PAIRS = tuple((seed, seed + 8) for seed in range(1, 9))

# Rodadas 4 e 5 ("Swiss Bracket", tabela de prioridade). Os números são posições
# (1 = melhor ordenado) dentro do grupo de 6 times de mesmo cartel.
SIX_TEAM_PRIORITY = (
    ((1, 6), (2, 5), (3, 4)),
    ((1, 6), (2, 4), (3, 5)),
    ((1, 5), (2, 6), (3, 4)),
    ((1, 5), (2, 4), (3, 6)),
    ((1, 4), (2, 6), (3, 5)),
    ((1, 4), (2, 5), (3, 6)),
    ((1, 6), (2, 3), (4, 5)),
    ((1, 5), (2, 3), (4, 6)),
    ((1, 3), (2, 6), (4, 5)),
    ((1, 3), (2, 5), (4, 6)),
    ((1, 4), (2, 3), (5, 6)),
    ((1, 3), (2, 4), (5, 6)),
    ((1, 2), (3, 6), (4, 5)),
    ((1, 2), (3, 5), (4, 6)),
    ((1, 2), (3, 4), (5, 6)),
)

# Rodadas em que vale "melhor ordenado x pior ordenado disponível".
HIGH_LOW_ROUNDS = (2, 3)
# Rodadas em que vale a tabela de prioridade.
TABLE_ROUNDS = (4, 5)


def is_decider_match(wins: int, losses: int) -> bool:
    """Indica se uma partida entre times com cartel ``wins``-``losses`` é decisiva.

    Decisiva = vale classificação ou eliminação. Pelo rulebook ("Swiss Bracket"),
    essas partidas são Bo3 e as demais Bo1.
    """
    if not (0 <= wins < WINS_TO_ADVANCE and 0 <= losses < LOSSES_TO_ELIMINATE):
        raise ValueError(f"cartel {wins}-{losses} não corresponde a um time ainda ativo")
    return wins == WINS_TO_ADVANCE - 1 or losses == LOSSES_TO_ELIMINATE - 1


def best_of(wins: int, losses: int, all_best_of_three: bool = False) -> int:
    """Formato (1 ou 3) da partida entre times com cartel ``wins``-``losses``.

    ``all_best_of_three`` NÃO está no rulebook; existe para o caso de o Stage 3 ser
    todo em Bo3 (ver ``docs/duvidas_abertas.md``). O padrão segue o rulebook.
    """
    decider = is_decider_match(wins, losses)
    return 3 if (decider or all_best_of_three) else 1
