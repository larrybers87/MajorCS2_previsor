# V3 — Stage 1 (RETROSPECTIVO)

Gerado **depois** das partidas: não é previsão. O B0 usa só o VRS de 02/11/2026 e beta calibrado em partidas até 2026-11-01; nada foi ajustado com o Stage 1. Com no máximo 33 partidas, o resultado NÃO permite comparar modelos.

As seções de métricas e partidas logo abaixo são do **B0 com w=0**; a comparação com o B1 está no fim.

Partidas decididas: 33 de 33; stage encerrado.

## Validação das regras

- Rodada 1 real = 1v9 ... 8v16 com os nossos seeds: **sim**
- V2, rodadas 2 a 5: **sem divergências**.

## Métricas

| Métrica | Valor |
|---|---|
| partidas | 33 |
| log_loss | 0.6855 |
| log_loss_erro_padrao | 0.0239 |
| log_loss_50 | 0.6931 |
| brier | 0.2462 |
| brier_50 | 0.2500 |
| brier_maior_vrs_vence | 0.3636 |
| acerto_do_favorito | 0.6364 |
| times_encerrados | 16 |
| log_score_cartel | 1.7567 |
| log_score_cartel_sem_informacao | 1.7753 |
| brier_avanco | 0.2495 |
| brier_avanco_sem_informacao | 0.2500 |

## Previsto desde a rodada 1 x observado

| Seed | Time | P(3-0) | P(3-1) | P(3-2) | P(2-3) | P(1-3) | P(0-3) | P(avançar) | Observado | P(observado) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | NiP | 17.6% | 23.5% | 21.1% | 16.1% | 13.9% | 7.7% | 62.3% | 3-0 | 17.6% |
| 2 | PVISION | 17.4% | 23.5% | 20.8% | 16.3% | 14.2% | 7.8% | 61.8% | 3-1 | 23.5% |
| 3 | HEROIC | 17.1% | 23.0% | 20.5% | 16.8% | 14.6% | 8.0% | 60.6% | 2-3 | 16.8% |
| 4 | FaZe | 16.5% | 22.4% | 20.7% | 17.0% | 15.1% | 8.3% | 59.6% | 1-3 | 15.1% |
| 5 | Liquid | 16.2% | 22.0% | 20.6% | 17.2% | 15.5% | 8.6% | 58.8% | 3-1 | 22.0% |
| 6 | Eternal Fire | 15.3% | 21.4% | 20.2% | 18.0% | 16.2% | 8.9% | 57.0% | 3-1 | 21.4% |
| 7 | 100 Thieves | 15.8% | 21.6% | 20.1% | 17.8% | 16.0% | 8.8% | 57.5% | 3-2 | 20.1% |
| 8 | 9z | 14.7% | 20.7% | 19.7% | 18.6% | 16.8% | 9.5% | 55.1% | 1-3 | 16.8% |
| 9 | M80 | 12.3% | 19.7% | 20.4% | 18.2% | 18.0% | 11.4% | 52.3% | 2-3 | 18.2% |
| 10 | DENDELE | 11.4% | 18.8% | 19.9% | 18.8% | 18.9% | 12.1% | 50.1% | 0-3 | 12.1% |
| 11 | Imperial | 9.5% | 16.7% | 18.3% | 20.1% | 20.9% | 14.5% | 44.6% | 3-2 | 18.3% |
| 12 | Wildcard | 9.1% | 16.1% | 17.8% | 20.3% | 21.5% | 15.1% | 43.0% | 2-3 | 20.3% |
| 13 | GOSH | 7.6% | 14.0% | 16.3% | 20.9% | 23.4% | 17.8% | 37.9% | 0-3 | 17.8% |
| 14 | FlyQuest | 7.2% | 13.4% | 15.6% | 21.1% | 24.0% | 18.8% | 36.1% | 3-0 | 7.2% |
| 15 | Chinggis Warriors | 6.1% | 11.6% | 14.1% | 21.4% | 25.5% | 21.3% | 31.9% | 1-3 | 25.5% |
| 16 | Lynn Vision | 6.0% | 11.6% | 13.9% | 21.6% | 25.6% | 21.4% | 31.5% | 3-2 | 13.9% |

## Partidas

