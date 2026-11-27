# H10: formato das partidas e avaliação aninhada do B0

Gerado por `python -m backtest.h10_format` (não editar à mão). Protocolo em [protocolo_sessao_03.md](protocolo_sessao_03.md).

## Escolha do B0 só no desenvolvimento (D23)

| População/transformação | log loss no desenvolvimento |
|---|---:|
| todas/points | 0.6676 |
| top100/points | 0.6664 |
| todas/log | 0.6682 |
| top100/log | 0.6680 |

Escolhido: **top100 / points**.

## Fração de Bo1 (w)

5196 partidas, 2025-06-01 a 2026-11-01.

- Estimativa conjunta: **w = 0.68**, beta = 0.2046.
- IC 95% pelo perfil de verossimilhança: [0.00; 1.00].
- IC 95% por bootstrap de dias: [0.00; 0.75].
- Regra (intervalo mais largo = 1.00): **faixa**; w = 0.00 com beta 0.1558, w = 1.00 com beta 0.2361.

### Perfil de verossimilhança

| w | beta | log-verossimilhança menos o máximo |
|---:|---:|---:|
| 0.00 | 0.1558 | -0.344 |
| 0.10 | 0.1617 | -0.258 |
| 0.20 | 0.1680 | -0.183 |
| 0.30 | 0.1747 | -0.119 |
| 0.40 | 0.1819 | -0.067 |
| 0.50 | 0.1895 | -0.029 |
| 0.60 | 0.1976 | -0.006 |
| 0.70 | 0.2063 | -0.000 |
| 0.80 | 0.2156 | -0.014 |
| 0.90 | 0.2255 | -0.050 |
| 1.00 | 0.2361 | -0.112 |

## Teste aninhado

1479 partidas, 2026-06-01 a 2026-11-01, walk-forward mensal, ambos no top 100. IC 95% por dias.

| Modelo | log loss | IC 95% | Brier | IC 95% |
|---|---:|---|---:|---|
| B0, w=0 | 0.6601 | [0.6475; 0.6730] | 0.2337 | [0.2277; 0.2396] |
| B0, w=1 | 0.6600 | [0.6478; 0.6722] | 0.2336 | [0.2278; 0.2394] |
| B0, w estimado | 0.6599 | [0.6476; 0.6723] | 0.2336 | [0.2280; 0.2393] |

| Diferença para w = 0 | log loss | IC 95% |
|---|---:|---|
| w=1 | -0.00011 | [-0.00021; -0.00001] |
| w estimado | -0.00016 | [-0.00031; -0.00002] |

w escolhido em cada mês do teste: 0.61, 0.64, 0.66, 0.66, 0.67, 0.68.

## D21: calibração do favorito no teste (B0, w = 0)

Wilson 95% (supõe partidas independentes).

| Faixa | n | previsto | observado | IC 95% |
|---|---:|---:|---:|---|
| 50%-60% | 918 | 54.6% | 56.0% | [52.8%; 59.2%] |
| 60%-70% | 423 | 64.2% | 68.1% | [63.5%; 72.3%] |
| 70%-80% | 116 | 73.9% | 75.0% | [66.4%; 82.0%] |
| 80%-90% | 21 | 84.3% | 57.1% | [36.5%; 75.5%] |
| 90%-100% | 1 | 93.8% | 100.0% | [20.7%; 100.0%] |
| >= 80% | 22 | 84.7% | 59.1% | [38.7%; 76.7%] |
