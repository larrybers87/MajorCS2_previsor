# Previsão do Stage 2 — PGL Major Singapore 2026

- Gerado em 2026-11-27T00:14:33+00:00 (UTC); commit do código `b4135ace1f`.
- Modo: **condicionado: Stage 1 com 30 partidas decididas, restante simulado**. Simulações: 200000 por variante.
- Modelo **B0**: só pontos VRS de 02/11/2026 (points), calibrado em partidas até 2026-11-01.
- Formato das partidas históricas (H10): a fração de Bo1 não é identificável (IC [0.00; 1.00]). Número principal = **média** das probabilidades dos dois extremos (w=0: beta 0.1558, w=1: beta 0.2361); as colunas `w=0` e `w=1` mostram a faixa.
- Limites: ignora forma recente, mapas, elencos, substitutos e a força mostrada neste Major (o B0 não atualiza ratings; os resultados entram só como fatos). No teste, o B0 foi confiante demais acima de 80% (n pequeno). Hipóteses de regras em `docs/duvidas_abertas.md`.

## Stage 1: partidas pendentes da rodada 5

| Seeds | Time A | Time B | Formato | P(A vence) |
|---|---|---|---|---|
| 3v16 | HEROIC | Lynn Vision | Bo3 | 69.5% |
| 7v9 | 100 Thieves | M80 | Bo3 | 51.6% |
| 11v12 | Imperial | Wildcard | Bo3 | 51.1% |

## Probabilidades por time no Stage 2

As colunas de cartel e P(avançar) já incluem a chance de o time chegar ao Stage 2.

| Time | P(participa) | P(3-0) | P(3-1) | P(3-2) | P(2-3) | P(1-3) | P(0-3) | P(avançar) | P(avançar | participa) | P(avançar) w=0 | P(avançar) w=1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FUT | 100.0% | 25.5% | 26.8% | 20.6% | 12.5% | 10.0% | 4.6% | 72.9% | 72.9% | 69.0% | 76.8% |
| Nemiga | 100.0% | 17.9% | 23.6% | 21.5% | 15.7% | 13.7% | 7.6% | 63.1% | 63.1% | 60.7% | 65.5% |
| G2 | 100.0% | 16.1% | 22.4% | 20.9% | 17.2% | 15.0% | 8.4% | 59.4% | 59.4% | 57.7% | 61.2% |
| THE ONE | 100.0% | 15.0% | 21.6% | 20.6% | 17.7% | 15.9% | 9.1% | 57.3% | 57.3% | 56.0% | 58.5% |
| Natus Vincere | 100.0% | 14.0% | 21.0% | 20.6% | 18.1% | 16.6% | 9.7% | 55.6% | 55.6% | 54.5% | 56.7% |
| Astralis | 100.0% | 14.5% | 20.7% | 19.7% | 18.9% | 16.8% | 9.4% | 54.9% | 54.9% | 54.2% | 55.7% |
| The MongolZ | 100.0% | 13.3% | 20.0% | 19.3% | 19.5% | 17.9% | 10.1% | 52.5% | 52.5% | 52.1% | 52.9% |
| NiP | 100.0% | 11.7% | 19.5% | 20.3% | 18.7% | 18.2% | 11.7% | 51.5% | 51.5% | 51.3% | 51.7% |
| MIBR | 100.0% | 12.2% | 19.2% | 19.3% | 19.6% | 18.5% | 11.2% | 50.8% | 50.8% | 50.8% | 50.8% |
| PVISION | 100.0% | 11.5% | 19.1% | 20.0% | 19.0% | 18.6% | 11.7% | 50.6% | 50.6% | 50.5% | 50.7% |
| Liquid | 100.0% | 10.4% | 17.6% | 18.9% | 19.8% | 20.0% | 13.2% | 47.0% | 47.0% | 47.7% | 46.2% |
| Eternal Fire | 100.0% | 9.8% | 17.0% | 18.5% | 20.0% | 20.7% | 14.0% | 45.3% | 45.3% | 46.4% | 44.2% |
| HEROIC | 69.6% | 7.4% | 12.4% | 13.7% | 13.3% | 13.9% | 9.0% | 33.4% | 48.0% | 31.9% | 34.9% |
| FlyQuest | 100.0% | 4.1% | 8.8% | 10.9% | 21.2% | 28.2% | 26.8% | 23.8% | 23.8% | 28.3% | 19.3% |
| 100 Thieves | 51.6% | 4.9% | 8.6% | 9.6% | 10.4% | 10.9% | 7.3% | 23.1% | 44.7% | 23.5% | 22.6% |
| M80 | 48.4% | 4.2% | 7.6% | 8.5% | 10.1% | 10.7% | 7.3% | 20.3% | 42.0% | 21.2% | 19.4% |
| Imperial | 51.2% | 3.4% | 6.2% | 7.3% | 11.2% | 12.9% | 10.2% | 16.8% | 32.9% | 18.4% | 15.2% |
| Wildcard | 48.8% | 2.9% | 5.7% | 6.7% | 10.7% | 12.7% | 10.2% | 15.3% | 31.3% | 17.0% | 13.5% |
| Lynn Vision | 30.4% | 1.1% | 2.4% | 3.0% | 6.5% | 9.0% | 8.5% | 6.5% | 21.2% | 8.6% | 4.3% |
| FaZe | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | nan% | 0.0% | 0.0% |
| 9z | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | nan% | 0.0% | 0.0% |
| DENDELE | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | nan% | 0.0% | 0.0% |
| GOSH | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | nan% | 0.0% | 0.0% |
| Chinggis Warriors | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | nan% | 0.0% | 0.0% |

## Rodada de abertura: três adversários mais prováveis (Bo1)

| Confronto | Time | Adversário | P(confronto) | P(vitória do convidado) |
|---|---|---|---|---|
| 1v9 | FUT | FlyQuest | 92.8% | 68.7% |
| 1v9 | FUT | NiP | 7.2% | 57.6% |
| 2v10 | Nemiga | NiP | 92.8% | 54.2% |
| 2v10 | Nemiga | FlyQuest | 7.2% | 65.6% |
| 3v11 | G2 | Liquid | 100.0% | 54.3% |
| 4v12 | THE ONE | Eternal Fire | 100.0% | 54.2% |
| 5v13 | Natus Vincere | PVISION | 100.0% | 51.4% |
| 6v14 | Astralis | Imperial | 51.2% | 58.1% |
| 6v14 | Astralis | 100 Thieves | 17.5% | 53.0% |
| 6v14 | Astralis | M80 | 16.4% | 54.1% |
| 7v15 | The MongolZ | Wildcard | 41.7% | 57.9% |
| 7v15 | The MongolZ | M80 | 31.9% | 53.2% |
| 7v15 | The MongolZ | 100 Thieves | 18.4% | 52.1% |
| 8v16 | MIBR | HEROIC | 69.6% | 49.9% |
| 8v16 | MIBR | 100 Thieves | 15.7% | 51.7% |
| 8v16 | MIBR | Lynn Vision | 7.6% | 63.3% |