| R | Time A | Time B | Bo | P(A) | Vencedor | log loss |
|---|---|---|---|---|---|---|
| 1 | NiP | M80 | 1 | 52.9% | NiP | 0.636 |
| 1 | PVISION | DENDELE | 1 | 53.7% | PVISION | 0.623 |
| 1 | HEROIC | Imperial | 1 | 55.5% | Imperial | 0.810 |
| 1 | FaZe | Wildcard | 1 | 55.7% | Wildcard | 0.815 |
| 1 | Liquid | GOSH | 1 | 57.4% | Liquid | 0.555 |
| 1 | Eternal Fire | FlyQuest | 1 | 57.5% | FlyQuest | 0.857 |
| 1 | 100 Thieves | Chinggis Warriors | 1 | 59.2% | 100 Thieves | 0.524 |
| 1 | 9z | Lynn Vision | 1 | 58.6% | Lynn Vision | 0.882 |
| 2 | FaZe | GOSH | 1 | 57.8% | FaZe | 0.548 |
| 2 | Liquid | Wildcard | 1 | 55.3% | Liquid | 0.592 |
| 2 | PVISION | FlyQuest | 1 | 59.3% | FlyQuest | 0.899 |
| 2 | Eternal Fire | DENDELE | 1 | 51.8% | Eternal Fire | 0.657 |
| 2 | 100 Thieves | Imperial | 1 | 54.1% | Imperial | 0.778 |
| 2 | 9z | M80 | 1 | 50.0% | M80 | 0.694 |
| 2 | NiP | Lynn Vision | 1 | 61.4% | NiP | 0.488 |
| 2 | HEROIC | Chinggis Warriors | 1 | 60.6% | HEROIC | 0.501 |
| 3 | GOSH | Chinggis Warriors | 3 | 53.8% | Chinggis Warriors | 0.772 |
| 3 | NiP | Liquid | 3 | 52.1% | NiP | 0.652 |
| 3 | Imperial | FlyQuest | 3 | 55.1% | FlyQuest | 0.801 |
| 3 | 9z | DENDELE | 3 | 51.4% | 9z | 0.666 |
| 3 | PVISION | FaZe | 1 | 50.8% | PVISION | 0.677 |
| 3 | Wildcard | Lynn Vision | 1 | 54.8% | Lynn Vision | 0.794 |
| 3 | HEROIC | M80 | 1 | 52.3% | M80 | 0.740 |
| 3 | Eternal Fire | 100 Thieves | 1 | 50.1% | Eternal Fire | 0.692 |
| 4 | Wildcard | Chinggis Warriors | 3 | 56.9% | Wildcard | 0.564 |
| 4 | Imperial | Liquid | 3 | 42.9% | Liquid | 0.561 |
| 4 | 100 Thieves | 9z | 3 | 51.2% | 100 Thieves | 0.669 |
| 4 | Lynn Vision | PVISION | 3 | 33.5% | PVISION | 0.407 |
| 4 | HEROIC | FaZe | 3 | 50.5% | HEROIC | 0.683 |
| 4 | M80 | Eternal Fire | 3 | 48.6% | Eternal Fire | 0.666 |
| 5 | Lynn Vision | HEROIC | 3 | 34.1% | Lynn Vision | 1.076 |
| 5 | Imperial | Wildcard | 3 | 50.9% | Imperial | 0.676 |
| 5 | M80 | 100 Thieves | 3 | 48.7% | 100 Thieves | 0.668 |

## B0 e B1 lado a lado (RETROSPECTIVO)

B0: logística na diferença de pontos VRS de 02/11. B1: Elo congelado (s=0,5, K=20, sem decaimento, m=2), atualizado só com rodadas anteriores. `média` = média das probabilidades de w=0 e w=1. EP = erro padrão entre partidas, que as trata como independentes (não são). A média B0/B1 não é calculada aqui.

| Modelo | Variante | n | log loss | Brier | Favorito venceu |
|---|---|---|---|---|---|
| B0 | w=0 | 33 | 0.6855 (EP 0.0239) | 0.2462 (EP 0.0117) | 21/33 |
| B1 | w=0 | 33 | 0.6504 (EP 0.0155) | 0.2289 (EP 0.0077) | 23/33 |
| B0 | w=1 | 33 | 0.6887 (EP 0.0363) | 0.2476 (EP 0.0174) | 21/33 |
| B1 | w=1 | 33 | 0.6325 (EP 0.0228) | 0.2204 (EP 0.0111) | 23/33 |
| B0 | média | 33 | 0.6865 (EP 0.0300) | 0.2466 (EP 0.0145) | 21/33 |
| B1 | média | 33 | 0.6412 (EP 0.0191) | 0.2245 (EP 0.0094) | 23/33 |

Referência 50%: log loss 0,6931, Brier 0,2500.

Diferença pareada B1 - B0 (negativo favorece o B1):

| Variante | log loss | Brier |
|---|---|---|
| w=0 | -0.0351 (EP 0.0195) | -0.0173 (EP 0.0096) |
| w=1 | -0.0562 (EP 0.0296) | -0.0272 (EP 0.0141) |
| média | -0.0453 (EP 0.0245) | -0.0222 (EP 0.0118) |

Por formato (variante `média`):

