# EMENDA 1 ao pré-registro do Stage 3 (D30 e D31)

Escrita em 26/11/2026, 21:45 BRT, antes de 02/12. O original,
[preregistro_stage3.md](preregistro_stage3.md), **não foi reescrito**. Onde houver
diferença, vale esta emenda.

## E1.1 Checagem de desastre (substitui a regra do item 1 e o aviso D30)

Motivo (planejamento): o limiar de 0,70 foi um erro; ele nunca decide, porque o 50% fixo
tem log loss 0,6931.

**Voltar ao B0 puro somente se (a) E (b):**
- **(a)** a média 50/50 tiver log loss **pior que o 50%** com significância **unilateral de
  95%** (bootstrap por partidas);
- **(b)** o **B1 sozinho for pior que o B0** nas mesmas partidas (diferença pontual).

| (a) | (b) | Consequência |
|---|---|---|
| sim | sim | voltar ao B0 puro |
| sim | não | relatar como **falha dos dois modelos**; não trocar nada |
| não | sim ou não | manter a média 50/50 |

### Detalhes operacionais PROPOSTOS (não vieram na regra)
- Partidas, informação disponível e formato: como no item 2 do original (todas as decididas
  dos Stages 1 e 2, juntas, até 66).
- (a): `d_i = log loss da média na partida i - ln 2`; reamostrar partidas com reposição,
  10.000 réplicas, semente 20261202; (a) vale se o quantil de 5% da média reamostrada de
  `d` for maior que zero.
- (b): B1 = média das probabilidades de w=0 e w=1; B0 idem; vale se
  `log loss(B1) - log loss(B0) > 0`.
- O bootstrap por partidas trata as partidas como independentes, o que não são.

## E1.2 Definições confirmadas (D31)
- Peso **1/4** para cada combinação (B0, B1) x (w=0, w=1).
- **Hiperparâmetros e código do B1 congelados**; ratings atualizados em walk-forward
  **até a véspera de cada rodada**.

### Ponto a confirmar (D33)
O original diz "rodada a rodada (nenhuma partida vê a própria rodada)", e é o que o código
congelado faz: cada rodada conta como um dia, e a rodada r vê todas as anteriores, mesmo
que duas rodadas caiam no mesmo dia do calendário. "Até a véspera" pode ser lido como
excluir também a rodada anterior jogada no mesmo dia, o que exigiria mudar o uso do
código. **Leitura adotada salvo resposta antes de 02/12: a do original (todas as rodadas
anteriores).**
