# Avaliação do Stage 1 (diagnóstico)

Gerado por `python -m backtest.v3_evaluation` (não editar à mão).

## Leia antes dos números

- **Não existe previsão commitada antes do primeiro jogo do Stage 1** (24/11). O primeiro commit do projeto é de 26/11. Nenhuma previsão retroativa foi criada aqui: só são lidas probabilidades que já estavam no git.
- **Retrospectivo** (rodadas 1 a 4 e cartéis): gerado **depois** dos jogos. O B0 usa só o VRS de 02/11 e beta calibrado até 01/11, mas isto **não é teste prospectivo**.
- **Prévio** (rodada 5): 3 partidas enviadas ao GitHub em 2026-11-27T00:14:53Z, antes do início (2026-11-27T06:00:00Z). É previsão de verdade, mas com n = 3.
- As duas partes usam variantes diferentes do B0 (w=0 no retrospectivo; média de w=0 e w=1 no prévio) e **não são somadas**.
- Com n = 30 (ou 33) isto é **diagnóstico**. Não ordena modelos, e as partidas e os times de um torneio não são independentes.
- O log loss do B1 e da média B0/B1 neste Major **não** foi calculado (reservado à checagem pré-registrada do Stage 3).

## Por partida

| Conjunto | n | log loss | Brier | Favorito venceu |
|---|---|---|---|---|
| Retrospectivo, rodadas 1-4 | 30 | 0.6734 (EP 0.023) | 0.2404 | 19/30 |
| Retrospectivo, só Bo1 | 20 | 0.6882 (EP 0.029) | 0.2476 | 11/20 |
| Retrospectivo, só Bo3 | 10 | 0.6440 (EP 0.036) | 0.2259 | 8/10 |
| Prévio, rodada 5 | 3 | 0.8405 (EP 0.174) | 0.3190 | 2/3 |
| Referência 50% | - | 0.6931 | 0.2500 | - |

A vantagem sobre os 50% no retrospectivo é menor que um erro padrão. Na rodada 5, o favorito mais claro (HEROIC) perdeu, o que domina a média de 3 partidas.

## Os 8 classificados (previsão desde a rodada 1, retrospectiva)

- Entre os 8 com maior P(avançar), **5 de 8** avançaram (ao acaso, o esperado é 4).
- Brier de avançar: 0.2495 (sem informação: 0.2500).
- Log score do cartel final: soma 28.108, média 1.7567. Sem informação (frequência de cada cartel no formato): soma 28.405, média 1.7753. Menor é melhor.
- A soma das marginais não é o log score da distribuição conjunta.

| Seed | Time | P(avançar) | Entre os 8 | Cartel | P(cartel) | log score | sem informação |
|---|---|---|---|---|---|---|---|
| 1 | NiP | 62.3% | sim | 3-0 | 17.6% | 1.735 | 2.079 |
| 2 | PVISION | 61.8% | sim | 3-1 | 23.5% | 1.448 | 1.674 |
| 3 | HEROIC | 60.6% | sim | 2-3 | 16.8% | 1.786 | 1.674 |
| 4 | FaZe | 59.6% | sim | 1-3 | 15.1% | 1.892 | 1.674 |
| 5 | Liquid | 58.8% | sim | 3-1 | 22.0% | 1.515 | 1.674 |
| 6 | Eternal Fire | 57.0% | sim | 3-1 | 21.4% | 1.542 | 1.674 |
| 7 | 100 Thieves | 57.5% | sim | 3-2 | 20.1% | 1.604 | 1.674 |
| 8 | 9z | 55.1% | sim | 1-3 | 16.8% | 1.783 | 1.674 |
| 9 | M80 | 52.3% | não | 2-3 | 18.2% | 1.702 | 1.674 |
| 10 | DENDELE | 50.1% | não | 0-3 | 12.1% | 2.109 | 2.079 |
| 11 | Imperial | 44.6% | não | 3-2 | 18.3% | 1.697 | 1.674 |
| 12 | Wildcard | 43.0% | não | 2-3 | 20.3% | 1.593 | 1.674 |
| 13 | GOSH | 37.9% | não | 0-3 | 17.8% | 1.725 | 2.079 |
| 14 | FlyQuest | 36.1% | não | 3-0 | 7.2% | 2.635 | 2.079 |
| 15 | Chinggis Warriors | 31.9% | não | 1-3 | 25.5% | 1.367 | 1.674 |
| 16 | Lynn Vision | 31.5% | não | 3-2 | 13.9% | 1.976 | 1.674 |

## Partidas: prévio (rodada 5)

