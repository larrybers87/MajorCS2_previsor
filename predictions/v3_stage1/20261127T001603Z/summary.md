# V3 — Stage 1 (RETROSPECTIVO)

Gerado **depois** das partidas: não é previsão. O B0 usa só o VRS de 02/11/2026 e beta calibrado em partidas até 2026-11-01; nada foi ajustado com o Stage 1. Com no máximo 33 partidas, o resultado NÃO permite comparar modelos.

Partidas decididas: 30 de 33; stage na rodada 5.

## Validação das regras

- Rodada 1 real = 1v9 ... 8v16 com os nossos seeds: **sim**
- V2, rodadas 2 a 5: **sem divergências**.

## Métricas

| Métrica | Valor |
|---|---|
| partidas | 30 |
| log_loss | 0.6734 |
| log_loss_erro_padrao | 0.0227 |
| log_loss_50 | 0.6931 |
| brier | 0.2404 |
| brier_50 | 0.2500 |
| brier_maior_vrs_vence | 0.3667 |
| acerto_do_favorito | 0.6333 |

## Previsto desde a rodada 1 x observado

| Seed | Time | P(3-0) | P(3-1) | P(3-2) | P(2-3) | P(1-3) | P(0-3) | P(avançar) | Observado | P(observado) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | NiP | 17.6% | 23.5% | 21.1% | 16.1% | 13.9% | 7.7% | 62.3% | 3-0 | 17.6% |
| 2 | PVISION | 17.4% | 23.5% | 20.8% | 16.3% | 14.2% | 7.8% | 61.8% | 3-1 | 23.5% |
| 3 | HEROIC | 17.1% | 23.0% | 20.5% | 16.8% | 14.6% | 8.0% | 60.6% | 2-2 (em jogo) | - |
| 4 | FaZe | 16.5% | 22.4% | 20.7% | 17.0% | 15.1% | 8.3% | 59.6% | 1-3 | 15.1% |
| 5 | Liquid | 16.2% | 22.0% | 20.6% | 17.2% | 15.5% | 8.6% | 58.8% | 3-1 | 22.0% |
| 6 | Eternal Fire | 15.3% | 21.4% | 20.2% | 18.0% | 16.2% | 8.9% | 57.0% | 3-1 | 21.4% |
| 7 | 100 Thieves | 15.8% | 21.6% | 20.1% | 17.8% | 16.0% | 8.8% | 57.5% | 2-2 (em jogo) | - |
| 8 | 9z | 14.7% | 20.7% | 19.7% | 18.6% | 16.8% | 9.5% | 55.1% | 1-3 | 16.8% |
| 9 | M80 | 12.3% | 19.7% | 20.4% | 18.2% | 18.0% | 11.4% | 52.3% | 2-2 (em jogo) | - |
| 10 | DENDELE | 11.4% | 18.8% | 19.9% | 18.8% | 18.9% | 12.1% | 50.1% | 0-3 | 12.1% |
| 11 | Imperial | 9.5% | 16.7% | 18.3% | 20.1% | 20.9% | 14.5% | 44.6% | 2-2 (em jogo) | - |
| 12 | Wildcard | 9.1% | 16.1% | 17.8% | 20.3% | 21.5% | 15.1% | 43.0% | 2-2 (em jogo) | - |
| 13 | GOSH | 7.6% | 14.0% | 16.3% | 20.9% | 23.4% | 17.8% | 37.9% | 0-3 | 17.8% |
| 14 | FlyQuest | 7.2% | 13.4% | 15.6% | 21.1% | 24.0% | 18.8% | 36.1% | 3-0 | 7.2% |
| 15 | Chinggis Warriors | 6.1% | 11.6% | 14.1% | 21.4% | 25.5% | 21.3% | 31.9% | 1-3 | 25.5% |
| 16 | Lynn Vision | 6.0% | 11.6% | 13.9% | 21.6% | 25.6% | 21.4% | 31.5% | 2-2 (em jogo) | - |

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
