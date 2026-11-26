# Dúvidas abertas e divergências (atualizado em 26/11/2026)

"RB" = `major-supplemental-rulebook.md`. Citações completas em
[regras_suica.md](regras_suica.md). Fontes de imprensa abaixo são **secundárias**: nenhuma
foi conferida em publicação oficial da PGL ou da Valve nesta sessão.

## 1. Divergências entre o rulebook e o design (o RB vence)

### D1 — Formato do Stage 3 (bloqueia a previsão do Stage 3)
- RB L167-168: só avanço/eliminação em Bo3; "All other matches are to be best of one."
  Sem exceção para o Stage 3.
- `design-v0.md` L12: "Stage 3: tudo Bo3."
- Imprensa: [Strafe](https://www.strafe.com/news/read/cs2-singapore-major-2026-format-teams-schedule-and-opening-matches/)
  diz "All games Bo3s" para o Stage 3; para o IEM Cologne 2026, a
  [Hotspawn](https://www.hotspawn.com/counter-strike/news/iem-cologne-major-2026-bo3-format-change)
  cita um anúncio da ESL com o Stage 3 todo em Bo3 (anúncio prévio).
- **Hoje:** a engine segue o RB; `all_best_of_three=True` liga a alternativa.
- **Pergunta:** há regulamento da PGL ou anúncio oficial? Confirmado, usamos Bo3?

### D2 — Final em Bo5
- RB L211: "All matches are best of three". Design L13 e Strafe: final Bo5.
- **Pergunta:** qual a fonte oficial?

### D3 — Disputa de 3º lugar
- RB: não coberta ("Single elimination bracket", L161).
  Design L5 e L13: haverá. [Dust2.us](https://www.dust2.us/news/72698/pgl-adds-third-place-decider-match-to-singapore-major)
  noticia o anúncio, citando um post da PGL no X (não aberto por nós).
- O arquivo de exceções da Valve não lista isso para o Singapore Major (L60 só trata da
  BC.Game); a ausência não prova nada.
- **Perguntas:** formato (Bo1/Bo3)? Vale como 3º/4º no ranking final?

### D4 — Emparelhamento nas rodadas 4 e 5
- Design L17: "melhor ordenado x pior ordenado" a partir da R2.
- RB L170-188: só nas rodadas 2 e 3; nas demais, tabela de 15 prioridades.
- **Resolvido pelo RB** (implementado). Atualizar o design.

### D5 — Seed dos classificados nos Stages 2 e 3
- Design L11: "Stage 2: 8 convidados + 8 do Stage 1, seed inicial por VRS."
- RB L246-247: convidados = 1-8 pelo VRS; **classificados = 9-16 pelo seed final do
  stage anterior**.
- **Resolvido pelo RB.** Atualizar o design.

## 2. Pontos que o rulebook não resolve (hipóteses em uso)

| Id | Questão | O que o código faz hoje | Como resolver |
|---|---|---|---|
| **H1** | Rodada 3: o "melhor x pior" sequencial pode sobrar em rematch | retrocede e tenta o próximo pior | procurar um caso real (V2) ou perguntar à Valve/PGL |
| **H2** | "Seed" nas rodadas 2-5 = Mid-stage Seed dentro do grupo | implementado assim | V2 |
| **H3** | "Final seed" usa Difficulty recalculado ao fim do stage | implementado assim (evidência na tabela de Austin) | V2 / chaveamento real do Stage 2 |
| **H4** | Stage 1: seeds 1-16 = ordem relativa do VRS | quem cria o estado informa os nomes em ordem de seed | lista oficial de seeds |
| **H5** | "Posição final no Stage 3" (design §1) = seed final do stage | `position_probabilities()` | Larry confirma a definição |
| **H6** | Difficulty considera só rodadas encerradas | implementado assim | V2 |
| **H7** | Semifinais: vencedor 1v8 x 4v5 e 2v7 x 3v6, sem re-seeding | **não implementado** | confirmar antes dos playoffs |
| **H8** | Ordem entre cartéis: mais vitórias, depois menos derrotas | implementado assim | V2 |
| **H9** | `prob_fn` recebe como `team_a` o melhor ordenado | implementado assim | definir com o modelo de veto |

### D6 — Snapshot VRS do seeding
RB L239 diz "current global standing", sem data. Design e imprensa citam o VRS de
02/11/2026. TOR §3.4.4 fala da versão anunciada (aplicar ao Major é interpretação).
**Pergunta:** qual é a lista oficial de seeds dos 32 times?

### D7 — Sem pareamento sem rematch / W.O. / desqualificação
Não coberto. A engine interrompe com `NoValidPairingError`. Substituições e W.O. não são
modelados.

### D8 — Ranking final do Major (necessário só para posições finais do torneio)
Não definido como comparar quem não jogou um stage (convite direto) nem a que "Initial
Seeding" se refere (a tabela de Austin traz 29 e 37). Não implementado.

### D9 — Versão do rulebook
O arquivo local é igual ao atual da Valve (commit `745a40758e`, 06/10/2026), mas mantém
tabelas de "Winter 2025" e Austin. **Pergunta:** existe regulamento próprio da PGL para
Singapore (o RB L6 remete ao organizador)? Se sim, colocar em `docs/`.

## 3. Calendário e validação

### D10 — O Stage 1 está em andamento
Hoje é 26/11/2026. Imprensa: Stage 1 de 24 a 27/11, Stage 2 a partir de 28/11, Stage 3
de 02 a 06/12, playoffs de 10 a 13/12 (Strafe, que tem erros de mês no dia a dia; outras
fontes citam início em 25/11). **Não há modelo nem dados** para prever o Stage 1 ao vivo.
**Perguntas:** o alvo realista passa a ser o Stage 2 (M5)? Mantemos o teste V3 com dados
cortados em 23/11, mesmo que o modelo fique pronto depois do Stage 1?

### D11 — Ratings dentro da simulação
`simulate_stage` avalia `prob_fn` uma vez: a força não muda ao longo de um caminho
simulado. Resultados **reais** atualizam os ratings entre execuções. **Pergunta:** isso
atende o "ratings são atualizados a cada partida" (design §1)?

## 4. Coleta de dados

### D12 — HLTV bloqueou o scraper (403, desafio Cloudflare)
Ver [relatorio_sessao_01.md](relatorio_sessao_01.md). **Perguntas:** contornar com
navegador automatizado (SeleniumBase UC) é aceitável para você? Alguém leu os termos de
uso do HLTV (não conseguimos verificar)? Aplicou ao GRID Open Access?

### D13 — `hltv-crawler` não atende mesmo sem bloqueio
Pela auditoria do código: não extrai estatísticas por jogador **por mapa**, apaga datas
em um dos fluxos, resolve times por nome contra o ranking atual (risco de vazamento
temporal) e supõe o lado inicial CT/T. Seria preciso parser próprio.

## 5. Repositório

### D14 — O repositório remoto é público
`larrybers87/MajorCS2_previsor` está vazio e público. O push publicaria design, decisões,
documentos da Valve e o autor dos commits. Nada foi enviado. **Pergunta:** fazer push
assim, ou torná-lo privado antes?
