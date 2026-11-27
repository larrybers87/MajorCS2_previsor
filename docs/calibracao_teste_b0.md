# Calibração do B0 por faixas no teste (diagnóstico)

Gerado por `python -m backtest.calibration_diagnostic`. **Só diagnóstico:** nada é ajustado a partir desta tabela. O teste já tinha sido visto (sessão 03).

1479 partidas, 2026-06-01 a 2026-11-01, ambos no top 100; walk-forward mensal; B0 top100/points. Faixa = probabilidade do favorito do modelo.

Dois intervalos de 95% para o observado: Wilson (supõe partidas independentes) e bootstrap por dias. **Diferença** = observado menos previsto (negativa = excesso de confiança), com bootstrap por dias.

## média de w=0 e w=1 (modelo da manchete do Stage 2)

| Faixa | n | previsto | observado | Wilson | bootstrap | diferença |
|---|---:|---:|---:|---|---|---|
| 50-60% | 912 | 54.6% | 55.9% | [52.7%; 59.1%] | [52.6%; 59.3%] | +1.3 pp [-2.1; +4.7] |
| 60-70% | 429 | 64.1% | 68.1% | [63.5%; 72.3%] | [63.5%; 72.7%] | +3.9 pp [-0.6; +8.5] |
| 70-80% | 116 | 73.9% | 75.0% | [66.4%; 82.0%] | [66.7%; 83.3%] | +1.1 pp [-7.4; +9.6] |
| 80%+ | 22 | 84.6% | 59.1% | [38.7%; 76.7%] | [36.8%; 79.2%] | -25.5 pp [-46.9; -6.2] |

## w=0

| Faixa | n | previsto | observado | Wilson | bootstrap | diferença |
|---|---:|---:|---:|---|---|---|
| 50-60% | 918 | 54.6% | 56.0% | [52.8%; 59.2%] | [52.7%; 59.3%] | +1.3 pp [-1.9; +4.7] |
| 60-70% | 423 | 64.2% | 68.1% | [63.5%; 72.3%] | [63.4%; 72.7%] | +3.9 pp [-0.6; +8.6] |
| 70-80% | 116 | 73.9% | 75.0% | [66.4%; 82.0%] | [66.4%; 83.5%] | +1.1 pp [-7.6; +9.5] |
| 80%+ | 22 | 84.7% | 59.1% | [38.7%; 76.7%] | [36.8%; 78.3%] | -25.6 pp [-47.3; -6.5] |

## w=1

| Faixa | n | previsto | observado | Wilson | bootstrap | diferença |
|---|---:|---:|---:|---|---|---|
| 50-60% | 907 | 54.6% | 55.8% | [52.5%; 59.0%] | [52.5%; 59.1%] | +1.2 pp [-2.1; +4.4] |
| 60-70% | 434 | 64.1% | 68.2% | [63.7%; 72.4%] | [63.6%; 72.8%] | +4.1 pp [-0.5; +8.8] |
| 70-80% | 116 | 73.9% | 75.0% | [66.4%; 82.0%] | [66.4%; 83.5%] | +1.1 pp [-7.5; +9.4] |
| 80%+ | 22 | 84.4% | 59.1% | [38.7%; 76.7%] | [36.8%; 78.3%] | -25.3 pp [-46.7; -5.8] |

## Leitura
- O valor da sessão 03 para a faixa acima de 80% (D21, 84,7% previsto) é a linha `w=0`. A manchete usa a média de w=0 e w=1 (84,6%). São as mesmas 22 partidas e o mesmo observado; só muda a probabilidade prevista.
- São quatro faixas e três versões do modelo: algum intervalo pode excluir o previsto por acaso (sem correção para comparações múltiplas).
- A faixa 80%+ tem poucas partidas; o bootstrap com poucos dias é instável.
