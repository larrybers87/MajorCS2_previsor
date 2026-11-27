# Relatório da sessão 05 — fechamento do Stage 1 e previsão do Stage 2 (27/11/2026)

## Resumo
- Previsão oficial do Stage 2 (`predictions/stage2/20261127T161221Z`) enviada em
  **27/11 16:13:36 UTC (13:13 BRT)**, horário da API do GitHub, antes do prazo (28/11
  04:00 UTC). Commit `7f8835f`.
- V2: a engine reproduz os 33 confrontos do Stage 1, e a rodada 1 listada do Stage 2
  coincide com os seeds calculados.
- **Não há previsão commitada antes do Stage 1.** A avaliação é diagnóstica e quase toda
  retrospectiva ([avaliacao_stage1.md](avaliacao_stage1.md)).
- 129 testes passam. B0, B1 e engine **não foram alterados**.

## 1. Dados do Stage 1
- O CSV local tinha **30 de 33** placares. A rodada 5 foi preenchida a partir do texto
  bruto da Wikipedia (revisão 1388316368, 27/11 15:24 UTC; cópia em
  `data/raw/wikipedia/`), **fonte secundária**: Lynn Vision 2-0 HEROIC, Imperial 2-1
  Wildcard, M80 1-2 100 Thieves. Os vencedores batem com a lista passada pelo Larry; os
  placares de mapas não entram em nenhum cálculo. Cópia do CSV anterior:
  `data/manual/stage1_results.r1-r4.bak.csv`.
- Os 33 confrontos, rodadas, formatos e os 16 cartéis conferem.
- **Uma diferença:** o quadro da partida PVISION x FlyQuest (rodada 2) na Wikipedia diz
  6-13; o CSV diz **9-13**. A tabela de rounds da própria página só fecha com 9-13, nos 16
  times. O CSV foi mantido.
- Classificados e eliminados: iguais aos esperados (BC.Game = GOSH, D15).

## 2. V2 e regras
- `tests/test_v2_real.py`: passa.
- Conferência independente (script de sessão, não versionado, escrito a partir do texto do
  RB, lendo a tabela de prioridade do próprio arquivo e os resultados da Wikipedia, sem
  usar `src/swiss`): R1 8/8, R2 8/8, R3 8/8, R4 6/6, R5 3/3, sem precisar de retrocesso.
- Controles: sem Difficulty, R3 acerta 1/8; Difficulty invertido, 2/8. "Melhor x pior" nas
  rodadas 4-5 também acerta tudo: o Stage 1 **não distingue** da tabela.
- Difficulty final calculado = coluna Buchholz da Wikipedia nos 16 times; soma zero.
- **H3 confirmada** (com a listagem secundária da rodada 1 do Stage 2): com o Difficulty
  congelado na saída de cada time, FlyQuest e NiP empatariam em +3 e NiP seria o seed 9; a
  listagem traz FUT x FlyQuest e Nemiga x NiP. Novo teste cobre isso.
- **H1 segue sem teste** (o beco sem saída não ocorreu).
- `claude/regras-verificadas.md`, citado no pedido, **não existe** no repositório; usei
  [regras_suica.md](regras_suica.md) e o rulebook.

## 3. Avaliação do Stage 1

| Conjunto | n | log loss | Brier | Favorito venceu |
|---|---:|---:|---:|---|
| Retrospectivo, rodadas 1-4 (B0 w=0) | 30 | 0,6734 | 0,2404 | 19/30 |
| Prévio, rodada 5 (média w=0/w=1) | 3 | 0,8405 | 0,3190 | 2/3 |
| Referência 50% | | 0,6931 | 0,2500 | |

Classificados: 5 de 8 (ao acaso, 4). Log score dos cartéis: soma 28,11 contra 28,41 sem
informação. Brier de avançar: 0,2495 contra 0,2500. Em resumo, **quase indistinguível de
não ter informação**, com n pequeno.

Não gerei a versão retrospectiva com as 33 partidas (passo 5 do roteiro), por causa da
instrução de não criar previsões retroativas. Pode ser rodada com autorização:
`python -m sim.v3_stage1`.

## 4. Ratings B1
`python -m sim.b1_ratings --stage1 ...`: rodada a rodada, cada rodada vê só as anteriores.
A configuração congelada **não tem decaimento temporal** (`half_life` nulo): foi a
escolhida no protocolo (H=180 ficou 0,000006 atrás no desenvolvimento). Não alterei. Maiores
mudanças: FlyQuest +29, NiP +27; DENDELE -26, FaZe -25, GOSH -24. Saída em
`data/processed/b1_major_ratings.csv`. Log loss do B1 neste Major **não** calculado
(pré-registro do Stage 3).

## 5. Seeds do Stage 2

