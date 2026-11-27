# ESQUELETO — Avaliação da previsão oficial do Stage 2

> **A preencher depois do fim do Stage 2.** Os campos `⟨…⟩` estão vazios de propósito.
> Copiar para `docs/resultado_stage2.md` antes de preencher. As regras abaixo vêm de
> [avaliacao_stage2.md](avaliacao_stage2.md), [emenda 1](avaliacao_stage2_emenda_01.md) e
> [emenda 2](avaliacao_stage2_emenda_02.md); em caso de diferença, valem elas. O código
> desta avaliação **ainda não foi escrito**.

Preenchido em: ⟨data e hora⟩ · commit do código: ⟨hash⟩

## 0. Conferências antes de calcular

| Item | Valor |
|---|---|
| Previsão avaliada | `predictions/stage2/20261127T161221Z`, commit `7f8835f`, tag `stage2-oficial` |
| Push | 2026-11-27T16:13:36Z (prazo 2026-11-28T04:00:00Z) |
| É a pasta mais recente do último push anterior ao prazo (D28)? | ⟨sim/não; conferido na API do GitHub⟩ |
| `pytest tests/test_stage2_official.py` | ⟨resultado⟩ |
| CSV dos resultados (SHA-256) | ⟨hash⟩ |
| Partidas decididas | ⟨n⟩ de 33 |
| V2 do Stage 2 (confrontos reais x engine) | ⟨sem divergências / lista⟩ |
| Conferência secundária dos resultados | ⟨fonte e diferenças⟩ |
| W.O., desistências, substituições durante o stage | ⟨registrar o que houve e a fonte⟩ |

## 1. Por partida (métrica primária: log loss; Brier secundária)

Probabilidade: média de w=0 e w=1 com `model_params.json` e `vrs_pontos` da pasta oficial,
no formato em que a partida foi jogada.

| Modelo ou referência | log loss | Brier |
|---|---:|---:|
| B0 oficial | ⟨⟩ | ⟨⟩ |
| 50% | 0,6931 | 0,2500 |
| Maior VRS fixo (0,595137) | ⟨⟩ | ⟨⟩ |

Diferença pareada, modelo − referência (negativo favorece o modelo). Bootstrap por
partidas, 10.000 réplicas, semente 20261128, quantis 2,5% e 97,5%; partidas ordenadas por
rodada e, dentro dela, pelo seed inicial do melhor time.

| Contra | log loss | IC 95% | Brier | IC 95% |
|---|---:|---|---:|---|
| 50% | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨⟩ |
| Maior VRS fixo | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨⟩ |

## 2. Cartel final (métrica primária)

Soma, nos 16 times, de `-ln P(cartel observado)`. Referências pelo mesmo simulador e os
mesmos seeds (200.000 por referência, semente 20261127). Se um cartel observado tiver
probabilidade zero numa simulação, usar `1 / (2 x simulações)` e declarar.

| Modelo ou referência | log score (soma) | modelo − referência |
|---|---:|---:|
| B0 oficial | ⟨⟩ | |
| 50% | ⟨⟩ | ⟨⟩ |
| Maior VRS fixo | ⟨⟩ | ⟨⟩ |

| Seed | Time | Cartel observado | P(cartel) | −ln P | P(avançar) | Avançou |
|---:|---|---|---:|---:|---:|---|
| ⟨16 linhas⟩ | | | | | | |

## 3. Teste de consistência (não mede qualidade)

Torneios simulados pelo próprio modelo oficial: 200.000 por extremo de w, semente
20261127. Percentil = fração dos torneios com score menor ou igual ao observado.

| Métrica | Observado | quantil 2,5% | quantil 97,5% | percentil |
|---|---:|---:|---:|---:|
| log loss por partida | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨⟩ |
| Brier por partida | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨⟩ |
| log score dos cartéis | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨⟩ |

## 4. Partidas

| R | Partida | Bo | P(melhor seed) | Vencedor | log loss | Brier |
|---:|---|---|---:|---|---:|---:|
| ⟨33 linhas⟩ | | | | | | |

## 5. Leitura

Regra quantitativa definida pelo Larry em 27/11/2026, antes do primeiro jogo do Stage 2.
Decide só o rótulo; as métricas e o IC por bootstrap das emendas continuam a ser
relatados.

Para cada referência, em cada partida decidida `i`:
`d_i = log loss do modelo − log loss da referência`.

- `d` = média dos `d_i`; `n` = número de partidas.
- `EP` = desvio padrão amostral dos `d_i` (divisor `n − 1`) dividido pela raiz de `n`
  (definição operacional: erro padrão da diferença **pareada**).
- **"Melhor que a referência"**: somente se `d < −2 × EP`, ou seja, o log loss do modelo é
  menor que o da referência por **mais** de 2 erros padrão.
- **"Inconclusivo"**: qualquer outro caso, inclusive diferença igual a 2 EP e inclusive
  modelo **pior** por mais de 2 EP.

| Contra | n | d | EP | −2 × EP | Leitura |
|---|---:|---:|---:|---:|---|
| 50% | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨melhor que a referência / inconclusivo⟩ |
| Maior VRS fixo | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨⟩ | ⟨melhor que a referência / inconclusivo⟩ |

- Só o log loss recebe rótulo. Brier, log score dos cartéis e percentil são relatados sem
  rótulo; se o IC por bootstrap sugerir outra coisa, vale o rótulo desta regra e a
  divergência é mencionada.
- O percentil só diz se o observado é compatível com o modelo; percentil dentro de
  2,5% a 97,5% não mostra que o modelo é bom.
- O EP trata as partidas como independentes, o que não são. Um torneio: o rótulo vale só
  para este stage e não ordena modelos.

⟨observações⟩

## 6. Fora desta avaliação
- Atualizações por rodada (`predictions/stage2/round<N>/`): listar quais foram enviadas
  antes de cada rodada, em tabela separada: ⟨pasta, horário do push, primeiro jogo⟩.
- Anexo D25 (não oficial).
- Ocorrências e limitações: ⟨⟩
