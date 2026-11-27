# Dúvidas abertas e divergências (atualizado em 26/11/2026, sessão 04)

"RB" = `major-supplemental-rulebook.md` (cópia local; ver [fontes_valve.md](fontes_valve.md)).
Citações em [regras_suica.md](regras_suica.md); decisões em [decisoes.md](decisoes.md).
Fontes de imprensa são **secundárias**.

## Urgentes (antes de 04:00 UTC de 28/11)

### D29 — Definições operacionais da avaliação (D28)
D28 não diz: (a) a probabilidade de "maior VRS fixo"; (b) o que é o "IC por bootstrap de
simulações"; (c) como pontuar o cartel se a oficial for a previsão condicionada. Propostas
em [avaliacao_stage2.md](avaliacao_stage2.md): (a) 0,595137; (b) intervalo das métricas em
torneios simulados pelo próprio modelo (intervalo esperado se o modelo estiver certo, não
IC da qualidade); (c) probabilidade condicionada à participação. **Confirmar.**

### D32 — Anexo D25: só redução conjunta
O anexo aplica a mesma redução a FUT e Astralis em cada cenário. **Pergunta:** basta, ou
quer combinações separadas? (Mudar depois do prazo deixaria de ser pré-registrado.)

## Antes de 02/12 (Stage 3)

### D30 — Checagem de desastre: limiar redundante
"Passar de 0,70 ou ficar pior que o 50%": o 50% tem log loss 0,6931 < 0,70, então o 0,70
nunca decide. Vale hoje o texto literal (limiar efetivo 0,6931). **Qual era a intenção?**
Com limiar de 0,6931 e até 66 partidas dependentes, a média pode voltar ao B0 por acaso
(o erro padrão do log loss do B0 em 30 partidas foi 0,023).

### D31 — Definições operacionais do Stage 3
Peso 1/4 para cada combinação de modelo e w; B1 congelado como avaliado, sem corrigir os
pontos P1-P5; checagem com Stages 1 e 2 juntos, calculada uma vez
([preregistro_stage3.md](preregistro_stage3.md)). **Confirmar.**

## Modelo e dados

### H10 — Formato das partidas históricas
Estimativa conjunta `w = 0,68`, intervalo [0; 1]: **não identificável** por resultados. A
previsão usa a média de `w = 0` e `w = 1` (D27 fechada). Só dados com formato resolvem, e
não há fonte em uso que os tenha.

### D21 — Favoritos fortes
No teste, acima de 80%: previsto 84,6%, observado 59,1% (n = 22; diferença -25,5 pp,
bootstrap por dias [-46,9; -6,2]). As outras faixas são compatíveis
([calibracao_teste_b0.md](calibracao_teste_b0.md)). Só diagnóstico; nada ajustado.

### D19 — Ratings durante o Major
O B0 não muda com os resultados. O B1 muda e entra no Stage 3 pela média (D26).

### D20 — Lacunas do histórico
Sem partidas de 02/11 a 23/11; sem evento, tier, formato; LAN parcial. Sem estatísticas por
jogador ou mapa ([fontes_dados.md](fontes_dados.md)).

### D22 — Disponibilidade real dos snapshots antigos
Não verificado se cada arquivo do VRS foi publicado na data do nome nem se foi regenerado.
O B1 usa partidas até a véspera, que na fonte só aparecem em snapshot posterior.

### D23 — Protocolo de avaliação
Resolvido pelo split desenvolvimento/teste. O V1 do design (corte no dia anterior ao
evento) segue sem solução: o VRS não informa o evento.

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
- **D17:** primeiro jogo do Stage 2 em 28/11, 04:00 UTC; Bo1/Bo3 confirmados pelo
  calendário (compatível com a engine).
- **D24:** GRID descartado; LiquipediaDB opcional, a cargo do Larry; nenhuma coleta nova.
- **D25:** B0 sem ajuste; anexo de sensibilidade (ver D32).
- **D26:** Stage 3 = média 50/50 de B0 e B1 (ver D30, D31).
- **D27:** média das probabilidades de w=0 e w=1.
- **D28:** vale a última previsão enviada antes do prazo (ver D29).
