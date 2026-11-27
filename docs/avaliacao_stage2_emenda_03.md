# EMENDA 3 à avaliação do Stage 2 (regra de leitura)

Escrita em 27/11/2026, antes do primeiro jogo do Stage 2 (28/11, 04:00 UTC). O
[original](avaliacao_stage2.md) e as emendas [1](avaliacao_stage2_emenda_01.md) e
[2](avaliacao_stage2_emenda_02.md) **não foram reescritos**. Esta emenda acrescenta a
regra que transforma a diferença de log loss em um rótulo; os textos anteriores não
definiam uma.

## Já conhecido ao escrever
- A previsão oficial (`predictions/stage2/20261127T161221Z`), publicada antes.
- Os resultados do Stage 1 e a avaliação diagnóstica dele.
- **Nenhum resultado do Stage 2.**

## E3.1 Regra (decidida pelo Larry)

Para cada referência (**50%** e **maior VRS fixo**), em cada partida decidida `i`:
`d_i = log loss do modelo − log loss da referência`.

- `d` = média dos `d_i`; `n` = número de partidas.
- `EP` = desvio padrão amostral dos `d_i` (divisor `n − 1`) dividido pela raiz de `n`.

| Condição | Rótulo |
|---|---|
| `d < −2 × EP` | **melhor que a referência** |
| `d > +2 × EP` | **pior que a referência** |
| `abs(d) ≤ 2 × EP` | **inconclusivo** |

A definição do `EP` como erro padrão da diferença **pareada** por partida é a definição
operacional desta emenda.

## E3.2 Alcance
- Só o **log loss por partida** recebe rótulo. Brier, log score dos cartéis e o percentil
  do teste de consistência são relatados sem rótulo.
- O bootstrap pareado da [emenda 1](avaliacao_stage2_emenda_01.md) (com os parâmetros da
  emenda 2) continua a ser calculado e relatado. Se o intervalo sugerir outra leitura, o
  rótulo segue esta regra e a divergência é mencionada.
- Probabilidades e partidas: como nos itens anteriores.

## E3.3 Limites
O `EP` trata as partidas como independentes, o que não são. É um único torneio: o rótulo
vale só para este stage e não ordena modelos.