| Seed | Time | Cartel | Difficulty | Seed no Stage 1 |
|---:|---|---|---:|---:|
| 9 | FlyQuest | 3-0 | +5 | 14 |
| 10 | NiP | 3-0 | +2 | 1 |
| 11 | Liquid | 3-1 | 0 | 5 |
| 12 | Eternal Fire | 3-1 | 0 | 6 |
| 13 | PVISION | 3-1 | -1 | 2 |
| 14 | Imperial | 3-2 | +4 | 11 |
| 15 | Lynn Vision | 3-2 | +1 | 16 |
| 16 | 100 Thieves | 3-2 | -2 | 7 |

Igual à estimativa do Larry. Convidados 1-8 pelo seed pré-evento (pontos do VRS de
02/11/2026, repositório da Valve, commit `f8c55f2`): FUT, Nemiga, G2, THE ONE, Natus
Vincere, Astralis, The MongolZ, MIBR. A lista com os mesmos números 1-8 está na
[Strafe, 12/11](https://www.strafe.com/news/read/cs2-singapore-major-2026-format-teams-schedule-and-opening-matches/)
(imprensa). A página oficial da PGL não trouxe conteúdo.

## 6. Previsão do Stage 2
200.000 simulações por extremo de w. Tabela completa em
[summary.md](../predictions/stage2/20261127T161221Z/summary.md). P(avançar), maiores: FUT
74,1%, Nemiga 64,1%, G2 60,7%, THE ONE 58,4%; menores: Lynn Vision 20,7%, FlyQuest 24,6%.
A rodada 1 da engine é igual à listada na Wikipedia (primeiro jogo 12:00 SGT de 28/11 =
04:00 UTC). Anexo D25 3x3 com o Stage 1 completo:
`predictions/anexo_d25/20261127T161324Z` (não oficial). O pedido falava em salvar em
`data/processed` e commitar; essa pasta é ignorada pelo git, então o commit é o de
`predictions/` e há uma cópia local em `data/processed/stage2_prediction/`.

## 7. Site
`python -m sim.export_site` e abrir `app/index.html`. Chave suíça do Stage 1, modo
Previsor (retrospectivo e prévio marcados), Stage 2 previsto e aba Times. O HTML só
desenha dados prontos. Em relação à referência em `docs/referencia_ui/`, ficaram de fora o
modo Simulador (calculava no navegador) e as abas Jogadores e Mapas (sem dados).
Conferido por capturas no Edge sem interface; **cliques não foram testados**.

## 8. Formato do Stage 3 (nada alterado na engine)

| Fonte | Tipo | Stage 3 todo Bo3 | Final Bo5 | 3º lugar |
|---|---|---|---|---|
| Rulebook da Valve (commit `621b7d9`, 07/10, ainda o HEAD) | **oficial** | não: Bo1 fora de avanço/eliminação (L167-168) | não: playoffs Bo3 (L211) | não trata |
| Exceções da Valve (mesmo commit) | **oficial** | nada | nada | nada (Singapore: só a região da BC.Game) |
| [Dust2.us, 10/04](https://www.dust2.us/news/72698/pgl-adds-third-place-decider-match-to-singapore-major) | imprensa | — | — | sim, anunciado pela PGL; formato não dito |
| [VDO, 09/11](https://www.vdoesports.gg/news/pgl-major-singapore-2026-schedule-format-tickets-how-watch/) | imprensa | sim | sim | não menciona |
| [GosuGamers](https://www.gosugamers.net/counterstrike/news/79519-cs2-pgl-major-singapore-2026-all-participating-teams-format-prize-pool-and-more) | imprensa | sim | sim | não menciona |
| Strafe, 12/11 (link acima) | imprensa | sim | sim | sim |
| [Pro-Gamer, 05/11](https://pro-gamer.gg/pgl-cs2-major-singapore-2026-bo5-grand-final-budapest-3rd-place-decider-format/) | imprensa | não diz | sim | sim |
| [Wikipedia](https://en.wikipedia.org/wiki/PGL_Major_Singapore_2026) | secundária | sim | sim | sim, Bo3, citando a PGL |

- **Não encontrei confirmação oficial legível.** A
  [página da PGL sobre o 3º lugar](https://news.pglesports.com/news/1775727332131-pgl-major-singapore-2026-introduces-3rd-place-decider-match-vrs-ranking-set-for-november-2)
  abriu sem conteúdo, e a de notícias da Valve também.
- A Pro-Gamer afirma que a Valve atualizou o regulamento para exigir final Bo5; o
  rulebook do repositório ainda diz Bo3. **Não verificado.**
- **Horário do Stage 3:** só as datas (2 a 6/12). Não encontrei horário oficial.
- A configuração do projeto já tem Stage 3 em Bo3 e final em Bo5 (decisão 2). Mantida.

## Em aberto
1. Confirmar os três placares da rodada 5 e a fonte usada.
2. Autorizar ou não o V3 retrospectivo com 33 partidas.
3. Confirmação oficial do formato e do horário do Stage 3 (antes de 02/12).
4. D35 (B1 com rodada pela metade); código do Stage 3 e da avaliação do Stage 2 ainda não
   escritos.
5. Regulamento da PGL (D9); H1 sem caso real; playoffs não implementados.
