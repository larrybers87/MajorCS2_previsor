# Relatório da sessão 03 — push, V2, H10, B1 (26/11/2026)

## Resumo
- Repositório **publicado**; previsão do Stage 2 condicionada a 30 partidas **enviada** em
  27/11 00:14 UTC (26/11 21:14 BRT).
- **V2 sem divergências:** os 33 confrontos do Stage 1 coincidem com a engine.
- **H10 não identificável:** a previsão usa a faixa w=0 / w=1.
- **B1 não adotado:** melhor que o B0 no teste, mas dentro do ruído. Segue o B0.
- **Liquipedia não usada** (termos). **FUT e Astralis jogam com substitutos.**
- 114 testes passam.

## 1. O que fazer na sexta, depois da rodada 5

Preencher os placares das três linhas da rodada 5 em `data/manual/stage1_results.csv`
(em mapas: 2-0 ou 2-1) e rodar:

```
conda activate majorcs2
pytest tests/test_v2_real.py
predict_stage2 --stage1 data/manual/stage1_results.csv
python -m sim.v3_stage1
git add predictions
git commit -m "Previsão do Stage 2 com o Stage 1 completo"
git log --format='%an <%ae>' | sort | uniq -c
git push origin main
```

- Ensaiado com os 8 desfechos possíveis; a previsão completa leva cerca de 6 s.
- Quando sair a rodada 1 oficial do Stage 2, comparar com `opening_round.csv` (testa H3).
  Para fixá-la como fato: `data/manual/stage2_results.csv` com placares vazios e
  `predict_stage2 --stage1 ... --stage2 data/manual/stage2_results.csv`.
- Se a rodada 5 não terminar a tempo, a previsão condicionada já publicada serve.
- Horário do primeiro jogo: **não confirmado** (D17).

## 2. A. Push

| Item | Resultado |
|---|---|
| Licença | `counter-strike_rules_and_regs` e o repositório do VRS: sem licença |
| Cópias da Valve | removidas de todo o histórico local antes do primeiro push (autorizado); seguem no disco, ignoradas; ver [fontes_valve.md](fontes_valve.md) |
| Dados brutos do VRS versionados | nenhum |
| Reescrita | `git filter-branch` (sem `filter-repo`); autor, e-mail, datas e mensagens iguais; mapa de hashes em [decisoes.md](decisoes.md) |
| Previsão antecipada | mesmos blobs; o GitHub serve LF, cujo SHA-256 difere do informado antes (ambos em `decisoes.md`) |
| Push | só `main`; remoto estava vazio; backup apagado depois |

Horários registrados pelo GitHub (API de atividade, independem da data do commit):

| UTC | De → para | Conteúdo |
|---|---|---|
| 26/11 23:58:26 | criação → `c4d31e6` | histórico, incluindo a previsão antecipada (`3ed704f`) |
| 26/11 23:59:39 | → `0974161` | protocolo pré-registrado de H10 e B1 |
| 27/11 00:14:53 | → `43fdad6` | código de C e E e a previsão condicionada |

## 3. B. V2

- Rodada 1 real = 1v9 ... 8v16 com os nossos seeds (8 de 8).
- Rodadas 2 a 4 sem divergência; formatos do CSV compatíveis com a regra.
- Rodada 5: a engine gera exatamente HEROIC x Lynn Vision, Imperial x Wildcard e M80 x
  100 Thieves (grupo 2-2: Imperial, M80, Lynn Vision, 100 Thieves, Wildcard, HEROIC;
  linhas 1 a 3 da tabela dão rematch, vale a 4).

**Alcance do teste:** descarta ordenar sem Buchholz ou com ele invertido, e qualquer
troca de seeds vizinhos. **Não** testa H1 (o beco da rodada 3 não ocorreu), não distingue
a tabela das rodadas 4-5 do "melhor x pior" (mesmos confrontos), nem testa H3 e H8.

## 4. C. H10 ([h10_verossimilhanca.md](h10_verossimilhanca.md))

- Estimativa: **w = 0,68**, beta 0,2046. IC 95%: perfil **[0,00; 1,00]**; bootstrap por
  dias [0,00; 0,75]. Largura 1,00 > 0,3: **publicar a faixa**.
- B0 escolhido só no desenvolvimento: top100/pontos (o mesmo de antes).
- Teste (1.479 partidas, jun-01/11): log loss 0,6601 (w=0), 0,6600 (w=1), 0,6599 (w
  estimado). O formato quase não muda o ajuste, mas muda as probabilidades de Bo1.
- **D21:** acima de 80%, previsto 84,7%, observado **59,1%** (n=22; IC [38,7%; 76,7%]).

## 5. E. B1 ([b1_avaliacao.md](b1_avaliacao.md))

- 172 configurações; escolhida: Elo com prior VRS (s=0,5), K=20, sem decaimento, K em
  dobro nas 10 primeiras partidas.

| Período | B0 | B1 |
|---|---:|---:|
| Desenvolvimento (log loss) | 0,6664 | 0,6563 |
| Teste (log loss) | 0,6601 | 0,6571 |
| Teste (Brier) | 0,2337 | 0,2320 |

- **B1 − B0 no teste: −0,0029, IC 95% [−0,0115; +0,0057].** Não atende a regra:
  **o B0 segue no Stage 2; o B1 fica para o Stage 3.**

## 6. Revisão de vazamento (C e E)

