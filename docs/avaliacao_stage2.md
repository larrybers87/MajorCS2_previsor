# Avaliação da previsão oficial do Stage 2

Escrito em 26/11/2026, antes do primeiro jogo do Stage 2.

## Regra decidida (D28, texto do Larry)

- **Previsão oficial:** a última enviada (push com horário da API do GitHub) antes do
  primeiro jogo do Stage 2, **04:00 UTC de 28/11** (D17).
- **Métricas primárias:** log loss por partida (Brier secundária) e log score da
  distribuição do cartel final, com IC por bootstrap de simulações (os 16 times são
  dependentes).
- **Referências:** 50% e maior VRS fixo.
- Atualizações ao vivo ficam em tabela separada.

## Definições operacionais PROPOSTAS (aguardam confirmação; D29)

Sem confirmação antes do prazo, valem estas, por estarem publicadas antes dos jogos.

1. **Qual pasta é a oficial:** a pasta mais recente de `predictions/stage2/` contida no
   último push anterior ao prazo. Pastas de `predictions/anexo_d25/` e
   `predictions/v3_stage1/` não contam. Conferir com
   `gh api repos/larrybers87/MajorCS2_previsor/activity`.
2. **Probabilidade por partida:** para cada uma das partidas do Stage 2, no formato em que
   foi jogada, a média das probabilidades de w=0 e w=1, calculada com
   `model_params.json` e a coluna `vrs_pontos` da pasta oficial. O B0 não muda durante o
   stage, então vale para qualquer confronto que ocorra.
3. **Log score do cartel:** média, nos 16 times, de `-ln P(cartel observado)`, com
   `probabilities.csv`. Se a oficial for uma previsão condicionada (rodada 5 pendente),
   usa-se `P(cartel) / P(participar)` para os times que participaram.
4. **"Maior VRS fixo":** o time com mais pontos VRS (02/11) vence qualquer série com
   probabilidade **0,595137**, a taxa observada em 5.182 partidas entre times do top 100
   de 01/06/2025 a 01/11/2026. Para o cartel, simula-se o stage com essa probabilidade.
5. **50%:** toda série com probabilidade 0,5; cartéis com 1/8, 3/16, 3/16, 3/16, 3/16, 1/8.
6. **IC por bootstrap de simulações:** gerar torneios completos do Stage 2 pelo próprio
   modelo oficial (mesma semente e parâmetros do `meta.json`, metade em cada extremo de w),
   calcular as métricas em cada torneio simulado e reportar os quantis 2,5% e 97,5% da
   métrica e da diferença para cada referência, junto com o percentil do valor observado.
   **Interpretação:** é o intervalo esperado *se o modelo estivesse certo*, não um IC da
   qualidade verdadeira. Um torneio é uma única observação dependente.

O código desta avaliação **ainda não foi escrito**. As entradas necessárias ficam
publicadas na pasta oficial.