| Formato | Modelo | n | log loss | Brier |
|---|---|---|---|---|
| Bo1 | B0 | 20 | 0.6896 (EP 0.0363) | 0.2483 (EP 0.0179) |
| Bo1 | B1 | 20 | 0.6461 (EP 0.0280) | 0.2270 (EP 0.0137) |
| Bo3 | B0 | 13 | 0.6818 (EP 0.0536) | 0.2440 (EP 0.0256) |
| Bo3 | B1 | 13 | 0.6337 (EP 0.0239) | 0.2205 (EP 0.0119) |

Cartéis finais previstos antes da rodada 1 (ratings fixos no stage; sem erro padrão, porque os times são dependentes):

| Modelo | Variante | Classificados | Brier de avançar | log score (soma) | sem informação |
|---|---|---|---|---|---|
| B0 | w=0 | 5/8 | 0.2495 | 28.108 | 28.405 |
| B0 | w=1 | 5/8 | 0.2572 | 28.304 | 28.405 |
| B0 | média | 5/8 | 0.2527 | 28.174 | 28.405 |
| B1 | w=0 | 5/8 | 0.2164 | 26.940 | 28.405 |
| B1 | w=1 | 5/8 | 0.2081 | 26.428 | 28.405 |
| B1 | média | 5/8 | 0.2118 | 26.670 | 28.405 |

Probabilidade de `time_a` por partida (variante `média`):

| R | Time A | Time B | Bo | B0 | B1 | Vencedor |
|---|---|---|---|---|---|---|
| 1 | NiP | M80 | 1 | 53.7% | 53.4% | NiP |
| 1 | PVISION | DENDELE | 1 | 54.6% | 57.0% | PVISION |
| 1 | HEROIC | Imperial | 1 | 56.9% | 56.1% | Imperial |
| 1 | FaZe | Wildcard | 1 | 57.2% | 58.2% | Wildcard |
| 1 | Liquid | GOSH | 1 | 59.2% | 58.9% | Liquid |
| 1 | Eternal Fire | FlyQuest | 1 | 59.4% | 49.5% | FlyQuest |
| 1 | 100 Thieves | Chinggis Warriors | 1 | 61.5% | 63.8% | 100 Thieves |
| 1 | 9z | Lynn Vision | 1 | 60.7% | 50.5% | Lynn Vision |
| 2 | FaZe | GOSH | 1 | 59.8% | 64.0% | FaZe |
| 2 | Liquid | Wildcard | 1 | 56.7% | 51.8% | Liquid |
| 2 | PVISION | FlyQuest | 1 | 61.6% | 51.0% | FlyQuest |
| 2 | Eternal Fire | DENDELE | 1 | 52.3% | 55.2% | Eternal Fire |
| 2 | 100 Thieves | Imperial | 1 | 55.1% | 52.3% | Imperial |
| 2 | 9z | M80 | 1 | 50.0% | 52.3% | M80 |
| 2 | NiP | Lynn Vision | 1 | 64.1% | 51.5% | NiP |
| 2 | HEROIC | Chinggis Warriors | 1 | 63.2% | 66.2% | HEROIC |
| 3 | GOSH | Chinggis Warriors | 3 | 54.8% | 49.8% | Chinggis Warriors |
| 3 | NiP | Liquid | 3 | 52.6% | 59.3% | NiP |
| 3 | Imperial | FlyQuest | 3 | 56.4% | 44.6% | FlyQuest |
| 3 | 9z | DENDELE | 3 | 51.8% | 56.6% | 9z |
| 3 | PVISION | FaZe | 1 | 51.0% | 51.7% | PVISION |
| 3 | Wildcard | Lynn Vision | 1 | 56.0% | 43.5% | Lynn Vision |
| 3 | HEROIC | M80 | 1 | 52.9% | 54.9% | M80 |
| 3 | Eternal Fire | 100 Thieves | 1 | 50.1% | 50.7% | Eternal Fire |
| 4 | Wildcard | Chinggis Warriors | 3 | 58.7% | 59.5% | Wildcard |
| 4 | Imperial | Liquid | 3 | 41.1% | 54.0% | Liquid |
| 4 | 100 Thieves | 9z | 3 | 51.5% | 49.8% | 100 Thieves |
| 4 | Lynn Vision | PVISION | 3 | 29.7% | 46.2% | PVISION |
| 4 | HEROIC | FaZe | 3 | 50.7% | 53.4% | HEROIC |
| 4 | M80 | Eternal Fire | 3 | 48.2% | 46.4% | Eternal Fire |
| 5 | Lynn Vision | HEROIC | 3 | 30.5% | 45.4% | Lynn Vision |
| 5 | Imperial | Wildcard | 3 | 51.1% | 56.7% | Imperial |
| 5 | M80 | 100 Thieves | 3 | 48.4% | 47.5% | 100 Thieves |