| R | Partida | Formato | P(A vence) | Vencedor | log loss | Brier |
|---|---|---|---|---|---|---|
| 5 | HEROIC x Lynn Vision | Bo3 | 69.5% | Lynn Vision | 1.189 | 0.484 |
| 5 | 100 Thieves x M80 | Bo3 | 51.6% | 100 Thieves | 0.661 | 0.234 |
| 5 | Imperial x Wildcard | Bo3 | 51.1% | Imperial | 0.671 | 0.239 |

## Partidas: retrospectivo (rodadas 1-4)

| R | Partida | Formato | P(A vence) | Vencedor | log loss | Brier |
|---|---|---|---|---|---|---|
| 1 | NiP x M80 | Bo1 | 52.9% | NiP | 0.636 | 0.222 |
| 1 | PVISION x DENDELE | Bo1 | 53.7% | PVISION | 0.623 | 0.215 |
| 1 | HEROIC x Imperial | Bo1 | 55.5% | Imperial | 0.810 | 0.308 |
| 1 | FaZe x Wildcard | Bo1 | 55.7% | Wildcard | 0.815 | 0.311 |
| 1 | Liquid x GOSH | Bo1 | 57.4% | Liquid | 0.555 | 0.182 |
| 1 | Eternal Fire x FlyQuest | Bo1 | 57.5% | FlyQuest | 0.857 | 0.331 |
| 1 | 100 Thieves x Chinggis Warriors | Bo1 | 59.2% | 100 Thieves | 0.524 | 0.166 |
| 1 | 9z x Lynn Vision | Bo1 | 58.6% | Lynn Vision | 0.882 | 0.343 |
| 2 | FaZe x GOSH | Bo1 | 57.8% | FaZe | 0.548 | 0.178 |
| 2 | Liquid x Wildcard | Bo1 | 55.3% | Liquid | 0.592 | 0.200 |
| 2 | PVISION x FlyQuest | Bo1 | 59.3% | FlyQuest | 0.899 | 0.352 |
| 2 | Eternal Fire x DENDELE | Bo1 | 51.8% | Eternal Fire | 0.657 | 0.232 |
| 2 | 100 Thieves x Imperial | Bo1 | 54.1% | Imperial | 0.778 | 0.292 |
| 2 | 9z x M80 | Bo1 | 50.0% | M80 | 0.694 | 0.250 |
| 2 | NiP x Lynn Vision | Bo1 | 61.4% | NiP | 0.488 | 0.149 |
| 2 | HEROIC x Chinggis Warriors | Bo1 | 60.6% | HEROIC | 0.501 | 0.155 |
| 3 | GOSH x Chinggis Warriors | Bo3 | 53.8% | Chinggis Warriors | 0.772 | 0.289 |
| 3 | NiP x Liquid | Bo3 | 52.1% | NiP | 0.652 | 0.229 |
| 3 | Imperial x FlyQuest | Bo3 | 55.1% | FlyQuest | 0.801 | 0.304 |
| 3 | 9z x DENDELE | Bo3 | 51.4% | 9z | 0.666 | 0.236 |
| 3 | PVISION x FaZe | Bo1 | 50.8% | PVISION | 0.677 | 0.242 |
| 3 | Wildcard x Lynn Vision | Bo1 | 54.8% | Lynn Vision | 0.794 | 0.300 |
| 3 | HEROIC x M80 | Bo1 | 52.3% | M80 | 0.740 | 0.273 |
| 3 | Eternal Fire x 100 Thieves | Bo1 | 50.1% | Eternal Fire | 0.692 | 0.249 |
| 4 | Wildcard x Chinggis Warriors | Bo3 | 56.9% | Wildcard | 0.564 | 0.186 |
| 4 | Imperial x Liquid | Bo3 | 42.9% | Liquid | 0.561 | 0.184 |
| 4 | 100 Thieves x 9z | Bo3 | 51.2% | 100 Thieves | 0.669 | 0.238 |
| 4 | Lynn Vision x PVISION | Bo3 | 33.5% | PVISION | 0.407 | 0.112 |
| 4 | HEROIC x FaZe | Bo3 | 50.5% | HEROIC | 0.683 | 0.245 |
| 4 | M80 x Eternal Fire | Bo3 | 48.6% | Eternal Fire | 0.666 | 0.236 |

## Procedência

| Arquivo | Commit | Data do commit |
|---|---|---|
| predictions/v3_stage1/20261127T001603Z/matches.csv | d8b7305 | 2026-11-26T21:17:09-03:00 |
| predictions/v3_stage1/20261127T001603Z/teams.csv | d8b7305 | 2026-11-26T21:17:09-03:00 |
| predictions/stage2/20261127T001433Z/stage1_next_round.csv | 43fdad6 | 2026-11-26T21:14:48-03:00 |
