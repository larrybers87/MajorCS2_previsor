# Relatório da sessão 02 — seeds, B0 e Stage 2 (26/11/2026)

## Resumo
- Seeds, modelo B0 calibrado e scripts do V3 e do Stage 2 prontos; **93 testes passam,
  1 pulado** (V2, sem dados).
- Há uma **previsão antecipada do Stage 2** commitada (sem nenhum resultado do Stage 1).
- **Bloqueios:** falta `data/manual/stage1_results.csv`; push suspenso por e-mail pessoal
  nos commits.

## 1. Bloqueios e o que fazer em 27/11

| Bloqueio | Efeito | Quem resolve |
|---|---|---|
| CSV do Stage 1 | sem V2, V3 real e previsão com os classificados reais | Larry |
| E-mail pessoal nos autores (D18) | sem push; carimbo local não é prova | Larry |
| Horário da 1ª partida do Stage 2 (D17) | define o prazo; pode ser a noite de 27/11 no Brasil (hipótese) | Larry |

### Passo a passo depois da rodada 5
1. Preencher `data/manual/stage1_results.csv` (modelo em
   `data/manual/stage1_results.template.csv`). Colunas
   `round,team_a,team_b,score_a,score_b,best_of`; vírgula ou ponto e vírgula; placar em
   rounds no Bo1 e em mapas no Bo3.
2. Rodar:
```
conda activate majorcs2
pytest tests/test_v2_real.py
python -m sim.v3_stage1
predict_stage2 --stage1 data/manual/stage1_results.csv
git add predictions
git commit -m "Previsão do Stage 2 com o Stage 1 completo"
```
3. Quando sair a rodada 1 oficial do Stage 2, colocá-la em
   `data/manual/stage2_results.csv` com placares vazios e comparar com `opening_round.csv`
   (testa H3). Depois, a cada resultado:
   `predict_stage2 --stage1 ... --stage2 data/manual/stage2_results.csv`.

Se a rodada 5 não terminar a tempo: complete o CSV com o que houver e rode
`predict_stage2 --conditioned`. Informe cada rodada **inteira** (partidas pendentes com
placar vazio).

**Conferência dos seeds:** a rodada 1 do Stage 1 deveria ter sido NiP x M80, PVISION x
DENDELE, HEROIC x Imperial, FaZe x Wildcard, Liquid x GOSH, Eternal Fire x FlyQuest, 100
Thieves x Chinggis Warriors e 9z x Lynn Vision. Qualquer diferença aponta erro nos seeds
(ou em D15/H4).

## 2. Feito e testado

### A. Housekeeping
Os três subagentes já tinham `tools: Read, Grep, Glob`; agora aparecem registrados e o
`leakage-reviewer` foi usado. Design atualizado, `decisoes.md` criado. Removidos o código,
os pacotes e o venv do spike e o script de guarda. `data/raw/spike/` (resposta salva)
**não** foi apagado.

### B. Seeds ([fonte_vrs.md](fonte_vrs.md))
- VRS clonado em `../_external/`, commit `f8c55f2`. Só um candidato para 02/11
  (`invitation` e `live` idênticos).
- `data/processed/seeds_singapore.csv` com os 32 times.
- **D15:** GOSH não existe no VRS e o "the ONE" é #318. Adotada a hipótese THE ONE = 1win
  e GOSH = BC.Game, a única encontrada em que a ordem de convites fica consistente.

### C. Histórico
O VRS tem partidas com data, vitória/derrota e elenco; por isso a Liquipedia **não** foi
consultada (e seus termos não foram abertos).

| Item | Valor |
|---|---:|
| Partidas 2025-06-01 a 2026-11-01 | 16.225 |
| Com rating dos dois lados | 13.127 |
| Visões repetidas entre snapshots unificadas | 60.259 |
| Linhas de mesmo par no mesmo dia (presentes já num único snapshot) | 300 |

Lacunas: sem formato, placar, evento, tier; LAN parcial; nada de 02/11 em diante. Nomes
normalizados só por caixa e espaços; identidade pelo elenco (3 jogadores em comum). O
filtro "tier 1-2" não é possível; usou-se "ambos no top 100".

### D. B0 ([b0_calibracao.md](b0_calibracao.md))
- `p_mapa = logística(beta * (r_A - r_B) / 100)`, **beta = 0,1558** (IC 95% 0,139-0,175),
  5.196 partidas.
- **Pontos x log:** pontos vence por pouco em verossimilhança (-3443,8 contra -3446,0) e
  no walk-forward (0,6643 contra 0,6650). São praticamente equivalentes.

