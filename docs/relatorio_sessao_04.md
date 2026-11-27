# Relatório da sessão 04 — registros, diagnóstico e pré-registros (26/11/2026)

## Resumo
- Quatro tarefas feitas; falta só a execução de sexta, que depende da rodada 5.
- Anexo D25 e pré-registro do Stage 3 **no GitHub** (push de 27/11 00:30:52 UTC), antes
  da rodada 5 do Stage 1.
- Nenhum conflito entre as regras e o código. B0 e engine **não foram alterados**.
- Há um ponto na regra D26 a corrigir ou confirmar (limiar redundante, D30).
- 121 testes passam.

## 1. Decisões registradas ([decisoes.md](decisoes.md))
D17, D24 (GRID descartado; LiquipediaDB opcional; nenhuma coleta além do VRS e dos
resultados do Major), D25, D26, D27 e D28. Novo [fontes_dados.md](fontes_dados.md):
**estatísticas por jogador e por mapa fora do escopo** até haver fonte permitida; com isso
o M1 do design não pode ser construído como descrito.

- **D17 x engine:** compatível (rodada 3 com 4 Bo1 e 4 Bo3). A ordem dos jogos no
  calendário não afeta a engine.
- **Substitutos:** texto atualizado como pedido. gambling.com e pley.gg foram informados
  por você; não abri essas páginas nem tenho os links.

## 2. Calibração do B0 no teste ([calibracao_teste_b0.md](calibracao_teste_b0.md))
1.479 partidas, 01/06 a 01/11. Modelo da manchete (média de w=0 e w=1):

| Faixa | n | previsto | observado | IC 95% (Wilson) | observado − previsto (IC por dias) |
|---|---:|---:|---:|---|---|
| 50-60% | 912 | 54,6% | 55,9% | [52,7; 59,1] | +1,3 pp [-2,1; +4,7] |
| 60-70% | 429 | 64,1% | 68,1% | [63,5; 72,3] | +3,9 pp [-0,6; +8,5] |
| 70-80% | 116 | 73,9% | 75,0% | [66,4; 82,0] | +1,1 pp [-7,4; +9,6] |
| **80%+** | **22** | **84,6%** | **59,1%** | [38,7; 76,7] | **-25,5 pp [-46,9; -6,2]** |

Só a faixa acima de 80% destoa; w=0 e w=1 mostram o mesmo. São poucas partidas e várias
comparações. **Só diagnóstico; nada ajustado.**

## 3. Anexo D25 ([protocolo](anexo_d25_protocolo.md))
Redução igual para FUT e Astralis, só nas probabilidades (seeds intactos). **-50 e -100
são arbitrários.** Versão condicionada (30 partidas), cenário 0 conferido com a previsão
publicada (diferença só de arredondamento):

| Time | 0 | -50 | -100 |
|---|---:|---:|---:|
| FUT | 72,9% | 68,3% | 63,5% |
| Astralis | 54,9% | 49,6% | 44,3% |

Os demais times sobem no máximo cerca de 2 pontos percentuais.

## 4. Pré-registro do Stage 3 ([preregistro_stage3.md](preregistro_stage3.md))
Texto da regra e definições propostas, com os betas fixados (B0 0,155760 e 0,236080; B1
0,350419 e 0,532006), calculados só com dados até 01/11. Registra o que já se sabia
(inclusive o log loss do B0 no Stage 1). O log loss do B1 e da média neste Major **não**
foi calculado.

**Limiar redundante (D30):** o 50% tem log loss 0,6931, abaixo de 0,70; o 0,70 nunca
decide. Registrei o texto literal.

**Código do Stage 3:** ainda não escrito.

## 5. Roteiro de sexta ([roteiro_sexta.md](roteiro_sexta.md))
- Ensaio completo, com rodada 5 fictícia em cópia do CSV: **88 s**, incluindo a variante
  com a rodada 1 anunciada; `git push --dry-run` autenticou. Nada do ensaio foi para o
  projeto.
- Meta: enviar até **sexta 18:00 BRT**; prazo **sábado 01:00 BRT**.
- **Folga:** se a rodada 5 começar sexta 01:00 BRT, como a primeira rodada do dia 24
  (hipótese minha), deve acabar bem antes das 18:00. Não verifiquei o horário.
- Se nada mais for enviado, vale a previsão condicionada `20261127T001433Z`.

## 6. Definições que propus para D28 ([avaliacao_stage2.md](avaliacao_stage2.md))
"Maior VRS fixo" = 59,5137% (taxa histórica no top 100); "bootstrap de simulações" =
intervalo das métricas em torneios simulados pelo próprio modelo (esperado se o modelo
estiver certo, não IC da qualidade); oficial condicionada pontuada com probabilidade dada
a participação. O código da avaliação não foi escrito.

