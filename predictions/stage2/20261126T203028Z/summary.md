# Previsão do Stage 2 — PGL Major Singapore 2026

- Gerado em 2026-11-26T20:30:28+00:00 (UTC); commit do código `b8b0c4eddc`.
- Modo: **condicionado: Stage 1 com 0 partidas decididas, restante simulado**. Simulações: 200000.
- Modelo **B0**: só pontos VRS de 02/11/2026; beta = 0.1558 (points), calibrado em partidas até 2026-11-01.
- Limites: ignora forma recente, mapas, elencos e resultados deste Major (o B0 não atualiza ratings); H10 (formato das partidas históricas) e as hipóteses de regras estão em `docs/duvidas_abertas.md`.
- Os nomes THE ONE = 1win e GOSH = BC.Game no VRS são hipótese (D15).

## Probabilidades por time

As colunas de cartel e P(avançar) já incluem a chance de o time chegar ao Stage 2.

| Time | P(participa) | P(3-0) | P(3-1) | P(3-2) | P(2-3) | P(1-3) | P(0-3) | P(avançar) | P(avançar | participa) | P(avançar) se H10=Bo1 |
|---|---|---|---|---|---|---|---|---|---|---|
| FUT | 100.0% | 21.2% | 25.5% | 21.3% | 14.0% | 11.8% | 6.3% | 67.9% | 67.9% | 75.2% |
| Nemiga | 100.0% | 17.6% | 23.2% | 20.8% | 16.3% | 14.4% | 7.8% | 61.5% | 61.5% | 66.3% |
| G2 | 100.0% | 16.2% | 21.9% | 20.3% | 17.2% | 15.5% | 8.7% | 58.5% | 58.5% | 61.7% |
| THE ONE | 100.0% | 15.3% | 21.3% | 20.1% | 17.8% | 16.2% | 9.3% | 56.7% | 56.7% | 59.2% |
| Natus Vincere | 100.0% | 14.7% | 21.0% | 20.1% | 18.1% | 16.6% | 9.5% | 55.8% | 55.8% | 57.8% |
| Astralis | 100.0% | 14.1% | 20.4% | 19.8% | 18.5% | 17.1% | 10.2% | 54.2% | 54.2% | 55.3% |
| The MongolZ | 100.0% | 13.2% | 19.8% | 19.5% | 18.8% | 18.0% | 10.8% | 52.4% | 52.4% | 52.8% |
| MIBR | 100.0% | 12.9% | 19.2% | 19.2% | 19.2% | 18.4% | 11.1% | 51.3% | 51.3% | 51.2% |
| NiP | 61.9% | 7.5% | 11.8% | 12.3% | 11.5% | 11.4% | 7.4% | 31.6% | 51.1% | 34.3% |
| PVISION | 61.6% | 7.3% | 11.7% | 12.1% | 11.6% | 11.3% | 7.6% | 31.1% | 50.4% | 33.6% |
| HEROIC | 60.9% | 6.9% | 11.3% | 11.9% | 11.4% | 11.5% | 7.8% | 30.1% | 49.5% | 32.0% |
| FaZe | 59.5% | 6.5% | 10.9% | 11.6% | 11.4% | 11.5% | 7.7% | 29.0% | 48.7% | 30.3% |
| Liquid | 58.6% | 6.2% | 10.5% | 11.1% | 11.4% | 11.5% | 7.9% | 27.8% | 47.5% | 28.6% |
| 100 Thieves | 57.3% | 6.0% | 10.0% | 10.6% | 11.2% | 11.8% | 7.8% | 26.6% | 46.4% | 26.5% |
| Eternal Fire | 57.2% | 5.9% | 9.9% | 10.6% | 11.3% | 11.5% | 8.0% | 26.4% | 46.2% | 26.6% |
| 9z | 55.1% | 5.3% | 9.0% | 10.0% | 10.9% | 11.6% | 8.3% | 24.4% | 44.2% | 23.4% |
| M80 | 52.8% | 5.1% | 8.7% | 9.5% | 10.5% | 11.2% | 7.9% | 23.3% | 44.1% | 21.9% |
| DENDELE | 50.2% | 4.5% | 7.9% | 8.8% | 10.2% | 10.8% | 8.0% | 21.2% | 42.2% | 18.8% |
| Imperial | 44.3% | 3.3% | 6.0% | 6.9% | 9.4% | 10.7% | 8.1% | 16.2% | 36.5% | 12.3% |
| Wildcard | 43.0% | 3.0% | 5.6% | 6.6% | 9.2% | 10.5% | 8.2% | 15.2% | 35.3% | 11.0% |
| GOSH | 37.7% | 2.2% | 4.3% | 5.1% | 8.2% | 9.7% | 8.2% | 11.6% | 30.8% | 7.2% |
| FlyQuest | 36.2% | 2.0% | 4.0% | 4.7% | 7.8% | 9.5% | 8.1% | 10.8% | 29.7% | 6.1% |
| Chinggis Warriors | 32.1% | 1.5% | 3.1% | 3.7% | 7.1% | 8.8% | 7.8% | 8.4% | 26.1% | 4.1% |
| Lynn Vision | 31.6% | 1.5% | 3.0% | 3.7% | 7.0% | 8.7% | 7.7% | 8.1% | 25.8% | 3.8% |

## Rodada de abertura: três adversários mais prováveis (Bo1)

| Confronto | Time | Adversário | P(confronto) | P(vitória do convidado) |
|---|---|---|---|---|
| 1v9 | FUT | NiP | 9.0% | 56.1% |
| 1v9 | FUT | PVISION | 8.8% | 56.2% |
| 1v9 | FUT | HEROIC | 8.3% | 56.7% |
| 2v10 | Nemiga | HEROIC | 8.8% | 54.0% |
| 2v10 | Nemiga | 100 Thieves | 8.8% | 55.4% |
| 2v10 | Nemiga | Liquid | 8.7% | 54.7% |
| 3v11 | G2 | NiP | 8.0% | 52.0% |
| 3v11 | G2 | PVISION | 7.8% | 52.2% |
| 3v11 | G2 | HEROIC | 7.5% | 52.6% |
| 4v12 | THE ONE | NiP | 7.8% | 51.3% |
| 4v12 | THE ONE | PVISION | 7.8% | 51.5% |
| 4v12 | THE ONE | HEROIC | 7.7% | 51.9% |
| 5v13 | Natus Vincere | HEROIC | 7.8% | 51.6% |
| 5v13 | Natus Vincere | FaZe | 7.7% | 51.9% |
| 5v13 | Natus Vincere | Liquid | 7.7% | 52.4% |
| 6v14 | Astralis | NiP | 7.1% | 50.3% |
| 6v14 | Astralis | PVISION | 7.1% | 50.5% |
| 6v14 | Astralis | M80 | 7.1% | 53.2% |
| 7v15 | The MongolZ | PVISION | 7.1% | 49.8% |
| 7v15 | The MongolZ | NiP | 7.1% | 49.6% |
| 7v15 | The MongolZ | 100 Thieves | 6.9% | 51.7% |
| 8v16 | MIBR | Liquid | 7.1% | 50.7% |
| 8v16 | MIBR | Eternal Fire | 7.1% | 51.3% |
| 8v16 | MIBR | 100 Thieves | 7.0% | 51.4% |