Walk-forward mensal, 4.356 partidas (09/2025 a 11/2026), IC por dias:

| Previsor | log loss | Brier |
|---|---:|---:|
| **B0** | **0,6643** [0,6575; 0,6714] | **0,2359** [0,2328; 0,2392] |
| Maior VRS vence, com taxa histórica | 0,6767 | 0,2418 |
| 50% fixo | 0,6931 | 0,2500 |
| Maior VRS vence (0 ou 100%) | infinito | 0,4071 |

Diferença pareada B0 - taxa fixa: -0,0124 [-0,0167; -0,0082]. B0 - 50%: -0,0289
[-0,0354; -0,0223]. O ganho é real e **pequeno**. Acerto do favorito: 59,2%.

Ressalvas: **H10** (tudo tratado como Bo3; se tudo fosse Bo1, beta = 0,236); acima de 80%
o B0 pareceu confiante demais (amostra de 50 partidas, D21); escolha do modelo feita nos
meses avaliados (D23).

**Revisão de vazamento:** nenhum vazamento ativo. Corrigidos: corte movido para antes de
23/11 (o VRS usa o fuso do Pacífico); snapshots a partir do corte não são lidos; commit
do VRS fixado; teste de orientação que passaria mesmo com vazamento; parâmetros e hashes
copiados para cada previsão; métricas de cartel do V3 só com stage completo. A
recalibração deu o mesmo resultado. Em aberto: D22 e D23.

### E e F
- `python -m sim.v3_stage1`: log loss por partida, previsto x observado, rodada 1 e V2.
- `predict_stage2`: completo, ao vivo e **condicionado** (bônus feito).
- Testados com dados sintéticos; o condicionado também rodou com os seeds reais.

## 3. Previsão antecipada do Stage 2

`predictions/stage2/20261126T203028Z/`, commit `c49c1b6`, 26/11 17:31 (BRT). 200 mil
simulações, **zero resultados do Stage 1** (embora ele já esteja em andamento).

| Convidado | P(avançar) | se H10=Bo1 |
|---|---:|---:|
| FUT | 67,9% | 75,2% |
| Nemiga | 61,5% | 66,3% |
| G2 | 58,5% | 61,7% |
| THE ONE | 56,7% | 59,2% |
| Natus Vincere | 55,8% | 57,8% |
| Astralis | 54,2% | 55,3% |
| The MongolZ | 52,4% | 52,8% |
| MIBR | 51,3% | 51,2% |

Vindos do Stage 1, os mais prováveis de avançar no Stage 2 (já contando a chance de
chegar lá): NiP 31,6%, PVISION 31,1%, HEROIC 30,1%, FaZe 29,0%, Liquid 27,8%.

Limite principal: o B0 só vê os pontos VRS de 02/11. Entre execuções os **fatos** são
atualizados, os ratings não (D19).

SHA-256 (para registrar publicamente sem push):
```
8403a87e0039b58116ae5b68ab131be77c5f0297388e5c1200ad05ceb2e8cfb2  probabilities.csv
49e97592d40c623f6a9085f59e22cf32b066d8049c0f15cb4696753990beca4c  opening_round.csv
```

## 4. Push (não feito)

`git log --format='%an <%ae>'`: **todos os commits** têm o mesmo autor, com e-mail pessoal
real (o endereço não é repetido aqui). Opções:

1. **Autorizar o push como está** (o e-mail fica público).
2. **Trocar o autor pelo e-mail `noreply` do GitHub** antes do primeiro push. Reescreve o
   histórico local (nada foi publicado, então não há force push), muda os hashes, inclusive
   os citados nas previsões, e exige sua autorização.
3. Sem push por ora: publicar os SHA-256 acima em um lugar que não permita editar.

## 5. Não feito
CSV do Stage 1, V2, V3 real, previsão com classificados reais, Liquipedia, GRID,
playoffs, B1.

## 6. Perguntas
1. Qual das opções de push? (D18)
2. THE ONE é o elenco da 1win e GOSH o da BC.Game? (D15)
3. Horário da primeira partida do Stage 2? (D17)
4. B1 (Elo/Glicko) é o próximo passo, para os ratings mudarem durante o Major? (D19)
5. Para H10, aceita fornecer o `LIQUIPEDIA_CONTACT` ou esperamos o GRID?

Dúvidas completas em [duvidas_abertas.md](duvidas_abertas.md).

**Parado aqui, aguardando.**
