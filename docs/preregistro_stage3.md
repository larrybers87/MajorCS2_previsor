# Pré-registro: modelo do Stage 3 (D26)

Escrito em 26/11/2026 (BRT); deve estar no GitHub antes de 02/12/2026.

## 1. Regra decidida (texto do Larry)

- **Modelo principal do Stage 3: média 50/50 de B0 e B1.**
- **Checagem de desastre** nos jogos dos Stages 1 e 2: se o log loss da média passar de
  0,70 ou ficar pior que o 50%, volta o B0 puro. Ela só detecta falha grosseira, não
  distingue modelos.
- **É proibido usar o teste já visto** (06 a 11/2026, `b1_avaliacao.md`) como argumento.

> **Ambiguidade a confirmar (D30):** o 50% fixo tem log loss ln 2 = 0,6931, menor que
> 0,70. Logo "passar de 0,70 **ou** ficar pior que o 50%" equivale a "passar de 0,6931": o
> limiar de 0,70 nunca decide. Até nova decisão vale o texto literal, ou seja, o limiar
> efetivo **0,6931**.

## 2. Definições operacionais PROPOSTAS (D31)

Não vieram no texto da regra; ficam fixadas aqui salvo mudança do Larry antes de 02/12.

### B0
Como no Stage 2: pontos VRS de 02/11/2026, `p = logística(beta*(rA-rB)/100)`, com
beta = **0,155760** (w=0) e **0,236080** (w=1). Calibrado até 01/11/2026.

### B1
- Configuração **congelada**: Elo com `s = 0,5`, `K = 20`, sem decaimento, `m = 2`.
- Código congelado como avaliado (commit `30a519a`: `src/models/ratings.py`,
  `src/sim/b1_ratings.py`). Os pontos apontados na revisão (P1 a P5 do relatório 03) não
  são corrigidos antes do Stage 3.
- Ratings: histórico do VRS até 01/11 e depois os resultados do Major, rodada a rodada
  (nenhuma partida vê a própria rodada). Sem ajuste de hiperparâmetro.
- `p = logística(beta1*(RA-RB)/100)`, com beta1 = **0,350419** (w=0) e **0,532006**
  (w=1), ajustados só com partidas até 01/11/2026. A regra de formato (H10) vale para o B1
  como para o B0.

### Combinação
- **Por partida:** média simples de quatro probabilidades de série: B0 w=0, B0 w=1, B1
  w=0, B1 w=1 (peso 1/4 cada, ou seja, 50/50 entre B0 e B1).
- **No stage:** simular cada uma das quatro e fazer a média das distribuições, como no
  tratamento de w no Stage 2.
- Probabilidades fixas dentro de cada simulação; os ratings do B1 são atualizados entre
  execuções, a cada resultado real. O B0 não muda.

### Checagem de desastre
- Partidas: todas as decididas dos Stages 1 e 2 (até 66), **juntas**.
- Cada probabilidade usa só o que se sabia antes da rodada: ratings do B1 até a rodada
  anterior; formato em que a partida foi jogada.
- Métrica: log loss médio da média 50/50. Calculada uma vez, depois do fim do Stage 2 e
  antes do primeiro jogo do Stage 3.
- Resultado e decisão registrados em commit antes desse jogo.

## 3. O que já se sabia ao registrar
- Resultados das rodadas 1 a 4 do Stage 1.
- Log loss do **B0** (versão w=0) nessas 30 partidas: 0,6734 (V3 retrospectivo).
- Ratings do B1 depois dessas rodadas (impressos na sessão 03).
- **Não** foram calculados o log loss do B1 nem o da média em partidas deste Major.
- Resultados de B0 e B1 no teste de 06 a 11/2026 (não podem ser usados como argumento).

Como parte das partidas da checagem (Stage 1) já era conhecida, ela não é um teste
prospectivo para o Stage 1.

## 4. Não coberto
- Modelo dos playoffs.
- Substitutos de Vitality e Legacy (decisão: tratar no Stage 3).
- O código da combinação e da checagem ainda precisa ser escrito, sem alterar o que está
  fixado aqui.
