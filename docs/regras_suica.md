# Regras da fase suíça (e playoffs) com citações

Fonte: `docs/major-supplemental-rulebook.md` ("RB"; L = linhas), cópia local **não
versionada**; ver [fontes_valve.md](fontes_valve.md) para versão, hash e como baixar.
Em 26/11/2026 o arquivo local era **idêntico** ao do repositório
`ValveSoftware/counter-strike_rules_and_regs` (último commit do arquivo: `745a40758e`,
06/10/2026). Mesmo assim a tabela de convites ainda é a de "Winter 2025" (L42) e a de
resultados é a de Austin 2025 (L606). Ver [duvidas_abertas.md](duvidas_abertas.md).

Extração feita com o papel `rules-auditor` e conferida na implementação.

**Legenda:** **VERIFICADO** = o texto diz; **DEDUZIDO** = consequência aritmética do
texto; **HIPÓTESE (Hn)** = exige uma leitura nossa; **NÃO COBERTO** = o texto não trata.

---

## 1. Emparelhamento

### 1.1 Regras gerais — VERIFICADO (seção "Swiss Bracket", L164-170)
> "Teams play against opponents of identical W-L record."
> "Three wins advance---Three losses eliminate"
> "Teams are not to play the same opponent twice in the same stage, if possible."

### 1.2 Rodada 1 — VERIFICADO (L170 e "Initial Swiss Match-ups", L190-202)
1v9, 2v10, 3v11, 4v12, 5v13, 6v14, 7v15, 8v16 (seeds iniciais do stage).

### 1.3 Rodadas 2 e 3 — VERIFICADO (L170)
> "In round 2 and 3, the highest seeded team faces the lowest seeded team available
> that does not result in a rematch within the stage."

- **H2:** aplica-se dentro de cada grupo de cartel; "seed" é o *Mid-stage Seed* (§2).
  Pareia-se o melhor ordenado, depois o melhor restante, e assim por diante.
- **DEDUZIDO:** na rodada 2 não há rematch possível; na 3, só no grupo 1-1 e apenas
  contra o adversário da rodada 1.
- **NÃO COBERTO — beco sem saída:** a escolha sequencial pode deixar como último par um
  rematch, embora exista solução sem rematch. A verificação exaustiva (§7) mostra a
  frequência. Exemplo (teste `test_round_three_dead_end_uses_backtracking`): grupo 1-1
  ordenado 1, 2, 3, 12, 4, 9, 10, 11; a sequência 1v11, 2v9, 3v10 sobra 12v4 (rematch).
- **H1 (implementada):** volta-se atrás e o adversário do melhor ordenado ainda
  disponível passa ao próximo pior que permita completar o grupo (no exemplo: 1v11,
  2v9, **3v4, 12v10**). Outras leituras são possíveis.

### 1.4 Rodadas 4 e 5 — VERIFICADO (L170-188)
> "In other rounds, refer to the following table and select the top-most row that does
> not result in a rematch"

| Prioridade | Pares | Prioridade | Pares | Prioridade | Pares |
|:--:|---|:--:|---|:--:|---|
| 1 | 1v6 2v5 3v4 | 6 | 1v4 2v5 3v6 | 11 | 1v4 2v3 5v6 |
| 2 | 1v6 2v4 3v5 | 7 | 1v6 2v3 4v5 | 12 | 1v3 2v4 5v6 |
| 3 | 1v5 2v6 3v4 | 8 | 1v5 2v3 4v6 | 13 | 1v2 3v6 4v5 |
| 4 | 1v5 2v4 3v6 | 9 | 1v3 2v6 4v5 | 14 | 1v2 3v5 4v6 |
| 5 | 1v4 2v6 3v5 | 10 | 1v3 2v5 4v6 | 15 | 1v2 3v4 5v6 |

- As 15 linhas são exatamente os 15 pareamentos possíveis de 6 times (testado).
- **H2:** "other rounds" = 4 e 5; 1 a 6 = posição dentro do grupo (2-1, 1-2 ou 2-2)
  pelo Mid-stage Seed.
- A tabela **não** equivale a "melhor x pior disponível": difere já na ordem das linhas
  (caso testado na rodada 5 em `test_favorites_path_round_by_round`).

## 2. Difficulty Score (Buchholz) e ordenação

### 2.1 Definição — VERIFICADO ("Difficulty Score (Buchholz)", L262-272)
> "The Difficulty Score is the sum of current wins minus the sum of current losses for
> every opponent a team has faced."

### 2.2 Ordem — VERIFICADO ("Mid-stage Seed Calculation", L256-260)
> "For all Swiss match-ups, after the initial matches, seed is determined (in order) by:"
> 1. "Current W-L record in the stage" 2. "Difficulty Score in the current stage"
> 3. "Initial seeding of the current stage"

