# ESQUELETO — Previsão do Stage 3 e dos playoffs

> **A preencher depois do fim do Stage 2 e antes do primeiro jogo do Stage 3.** Os campos
> `⟨…⟩` estão vazios de propósito. Copiar para `docs/previsao_stage3.md` antes de
> preencher. Regras: [pré-registro](preregistro_stage3.md),
> [emenda 1](preregistro_stage3_emenda_01.md),
> [emenda 2](preregistro_stage3_emenda_02.md),
> [emenda 3](preregistro_stage3_emenda_03.md),
> [emenda 4](preregistro_stage3_emenda_04.md) e
> [adendo](adendo_preregistro_stage1.md). O script da combinação e da checagem
> **ainda não foi escrito**.

Preenchido em: ⟨data e hora⟩ · pasta: `predictions/stage3/⟨carimbo⟩` · commit: ⟨hash⟩ ·
push: ⟨horário da API do GitHub⟩ · primeiro jogo: ⟨data, hora e fonte⟩

## 0. Conferências
| Item | Valor |
|---|---|
| Stage 2 completo no CSV (SHA-256) | ⟨⟩ |
| V2 do Stage 2 | ⟨⟩ |
| Código e configuração do B1 iguais aos congelados (`30a519a`) | ⟨⟩ |
| Formato confirmado oficialmente? | ⟨sim, fonte / não⟩ |
| `ACTIVE_FORMAT` usado | ⟨anunciado / rulebook⟩ |

## 1. Checagem de desastre (uma vez, antes deste modelo)

Partidas dos Stages 1 e 2 juntas: ⟨n⟩ (até 66). Cada probabilidade usa só rodadas
anteriores; formato em que a partida foi jogada.

| Condição | Valor | Vale? |
|---|---|---|
| (a) log loss da média 50/50 − ln 2: média ⟨⟩; quantil de 5% do bootstrap (10.000, semente 20261202) ⟨⟩ > 0 | ⟨⟩ | ⟨⟩ |
| (b) log loss do B1 − log loss do B0 > 0 (cada um com a média de w) | ⟨⟩ | ⟨⟩ |

| (a) | (b) | Consequência |
|---|---|---|
| sim | sim | voltar ao B0 puro |
| sim | não | relatar falha dos dois; não trocar nada |
| não | qualquer | manter a média 50/50 |

**Resultado:** ⟨⟩.

## 2. Modelo usado
- ⟨média 50/50 de B0 e B1 / B0 puro⟩.
- Na média: quatro simulações (B0 w=0 beta 0,155760; B0 w=1 beta 0,236080; B1 w=0 beta
  0,350419; B1 w=1 beta 0,532006) e média das distribuições, peso 1/4 cada.
- B0: pontos VRS de 02/11. B1: Elo s=0,5, K=20, sem decaimento, m=2, com os resultados dos
  Stages 1 e 2; probabilidades fixas dentro de cada simulação.
- Simulações: ⟨n⟩ por variante; semente: ⟨definir antes de ver os seeds⟩.

## 3. Participantes e seeds

| Seed | Time | Origem | VRS | Rating B1 | Observação |
|---:|---|---|---:|---:|---|
| 1 | MOUZ | convidado | 1960 | ⟨⟩ | |
| 2 | Vitality | convidado | 1922 | ⟨⟩ | substituto registrado (imprensa; ver substitutos) |
| 3 | FURIA | convidado | 1912 | ⟨⟩ | |
| 4 | Aurora | convidado | 1860 | ⟨⟩ | |
| 5 | Spirit | convidado | 1842 | ⟨⟩ | |
| 6 | BB Team | convidado | 1786 | ⟨⟩ | |
| 7 | Falcons | convidado | 1764 | ⟨⟩ | |
| 8 | Legacy | convidado | 1662 | ⟨⟩ | substituto registrado (imprensa; ver substitutos) |
| 9–16 | ⟨classificados, pelo seed final do Stage 2⟩ | Stage 2 | ⟨⟩ | ⟨⟩ | |

Reservas de Vitality e Legacy ([emenda 3](preregistro_stage3_emenda_03.md)): **o modelo
oficial não é ajustado**. A sensibilidade vai na seção 6-A, à parte.

## 4. Rodada de abertura (1v9 … 8v16)

| Seeds | Time A | Time B | Bo | P(A), modelo oficial | Confere com o anúncio? |
|---|---|---|---|---:|---|
| ⟨8 linhas⟩ | | | | | |

## 5. Fase suíça

| Time | 3-0 | 3-1 | 3-2 | 2-3 | 1-3 | 0-3 | P(avançar) oficial | faixa na sensibilidade (mín. – máx.) |
|---|---|---|---|---|---|---|---|---|
| ⟨16 linhas⟩ | | | | | | | | |

Posição final na suíça (P de cada posição, 1 a 16): ⟨arquivo⟩.

## 6. Playoffs

| Time | Quartas | Semifinal | Final | Título | 3º | 4º |
|---|---|---|---|---|---|---|
| ⟨16 linhas⟩ | | | | | | |

Hipóteses: semifinais por chave, sem reordenar seeds (H7); **3º lugar em Bo3
(hipótese)**; final em Bo5 conforme [formato](formato_stage3_playoffs.md). Modelo dos
playoffs: **não coberto pelo pré-registro** — ⟨decidir antes de preencher⟩.

## 6-A. Sensibilidade aos reservas (NÃO é a previsão oficial)

[Emenda 4](preregistro_stage3_emenda_04.md): grade 3x3 (Vitality 0, −25, −50; Legacy 0,
−50, −100 pontos VRS, com o equivalente no B1). Publica-se **só** o oficial e a faixa
mínima-máxima de P(avançar) por time (coluna da seção 5); os cenários não são publicados.
Cenário sem desconto igual à oficial? ⟨sim/não⟩. A troca de titular não foi confirmada
pela PGL; ksloks não tem partida alguma com a Legacy no histórico.

## 7. Limites
Sem mapas, veto, forma por jogador nem ajuste a substitutos; probabilidades fixas dentro
da simulação; no teste histórico o B0 foi confiante demais acima de 80% (n pequeno); o
desempenho no Stage 1 era conhecido ([adendo](adendo_preregistro_stage1.md)). ⟨outros⟩

## 8. Publicação
Commit e push **antes** do primeiro jogo; mostrar os autores antes do push; registrar o
horário do push. Pasta nova, nunca sobrescrita.
