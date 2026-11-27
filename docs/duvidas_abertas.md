# Dúvidas abertas e divergências (atualizado em 26/11/2026, sessão 03)

"RB" = `major-supplemental-rulebook.md` (cópia local; ver [fontes_valve.md](fontes_valve.md)).
Citações em [regras_suica.md](regras_suica.md); decisões em [decisoes.md](decisoes.md).
Fontes de imprensa são **secundárias**.

## Urgentes (antes do Stage 2)

### D17 — Horário da primeira partida do Stage 2
Sábado 28/11, horário não confirmado. Pelo fuso de Singapura (UTC+8), manhã de sábado lá
é **noite de sexta no Brasil** (hipótese). A previsão precisa estar enviada antes.

### D25 — Substitutos
FUT e Astralis começam o Major com o substituto ([substitutos.md](substitutos.md)). O B0
usa os pontos VRS do elenco registrado. **Pergunta:** aceitamos assim no Stage 2 (hoje:
sim, sem ajuste)? Um ajuste exigiria ratings por jogador, que não temos.

### D28 — Qual previsão vale para avaliar o Stage 2
Há mais de uma previsão publicada. **Proposta:** vale a última enviada ao GitHub antes do
primeiro jogo do Stage 2; as anteriores são registro. Confirmar, e confirmar a métrica
(log loss por partida e log score do cartel final).

## Modelo e dados

### D24 — Termos da Liquipedia
A API MediaWiki "não é suportada" para fins que não sejam edição; os termos indicam a
LiquipediaDB, com aprovação ([h10_formato.md](h10_formato.md)). A decisão 1 da sessão 02
a listava como permitida. **Pergunta:** pedir acesso à LiquipediaDB? Abandonar?

### H10 — Formato das partidas históricas
Estimativa conjunta `w = 0,68`, intervalo [0; 1] no perfil de verossimilhança: **não
identificável** por resultados. Pela regra pré-registrada, o Stage 2 usa a média de
`w = 0` e `w = 1`. O "ponto médio" foi lido como média das probabilidades dos extremos
(D27). Só dados com formato resolvem.

### D27 — Leitura de "ponto médio"
Alternativa seria simular com `w = 0,5`. **Confirmar** a leitura adotada.

### D21 — Favoritos fortes
No teste (jun-nov/2026), acima de 80%: previsto 84,7%, observado 59,1% (n = 22, Wilson
[38,7%; 76,7%], supondo independência). Há indício de excesso de confiança. Não corrigido:
poucas partidas, e nada foi pré-registrado para corrigir. No Stage 2 poucas partidas
chegam a essa faixa.

### D26 — B1 para o Stage 3
Não adotado no Stage 2 (IC da diferença contém zero). Os defeitos apontados na revisão
(ordem dentro do dia, teto do RD, identidade) não foram corrigidos depois de ver o teste.
**Pergunta:** qual será o critério para o Stage 3? O teste já foi visto; um teste limpo
só com dados novos (por exemplo, partidas do Stage 2, poucas) ou pré-registrando
correções e aceitando que o teste atual vira desenvolvimento.

### D19 — Ratings durante o Major
O B0 não muda com os resultados. O B1 muda (`python -m sim.b1_ratings`), mas não foi
adotado.

### D20 — Lacunas do histórico
Sem partidas de 02/11 a 23/11; sem evento, tier, formato; LAN parcial.

### D22 — Disponibilidade real dos snapshots antigos
Não verificado se cada arquivo do VRS foi publicado na data do nome nem se foi regenerado.
Além disso, o B1 usa partidas até a véspera, que na fonte só aparecem em snapshot
posterior; isso o favorece na comparação.

### D23 — Protocolo de avaliação
Resolvido pelo split desenvolvimento/teste. Continua sem solução o V1 do design (corte no
dia anterior ao evento): o VRS não informa o evento.

## Regras

| Id | Questão | Estado |
|---|---|---|
| **H1** | R3: "melhor x pior" pode sobrar em rematch | provisória; **o caso não ocorreu** no Stage 1 |
| **H2** | "Seed" nas rodadas 2-5 = Mid-stage Seed no grupo | **confirmada pelos fatos** do Stage 1 (ordenar sem Buchholz ou invertido é descartado) |
| **H3** | "Final seed" usa Difficulty recalculado ao fim do stage | pendente: chaveamento real do Stage 2 |
| **H4** | Stage 1: seeds 1-16 = ordem relativa do VRS | **confirmada** (rodada 1; qualquer troca de seeds vizinhos é detectada) |
| **H5** | Posição final = seed final do stage | adotada |
| **H6** | Difficulty só com rodadas encerradas | consistente com o Stage 1 |
| **H7** | Semifinais 1v8 x 4v5 e 2v7 x 3v6, sem re-seeding | confirmar antes dos playoffs |
| **H8** | Entre cartéis: mais vitórias, depois menos derrotas | pendente |
| **H9** | `prob_fn` recebe como `team_a` o melhor ordenado | rever no modelo de veto |

- **Tabela das rodadas 4-5 x "melhor x pior":** o Stage 1 real **não distingue** as duas
  (deram os mesmos confrontos). Seguimos o RB.
- **D1-D3 — Stage 3 Bo3, final Bo5, 3º lugar:** adotados por decisão; fora do RB.
- **D7 — Sem pareamento possível / W.O.:** não coberto; a engine para.
- **D8 — Ranking final do Major:** não definido para quem não jogou um stage.
- **D9 — Regulamento da PGL:** ainda não temos.

## Encerradas
- **D4, D5:** resolvidas pelo RB. **D6:** snapshot de 02/11 validado pela rodada 1.
- **D10-D13:** ver relatórios anteriores.
- **D14, D18:** push autorizado e feito; arquivos da Valve fora do histórico.
- **D15:** THE ONE = 1win, GOSH = BC.Game (decisão 3 da sessão 03).
- **D16:** CSV do Stage 1 recebido (rodadas 1 a 4; falta o placar da 5).