## 7. Não feito
Execução de sexta; anexo com o Stage 1 completo; código de avaliação do Stage 2 e do
Stage 3. Não usei o `leakage-reviewer` nos dois módulos novos (não ajustam modelo).

## 8. Perguntas
1. **Antes do prazo:** confirma as definições de D28 (D29)?
2. **Antes do prazo:** o anexo D25 basta com a redução conjunta (D32)?
3. Checagem de desastre: o que se pretendia com 0,70 (D30)?
4. Confirma as definições do Stage 3 (D31)?
5. Tem os links de gambling.com e pley.gg para registrar?

**Parado aqui, aguardando.**

---

## Adendo: respostas de 26/11 21:45 BRT

### Feito
- **Três emendas em arquivos novos**, sem reescrever os originais, enviadas em 27/11
  00:41:22 UTC (`a9e0eed`): [Stage 3](preregistro_stage3_emenda_01.md) (checagem de
  desastre corrigida; D31 confirmada), [anexo D25](anexo_d25_emenda_01.md) (grade 3x3) e
  [avaliação](avaliacao_stage2_emenda_01.md) (bootstrap pareado por partidas; intervalo
  por simulações = teste de consistência).
- **59,5% conferido:** 3.084/5.182, partidas de 01/06/2025 a 01/11/2026, antes do corte
  (23/11) e do evento; ratings de snapshots anteriores a cada partida.
- **Anexo 3x3** (condicionado), cenário (0, 0) igual à previsão publicada:

| FUT \ Astralis | FUT avança (0 / -50 / -100) | Astralis avança (0 / -50 / -100) |
|---|---|---|
| FUT 0 | 72,9 / 73,1 / 73,3 | 54,9 / 49,3 / 43,7 |
| FUT -50 | 68,1 / 68,3 / 68,6 | 55,2 / 49,6 / 44,0 |
| FUT -100 | 62,9 / 63,2 / 63,5 | 55,5 / 49,9 / 44,3 |

- Roteiro ensaiado de novo: **159 s**.

### Correções
- **Rodada 5 do Stage 1:** sexta às 03:00, 05:30 e 08:00 BRT. O item 5 acima supunha
  01:00; estava errado. A previsão (21:14) e o anexo de quinta são anteriores a ela.
- **84,7% x 84,6% (faixa acima de 80%):** são modelos diferentes. 84,7% é só w=0 (D21, sessão
  03); 84,6% é a média de w=0 e w=1, usada na manchete (w=1 sozinho: 84,4%). Conferido:
  as **mesmas 22 partidas** e o mesmo observado (59,1%) nas três versões.

### Substitutos ([substitutos.md](substitutos.md))
Abriram a gambling.com e as duas páginas da Strafe; **pley.gg e as três da rg.org
recusaram (403)**. Achado: cmtry foi para a Astralis, mas segue no elenco VRS da FUT.
SunPayus (FUT) é quem vinha jogando no lugar dele; Anlelele (Astralis) é um empréstimo
para cobrir a ausência dele. A redução do anexo faz mais sentido para a Astralis que para
a FUT. A gambling.com conta quatro substituições, as outras fontes cinco.

### Perguntas em aberto
- **D34 (antes de 28/11 04:00 UTC):** log score do cartel sem bootstrap por partidas:
  basta diferença pontual e teste de consistência?
- **D33 (antes de 02/12):** "véspera de cada rodada" exclui a rodada anterior do mesmo
  dia?

**Parado aqui, aguardando o relatório de sexta.**

---

## Adendo 2: respostas de 26/11 22:00 BRT

- **Três emendas 2** em arquivos novos (originais e emendas 1 intactos):
  [anexo](anexo_d25_emenda_02.md), [avaliação](avaliacao_stage2_emenda_02.md) e
  [Stage 3](preregistro_stage3_emenda_02.md). Réplicas e sementes fixadas.
- **Substitutos:** a leitura sobre FUT x Astralis passou a **especulação**.
- **Dois pares de "-100":** células diferentes, não mudança de resultado. (-100, -100): FUT
  63,5%, Astralis 44,3% (anexo original). (-100, 0): FUT 62,9%. (0, -100): Astralis
  43,7%. A frase do adendo anterior juntou as duas últimas sem avisar; erro de redação meu.
  Células iguais conferidas nos CSVs (diferença 0).
- **Referência de P2:** a fronteira de dia do backtest é a regra "Sem informação do mesmo
  dia" do protocolo; P2 trata da ordem das atualizações no dia. Registrado assim.
- **D35 (nova, antes de 02/12):** o `b1_ratings` congelado inclui jogos da rodada em
  andamento se recebê-los; a D33 será cumprida filtrando a entrada. Confirmar.

Nenhum código foi alterado. **Parado aqui, aguardando o relatório de sexta.**

