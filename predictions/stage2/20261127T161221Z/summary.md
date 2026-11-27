# Previsão do Stage 2 — PGL Major Singapore 2026

- Gerado em 2026-11-27T16:12:21+00:00 (UTC); commit do código `d39cd1a42b`.
- Modo: **Stage 1 completo**. Simulações: 200000 por variante.
- Modelo **B0**: só pontos VRS de 02/11/2026 (points), calibrado em partidas até 2026-11-01.
- Formato das partidas históricas (H10): a fração de Bo1 não é identificável (IC [0.00; 1.00]). Número principal = **média** das probabilidades dos dois extremos (w=0: beta 0.1558, w=1: beta 0.2361); as colunas `w=0` e `w=1` mostram a faixa.
- Limites: ignora forma recente, mapas, elencos, substitutos e a força mostrada neste Major (o B0 não atualiza ratings; os resultados entram só como fatos). No teste, o B0 foi confiante demais acima de 80% (n pequeno). Hipóteses de regras em `docs/duvidas_abertas.md`.

## Probabilidades por time

| Time | Seed | P(3-0) | P(3-1) | P(3-2) | P(2-3) | P(1-3) | P(0-3) | P(avançar) | P(avançar) w=0 | P(avançar) w=1 |
|---|---|---|---|---|---|---|---|---|---|---|
| FUT | 1 | 26.6% | 27.1% | 20.3% | 12.3% | 9.5% | 4.1% | 74.1% | 70.0% | 78.2% |
| Nemiga | 2 | 18.1% | 24.3% | 21.8% | 15.6% | 13.3% | 7.0% | 64.1% | 61.4% | 66.9% |
| G2 | 3 | 16.4% | 23.1% | 21.1% | 17.0% | 14.6% | 7.8% | 60.7% | 58.7% | 62.6% |
| THE ONE | 4 | 15.3% | 22.2% | 21.0% | 17.8% | 15.5% | 8.3% | 58.4% | 56.9% | 60.0% |
| Natus Vincere | 5 | 14.2% | 21.5% | 21.0% | 17.9% | 16.3% | 9.1% | 56.7% | 55.5% | 58.0% |
| Astralis | 6 | 14.8% | 21.1% | 20.2% | 18.7% | 16.4% | 8.8% | 56.1% | 55.0% | 57.2% |
| The MongolZ | 7 | 15.2% | 20.8% | 19.5% | 19.3% | 16.8% | 8.4% | 55.5% | 54.5% | 56.5% |
| NiP | 10 | 12.0% | 19.8% | 20.6% | 18.6% | 17.8% | 11.1% | 52.4% | 52.0% | 52.9% |
| PVISION | 13 | 11.5% | 19.4% | 20.8% | 18.8% | 18.1% | 11.4% | 51.7% | 51.4% | 52.0% |
| MIBR | 8 | 12.1% | 19.5% | 20.0% | 19.5% | 18.0% | 10.8% | 51.6% | 51.4% | 51.9% |
| Liquid | 11 | 10.6% | 17.9% | 19.6% | 19.8% | 19.6% | 12.6% | 48.1% | 48.5% | 47.6% |
| Eternal Fire | 12 | 9.8% | 17.2% | 19.2% | 20.1% | 20.3% | 13.3% | 46.3% | 47.2% | 45.5% |
| 100 Thieves | 16 | 9.3% | 16.6% | 19.1% | 20.1% | 20.9% | 14.0% | 45.0% | 46.1% | 43.9% |
| Imperial | 14 | 6.4% | 12.6% | 14.9% | 21.9% | 25.0% | 19.1% | 34.0% | 37.2% | 30.8% |
| FlyQuest | 9 | 4.2% | 9.0% | 11.3% | 21.4% | 28.2% | 25.8% | 24.6% | 28.9% | 20.2% |
| Lynn Vision | 15 | 3.5% | 7.6% | 9.6% | 21.3% | 29.7% | 28.3% | 20.7% | 25.4% | 16.0% |

## Rodada de abertura (1v9 ... 8v16, pela engine)

| Seeds | Time A | Time B | Formato | P(A vence) |
|---|---|---|---|---|
| 1v9 | FUT | FlyQuest | Bo1 | 68.7% |
| 2v10 | Nemiga | NiP | Bo1 | 54.2% |
| 3v11 | G2 | Liquid | Bo1 | 54.3% |
| 4v12 | THE ONE | Eternal Fire | Bo1 | 54.2% |
| 5v13 | Natus Vincere | PVISION | Bo1 | 51.4% |
| 6v14 | Astralis | Imperial | Bo1 | 58.1% |
| 7v15 | The MongolZ | Lynn Vision | Bo1 | 63.7% |
| 8v16 | MIBR | 100 Thieves | Bo1 | 51.7% |
