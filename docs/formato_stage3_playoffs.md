# Formato do Stage 3 e dos playoffs — **NÃO CONFIRMADO OFICIALMENTE**

Registro de 27/11/2026. **A PGL não foi confirmada:** nenhuma página oficial com o formato
ou os horários pôde ser lida.

## Informado (fontes secundárias)

Informado pelo Larry, citando Insider Gaming e GlobalGameGuide:

| Item | Valor informado | Status |
|---|---|---|
| Stage 3 | todo em Bo3 | não confirmado |
| Datas do Stage 3 | 2 a 6/12 | não confirmado |
| Playoffs | Bo3 | não confirmado |
| Final | Bo5 | não confirmado |
| Disputa de 3º lugar | em 13/12 | não confirmado |
| Formato do 3º lugar | Bo3 | **HIPÓTESE** |

## O que cada fonte diz (conferido em 27/11)

| Fonte | Stage 3 | Datas do Stage 3 | Playoffs / final | 3º lugar |
|---|---|---|---|---|
| [Insider Gaming, 16/11](https://insider-gaming.com/pgl-singapore-major-2026-tournament-guide/) | todo Bo3 | **"December 2-13"** | Bo3, final Bo5 | **não menciona** |
| GlobalGameGuide | **não conferido:** não encontrei a página | — | — | — |
| [VDO Esports, 09/11](https://www.vdoesports.gg/news/pgl-major-singapore-2026-schedule-format-tickets-how-watch/) | todo Bo3 | 2 a 6/12 | final Bo5 em 13/12 | não menciona |
| [Pro-Gamer, 05/11](https://pro-gamer.gg/pgl-cs2-major-singapore-2026-bo5-grand-final-budapest-3rd-place-decider-format/) | não diz | não diz (fases suíças até 6/12) | final Bo5 | 13/12, antes da final; formato não dito |
| [Dust2.us, 10/04](https://www.dust2.us/news/72698/pgl-adds-third-place-decider-match-to-singapore-major) | — | — | — | anunciado pela PGL, antes da final; formato não dito |
| [Wikipedia](https://en.wikipedia.org/wiki/PGL_Major_Singapore_2026) | todo Bo3 | 2 a 6/12 | Bo3, final Bo5 | Bo3, citando a página da PGL |

Portanto, das duas fontes informadas, a Insider Gaming **sustenta** Stage 3 em Bo3,
playoffs em Bo3 e final em Bo5, **não sustenta** o 3º lugar e dá outro intervalo para o
Stage 3. O período de 2 a 6/12 e o Bo3 do 3º lugar aparecem em outras fontes secundárias.

## Fonte oficial disponível (diz outra coisa)

Rulebook da Valve (commit `621b7d9`, o mais recente em 27/11): Bo1 fora de avanço e
eliminação em todo stage suíço (L167-168); playoffs todos em Bo3 (L211); não trata de
disputa de 3º lugar. O arquivo de exceções não traz exceção de formato para este Major.

## No código

`src/sim/format_config.py`, `ACTIVE_FORMAT = "anunciado"`: Stage 3 todo em Bo3, final em
Bo5, 3º lugar ativo em Bo3 (comentado como hipótese). `"rulebook"` troca para o texto da
Valve. **Nada muda sem fonte oficial.** Horário do Stage 3: desconhecido.