Sem resultado do dia ou posterior em previsão, sem uso do teste na seleção e sem caminho
do Stage 1 para ajuste. Os vieses achados **favorecem o B1**, o que não muda a decisão:
o principal é que ele usa partidas até a véspera, que na fonte só aparecem em snapshot
posterior. Também há possível seleção do histórico por snapshots posteriores (não medida).
Nada no modelo foi alterado depois de visto o teste; só foram acrescentados testes.

### Desvios do protocolo pré-registrado
| # | Desvio |
|---|---|
| P1 | O RD do Glicko tem teto no valor inicial |
| P2 | No Glicko, partidas do mesmo dia atualizam em sequência (ordem alfabética); no Elo, a fronteira das 10 partidas depende da ordem. As previsões do dia não são afetadas, os ratings finais podem ser |
| P3 | Desempates de identidade não previstos (mesmo nome, depois o time mais novo) |
| P4 | Time visto primeiro sem elenco e depois com elenco vira dois times |
| P5 | O decaimento do Elo é em direção ao prior do dia (o texto era ambíguo) |
| P6 | `w` em grade de 0,01; bootstrap com 400 réplicas em grade de 0,05 |
| P7 | `w=1` e "w estimado" também foram avaliados no teste: análise exploratória, não usada |
| P8 | O modelo principal do Stage 2 (média de w=0 e w=1) não foi avaliado no teste, nem a calibração D21 dele. Pela convexidade, seu log loss não passa da média dos dois |
| P9 | O teste termina em 01/11, não em 22/11 (não há dados) |

Limite: o protocolo foi enviado antes de eu abrir o CSV, mas já conhecia os confrontos
da rodada 5; o código foi commitado só depois de rodar.

## 7. D e F
- **D não executada.** Os termos dizem: "Use of the API for non-editing purposes is not
  supported" e indicam a LiquipediaDB, com aprovação. Nenhuma requisição à API
  ([h10_formato.md](h10_formato.md)).
- **F:** começam com substituto FUT (SunPayus por cmtry), Astralis (Anlelele por jabbi),
  Vitality (apEX por jL), Legacy (ksloks por n1ssim) e 9z (history por meyern, já
  eliminada). Fontes secundárias; a página oficial da PGL não carregou
  ([substitutos.md](substitutos.md)). Modelo inalterado.

## 8. Previsão publicada (`predictions/stage2/20261127T001433Z/`)

30 partidas do Stage 1 como fatos, rodada 5 simulada, B0, 200 mil simulações por extremo.

Rodada 5 (Bo3): HEROIC 69,5% contra Lynn Vision; 100 Thieves 51,6% contra M80; Imperial
51,1% contra Wildcard.

| Time | P(participar) | P(avançar no Stage 2) | faixa w=0 a w=1 |
|---|---:|---:|---|
| FUT * | 100% | 72,9% | 69,0 a 76,8 |
| Nemiga | 100% | 63,1% | 60,7 a 65,5 |
| G2 | 100% | 59,4% | 57,7 a 61,2 |
| THE ONE | 100% | 57,3% | 56,0 a 58,5 |
| Natus Vincere | 100% | 55,6% | 54,5 a 56,7 |
| Astralis * | 100% | 54,9% | 54,2 a 55,7 |
| The MongolZ | 100% | 52,5% | 52,1 a 52,9 |
| NiP | 100% | 51,5% | 51,3 a 51,7 |
| MIBR | 100% | 50,8% | 50,8 |
| PVISION | 100% | 50,6% | 50,5 a 50,7 |
| Liquid | 100% | 47,0% | 46,2 a 47,7 |
| Eternal Fire | 100% | 45,3% | 44,2 a 46,4 |
| HEROIC | 69,6% | 33,4% | 31,9 a 34,9 |
| FlyQuest | 100% | 23,8% | 19,3 a 28,3 |
| 100 Thieves | 51,6% | 23,1% | 22,6 a 23,5 |
| M80 | 48,4% | 20,3% | 19,4 a 21,2 |
| Imperial | 51,2% | 16,8% | 15,2 a 18,4 |
| Wildcard | 48,8% | 15,3% | 13,5 a 17,0 |
| Lynn Vision | 30,4% | 6,5% | 4,3 a 8,6 |

\* começa com substituto. A faixa cobre só a incerteza de formato, **não** a do modelo.

**V3 retrospectivo** (30 partidas): log loss 0,6734 contra 0,6931 do 50%, erro padrão
0,023. Não distingue modelos.

## 9. Não feito e bloqueios
Previsão com o Stage 1 completo (rodada 5 não jogada); amostra da Liquipedia; confirmação
oficial dos substitutos e do horário; playoffs; GRID.

## 10. Perguntas
1. Horário do primeiro jogo do Stage 2? (D17)
2. Vale a última previsão enviada antes do primeiro jogo, com log loss por partida e log
   score do cartel? (D28)
3. Mantemos o B0 sem ajuste para os substitutos? (D25)
4. "Ponto médio" = média das probabilidades de w=0 e w=1? (D27)
5. Pedir acesso à LiquipediaDB ou esperar o GRID? (D24)
6. Qual o critério de adoção do B1 no Stage 3, já que o teste atual foi visto? (D26)

Dúvidas completas em [duvidas_abertas.md](duvidas_abertas.md). **Parado aqui, aguardando.**