### 2.3 Direção — VERIFICADO (L272)
> "Team A gets the higher seed because it played against teams that were more difficult
> to defeat."

Maior Difficulty = melhor seed. Empate: menor número de seed inicial. Como os seeds são
únicos, não sobra empate. Não há confronto direto nem saldo de mapas/rounds.

### 2.4 Momento do cálculo
- **H6:** recalculado antes de cada rodada com os cartéis ao fim da rodada anterior;
  partidas não decididas não contam; zera a cada stage.
- **H3 (com evidência):** o valor final de quem saiu cedo continua mudando enquanto os
  adversários jogam. Na tabela de Austin, FURIA (3-0) tem D = -2 (L614) e Liquid (0-3)
  tem D = 0 (L625); ao fim da rodada 3 a soma de três saldos ímpares seria ímpar.
- **H8:** entre cartéis diferentes: mais vitórias, depois menos derrotas
  (3-0 > 3-1 > 3-2 > 2-3 > 1-3 > 0-3). Compatível com a tabela de Austin.

## 3. Seeding

**Atualização de 27/11:** H3 e a parte de H8 entre os classificados foram confirmadas pela
rodada 1 do Stage 2 listada antes dos jogos (Wikipedia, fonte secundária); ver o fim
deste documento. A tabela abaixo mantém o status pelo texto do rulebook.

| Item | Status | Texto |
|---|---|---|
| Seed pré-evento: 32 times pelo VRS **global** | VERIFICADO (L53, L239) | "sorted based on their current global standing in the VRS" |
| Stage 1 usa o seed pré-evento | VERIFICADO (L243-244) | "All teams will use their pre-event seed." |
| Stage 1 renumerado 1-16 mantendo a ordem relativa | **H4** | o texto não explicita a renumeração |
| Stages 2 e 3: convidados = seeds 1-8 pelo pré-evento | VERIFICADO (L246, L250) | "will be seeds 1-8, and use their pre-event seed" |
| Stages 2 e 3: classificados = seeds 9-16 | VERIFICADO (L247, L251) | "will be seeds 9-16 and use their final seed from the previous stage" |
| "Final seed" = ordem de §2 ao fim do stage anterior; 1º vira 9, 8º vira 16 | **H3** | decorre da remissão ao Mid-stage Seed |
| Data do snapshot VRS | NÃO COBERTO no RB | `tournament-operation-requirements.md` §3.4.4 fala da versão anunciada; aplicar ao Major é interpretação |

## 4. Formato das partidas

### VERIFICADO (L167-168)
> "All elimination and advancement matches are to be best of three."
> "All other matches are to be best of one."

- **DEDUZIDO:** Bo3 em 2-0 e 0-2 (R3), 2-1 e 1-2 (R4) e 2-2 (R5); Bo1 em R1, R2 e no
  grupo 1-1. Por stage: 20 Bo1 e 13 Bo3.
- **Não há exceção para o Stage 3 no RB.** O design e fontes secundárias dizem que o
  Stage 3 é todo Bo3 (dúvida D1). A engine segue o RB por padrão e oferece
  `StageState(all_best_of_three=True)`.

### Veto — VERIFICADO ("Map Pick-Ban", L213-233; será usado pelo modelo)
- O melhor seed escolhe ser Team A ou B.
- Bo1: A bane 2; B bane 3; A bane 1; B escolhe o lado.
- Bo3: A bane 1; B bane 1; A escolhe o mapa 1 (B o lado); B escolhe o mapa 2 (A o lado);
  B bane 1; A bane 1; B escolhe o lado no mapa 3.
- NÃO COBERTO: veto de Bo5; como o melhor seed decide entre A e B.

## 5. Playoffs (implementados em `src/sim/playoffs.py`)

Testes em `tests/test_playoffs.py`. O formato vem de `src/sim/format_config.py`
(`ACTIVE_FORMAT`: `anunciado`, atual, ou `rulebook`).

| Item | Status | Texto |
|---|---|---|
| Eliminação simples com o top 8 do Stage 3 | VERIFICADO (L160-162) | "Single elimination bracket", "Top 8 from Stage 3" |
| Seeds = seed final do Stage 3 (cartel, Difficulty, seed inicial) | VERIFICADO (L253-254 + L256-260) | "All teams will use their final seed from Stage 3" |
| Quartas: A = 1v8 e 4v5; B = 2v7 e 3v6 | VERIFICADO (L204-210) | |
| Semifinais dentro de cada bracket; final A x B; sem re-seeding | **H7** | o texto não escreve os cruzamentos |
| Todas as partidas Bo3 | VERIFICADO (L211) | "All matches are best of three" |
| Final em Bo5 | **Não consta no RB** (contradiz L211) | dúvida D2 |
| Disputa de 3º lugar | NÃO COBERTO | a tabela de Austin tem dois "3rd" (L611-612); dúvida D3 |
| 3º lugar em **Bo3** | **HIPÓTESE** (só fonte secundária; PGL não confirmada) | [formato_stage3_playoffs.md](formato_stage3_playoffs.md) |

