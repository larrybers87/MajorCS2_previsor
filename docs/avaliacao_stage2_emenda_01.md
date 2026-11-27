# EMENDA 1 à avaliação do Stage 2 (D29)

Escrita em 26/11/2026, 21:45 BRT, antes do primeiro jogo do Stage 2. O original,
[avaliacao_stage2.md](avaliacao_stage2.md), **não foi reescrito**. Onde houver diferença,
vale esta emenda.

## E1.1 Aprovado
"Itens 1 a 3 aprovados". Li como os três pontos levados para aprovação: (a) "maior VRS
fixo" com a taxa histórica; (b) o intervalo por simulações; (c) a pontuação da oficial
condicionada. Os itens 1 a 3 do original (qual pasta vale, probabilidade por partida e log
score do cartel) são consistentes com isso e seguem como escritos.

## E1.2 "Maior VRS fixo": conferido que usa só dados anteriores ao evento
- **3.084 / 5.182 = 0,595137** (14 partidas com pontos iguais excluídas).
- Partidas entre times do top 100, de **2025-06-01 a 2026-11-01**; corte exclusivo
  2026-11-23. A primeira partida do Major foi em 24/11 01:00 BRT (23/11 no fuso do
  Pacífico, usado pelo VRS), logo fora.
- Rating de cada partida vindo de snapshot anterior a ela (o mais novo usado: 2026-10-05).
- Cálculo: sobre `backtest.b0_calibration.rated_matches(matches.parquet)` filtrado por
  `in_population(..., "top100")`, fração em que o time com mais pontos venceu.

## E1.3 Comparação modelo x referência (substitui o uso do item 6 do original)
- **Comparação:** bootstrap **pareado por partidas** da diferença (modelo - referência) em
  log loss e Brier.
- O intervalo por simulações do item 6 passa a se chamar **teste de consistência** (o
  observado é compatível com o que o modelo esperaria se estivesse certo?). Não compara
  modelos.

### Detalhes operacionais PROPOSTOS
- Reamostrar as partidas do Stage 2 com reposição, 10.000 réplicas, semente 20261128;
  intervalo de 95% pelos quantis 2,5% e 97,5%.
- O bootstrap por partidas trata as partidas como independentes, o que não são.

### Ponto a confirmar (D34)
O **log score do cartel** é por time, não por partida: o bootstrap por partidas não se
aplica a ele. Proposta: reportar a diferença pontual para cada referência e o teste de
consistência, sem intervalo de comparação.
