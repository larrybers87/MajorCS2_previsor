# Calibração do B0

Gerado por `python -m backtest.b0_calibration` (não editar à mão).

- Partidas com rating na janela: 13127; treino final: 5196 (2025-06-01 a 2026-11-01), população **top100**.
- Transformação escolhida: **points**; **beta = 0.1558**, IC 95% [0.1386; 0.1750].
- **Hipótese H10 (não verificada):** toda partida histórica tratada como Bo3.

## Escolha do modelo

| Transformação | beta | log-verossimilhança no treino final |
|---|---:|---:|
| points | 0.1558 | -3443.8 |
| log | 2.0184 | -3446.0 |

| Treino / transformação | log loss walk-forward no alvo |
|---|---:|
| todas/points | 0.6650 |
| todas/log | 0.6659 |
| top100/points | 0.6643 |
| top100/log | 0.6650 |

A escolha usa os mesmos dados da avaliação abaixo (4 combinações), o que traz um otimismo pequeno.

## Avaliação walk-forward (4356 partidas, 2025-09-01 a 2026-11-01, ambos no top 100)

IC 95% por bootstrap reamostrando dias.

| Previsor | log loss | IC 95% | Brier | IC 95% |
|---|---:|---|---:|---|
| B0 | 0.6643 | [0.6575; 0.6714] | 0.2359 | [0.2328; 0.2392] |
| Maior VRS vence, com a taxa histórica | 0.6767 | [0.6713; 0.6824] | 0.2418 | [0.2390; 0.2448] |
| 50% fixo | 0.6931 | [0.6931; 0.6931] | 0.2500 | [0.2500; 0.2500] |
| Maior VRS vence (0 ou 100%) | infinito | - | 0.4071 | [0.3927; 0.4213] |

Acerto da regra "maior VRS vence": 59.2%.

| Diferença pareada (negativo = B0 melhor) | log loss | IC 95% | Brier | IC 95% |
|---|---:|---|---:|---|
| B0 - 50% | -0.0289 | [-0.0354; -0.0223] | -0.0141 | [-0.0173; -0.0109] |
| B0 - taxa fixa | -0.0124 | [-0.0167; -0.0082] | -0.0059 | [-0.0077; -0.0040] |

## Calibração (favorito do modelo)

| Faixa | n | previsto | observado |
|---|---:|---:|---:|
| 50%-60% | 2786 | 54.5% | 54.5% |
| 60%-70% | 1181 | 64.0% | 65.2% |
| 70%-80% | 339 | 73.6% | 74.6% |
| 80%-90% | 46 | 83.9% | 73.9% |
| 90%-100% | 4 | 91.7% | 75.0% |

## Sensibilidade a H10

Se as partidas fossem todas Bo1: beta por mapa = 0.2361 (contra 0.1558), log loss walk-forward 0.6643. O log loss quase não distingue as duas leituras, mas o beta por mapa muda, e com ele as probabilidades de Bo1. O valor verdadeiro (mistura de formatos) deve ficar entre os dois.