## 6. Ranking final do Major — VERIFICADO ("Final Rankings", L594-604)
Ordem: posição nos playoffs; cartel S3; Difficulty S3; cartel S2; Difficulty S2; cartel
S1; Difficulty S1; seed inicial. **NÃO COBERTO:** como comparar quem não jogou um stage
(convite direto) e a que "Initial Seeding" se refere (a coluna de Austin traz 29 e 37,
L636-637). Ver D8.

## 7. Quantidades

**DEDUZIDO** do formato (16 times, sem empates nem W.O.); o RB não afirma estes números:
partidas por rodada 8, 8, 8, 6, 3 (**33**); **8** classificados e **8** eliminados;
cartéis **2** 3-0, **3** 3-1, **3** 3-2, **3** 2-3, **3** 1-3, **2** 0-3. A tabela de
Austin confirma 3/3/2 entre os eliminados nos três stages (L618-643). A soma dos
Difficulty Scores finais dos 16 times é zero.

### Verificação exaustiva dos emparelhamentos
`python -m swiss.exhaustive_check` percorre todos os caminhos de resultados:

Resultado em 26/11/2026 (12 núcleos, cerca de 20 minutos):

| Verificação | Resultado |
|---|---|
| R3: o "melhor x pior" sem retrocesso trava | **400 de 65.536** combinações de resultados das rodadas 1 e 2 (0,61%) |
| R4: existe emparelhamento sem rematch | sim, nos 16.777.216 históricos |
| R5: existe emparelhamento sem rematch | sim, nos 1.073.741.824 históricos |

Os percentuais contam combinações com peso igual; não são a probabilidade real de o caso
ocorrer. Os históricos usam a resolução H1 na rodada 3.

**NÃO COBERTO:** o que fazer se não houver pareamento sem rematch (desistência,
desqualificação, erro do organizador). A engine levanta `NoValidPairingError`.

## 8. Mapa regra → código → teste

| Regra | Código (`src/swiss`) | Teste |
|---|---|---|
| Rodada 1 | `rules.ROUND_ONE_SEED_PAIRS`, `engine.pair_round` | `test_round_one_is_1v9_to_8v16` |
| R2-R3 e H1 | `engine._pair_high_low` | `test_round_three_dead_end_uses_backtracking` |
| Tabela R4-R5 | `engine._pair_by_table` | `test_table_picks_topmost_row_without_rematch`, `test_favorites_path_round_by_round` |
| Buchholz e ordem | `engine.buchholz`, `engine.standings` | `test_favorites_path_round_by_round`, `test_higher_buchholz_ranks_first_within_record` |
| Bo1/Bo3 | `rules.is_decider_match`, `rules.best_of` | `test_decider_matches_are_best_of_three` |
| Invariantes | engine | `test_invariants_over_random_stages` |
| Versão vetorizada = referência | `simulate._pair_round_batch` | `test_vectorized_pairing_matches_reference_engine` |
| Emparelhamentos reais (V2) | `engine.check_pairings` | `tests/test_v2_real.py` (precisa do CSV local) |

### V2 com o Stage 1 deste Major (26/11/2026)
Os **33 confrontos** das rodadas 1 a 5 coincidem com os da engine (30 jogados e os 3
anunciados da rodada 5). Isso confirma H4 e o uso e a direção do Buchholz; **não**
testa H1 (o beco sem saída não ocorreu), nem distingue a tabela das rodadas 4-5 do
"melhor x pior", nem testa H3 e H8.

### V2 com o Stage 1 completo (27/11/2026)
Os **33 confrontos jogados** coincidem com a engine e com uma segunda implementação feita
só a partir do texto do RB (script de sessão, não versionado): R1 8/8, R2 8/8, R3 8/8, R4
6/6, R5 3/3. Sem Difficulty, ou com ele invertido, a rodada 3 falha (1/8 e 2/8). Os
Difficulty finais batem com a tabela da Wikipedia.

A rodada 1 do Stage 2 listada (FUT x FlyQuest, Nemiga x NiP, G2 x Liquid, THE ONE x
Eternal Fire, Natus Vincere x PVISION, Astralis x Imperial, The MongolZ x Lynn Vision,
MIBR x 100 Thieves) exige o Difficulty **recalculado ao fim do stage** (H3): congelado na
saída, NiP passaria à frente de FlyQuest. Teste:
`test_v2_stage2_listed_round_one_confirms_final_seeds`.
