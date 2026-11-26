# Dúvidas abertas e divergências (atualizado em 26/11/2026, sessão 02)

"RB" = `major-supplemental-rulebook.md`. Citações em [regras_suica.md](regras_suica.md);
decisões em [decisoes.md](decisoes.md). Fontes de imprensa são **secundárias**.

## Abertas e urgentes

### D15 — THE ONE e GOSH no VRS (afeta a previsão do Stage 2)
A lista de times por stage (Larry, citando a Wikipedia) tem dois nomes que não casam com
o VRS de 02/11: **GOSH** não existe, e o único "the ONE" é um roster em #318 (Ásia #40),
o que violaria a ordem de convites.
- **Hipótese em uso:** THE ONE = **1win** (#12) e GOSH = **BC.Game** (#45).
- **A favor (verificado):** com ela, em cada região os convidados são os primeiros do VRS,
  sem pular ninguém, na ordem Stage 3 > 2 > 1; o arquivo de exceções da Valve declara a
  BC.Game elegível para este Major. Sem ela, a ordem é violada.
- **Não verificado:** a troca de nome em si (palpite: restrição a marcas de apostas, como
  BetBoom → BB Team e PARIVISION → PVISION).
- **Confirmar:** elencos de THE ONE e GOSH. Se errada, mudar em
  `src/sim/singapore2026.py` e rodar de novo `ingest.seeds`.

### D16 — Seeds e resultados do Stage 1
Falta `data/manual/stage1_results.csv`. Sem ele não há V2, nem V3, nem a previsão do
Stage 2 com os classificados reais. A rodada 1 valida a lista de seeds (e D15).

### D17 — Horário da primeira partida do Stage 2
A previsão precisa de commit **antes** dela. Pelo fuso de Singapura (UTC+8) e a data da
imprensa (28/11), pode ser na noite de 27/11 no Brasil (**hipótese**). Confirmar.

### D18 — Carimbo de tempo verificável e push
Os autores dos commits usam e-mail pessoal real; pela decisão 5 não houve push. Commit
local tem data editável e não prova nada a terceiros. Decidir antes do Stage 2.

## Modelo e dados

### H10 — Formato das partidas históricas
O VRS não informa Bo1/Bo3. A calibração trata todas como **Bo3** (não verificado). Se
muitas forem Bo1, o beta por mapa verdadeiro é maior que o usado (entre 0,156 e 0,236) e
as probabilidades de Bo1 estão próximas demais de 50%. As previsões trazem a coluna
"P(avançar) se H10=Bo1". **Resolver:** formato via Liquipedia (precisa do
`LIQUIPEDIA_CONTACT`) ou GRID.

### D19 — "Ratings atualizados a cada resultado" e o B0
A decisão 3 pede atualização entre execuções, mas o B0 usa pontos VRS, que não mudam
durante o Major. Hoje, entre execuções só os **fatos** são atualizados. Atualizar ratings
exige o B1 (Elo/Glicko). **Pergunta:** confirma que o B1 é o próximo passo?

### D20 — Lacunas do histórico
Sem partidas de 02/11 a 23/11; sem evento, tier e (na maioria) LAN. A seleção de tier 1-2
pedida para a Liquipedia não pode ser feita com o VRS; usamos "ambos no top 100".

### D21 — Favoritos muito fortes
No walk-forward, nas faixas acima de 80% o B0 previu 83,9% e 91,7% e observou 73,9%
(n = 46) e 75,0% (n = 4). Amostra pequena; pode ser excesso de confiança nos extremos.

### D22 — Disponibilidade real dos snapshots antigos
Não verificado se cada arquivo do VRS foi publicado na data do nome nem se foi regenerado
depois (clone raso). Verificável com o histórico completo do repositório. Não afeta a
previsão do Stage 2 (usa o snapshot de 02/11), só a calibração e o walk-forward.

### D23 — Protocolo para comparar B1 e M1 (antes de implementá-los)
No B0, a população de treino e a transformação foram escolhidas olhando os mesmos meses
avaliados (4 combinações, 0,6643 a 0,6659). Diferenças de 0,001-0,002 estão dentro do que
essa escolha produz. Para B1/M1: escolher com seleção aninhada (só meses anteriores) ou
fixar a configuração antes. Além disso, o V1 do design (cortar no dia anterior ao evento)
**não pode** ser cumprido com o VRS, que não informa o evento.

## Regras

| Id | Questão | Estado |
|---|---|---|
| **H1** | R3: "melhor x pior" pode sobrar em rematch | **aceita como provisória** (decisão 3); resolver com caso real |
| **H2** | "Seed" nas rodadas 2-5 = Mid-stage Seed no grupo | V2 pendente |
| **H3** | "Final seed" usa Difficulty recalculado ao fim do stage | V2 / chaveamento real do Stage 2 |
| **H4** | Stage 1: seeds 1-16 = ordem relativa do VRS | R1 real pendente |
| **H5** | Posição final = seed final do stage | **adotada** (decisão 3) |
| **H6** | Difficulty só com rodadas encerradas | V2 |
| **H7** | Semifinais 1v8 x 4v5 e 2v7 x 3v6, sem re-seeding | confirmar antes dos playoffs |
| **H8** | Entre cartéis: mais vitórias, depois menos derrotas | V2 |
| **H9** | `prob_fn` recebe como `team_a` o melhor ordenado | rever no modelo de veto |

- **D1-D3 — Stage 3 Bo3, final Bo5, 3º lugar:** adotados por decisão (2); o RB não os
  prevê e não vimos publicação oficial. O formato do 3º lugar (Bo3) é hipótese.
- **D4, D5 — Rodadas 4-5 e seeds dos classificados:** resolvidas pelo RB e registradas no
  design.
- **D6 — Snapshot do seeding:** usado `invitation` de 02/11/2026 (idêntico ao `live`; não
  há outro candidato). Que o Major use essa data vem do design e da imprensa.
- **D7 — Sem pareamento possível / W.O. / desqualificação:** não coberto; a engine para.
- **D8 — Ranking final do Major:** não definido para quem não jogou um stage.
- **D9 — Regulamento da PGL:** ainda não temos.

## Encerradas
- **D10** (alvo): o entregável é a previsão do Stage 2; V3 retrospectivo.
- **D11** (ratings dentro da simulação): fixos na v1.
- **D12, D13** (HLTV e `hltv-crawler`): descartados pela decisão 1.
- **D14** (repositório público): pode continuar público; ver D18.
