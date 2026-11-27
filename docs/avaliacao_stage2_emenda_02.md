# EMENDA 2 à avaliação do Stage 2 (D34 e parâmetros fixos)

Escrita em 26/11/2026, 22:00 BRT, antes do primeiro jogo do Stage 2. O
[original](avaliacao_stage2.md) e a [emenda 1](avaliacao_stage2_emenda_01.md) **não foram
reescritos**. Onde houver diferença, vale esta emenda.

## E2.1 Log score do cartel (decidido; substitui "média" no item 3 do original)
- **Soma**, nos 16 times, dos log scores **marginais**: `soma de -ln P(cartel observado)`.
- Os 16 times são **dependentes** (o formato fixa quantos terminam em cada cartel). A soma
  das marginais **não é** o log score da distribuição conjunta.
- **Referências:** cartéis gerados pelo **mesmo simulador**, com probabilidade fixa por
  série: **0,5** e **0,595137** para o time com mais pontos VRS (não há empate de pontos
  entre os times do Major, conferido). Mesmos seeds do Stage 2 da previsão oficial.
- **Relatar:** a diferença pontual (modelo - referência) e o **percentil do score
  observado** na distribuição simulada pelo modelo.
- Esse percentil é um **teste de consistência**: **não mede a qualidade do modelo**.
- Se a oficial for condicionada: `P(cartel) / P(participar)` para os times que
  participaram, e as referências passam pela mesma simulação encadeada.

## E2.2 Parâmetros fixados antes de ver dados
| Cálculo | Réplicas | Semente |
|---|---:|---:|
| Bootstrap pareado por partidas (log loss e Brier), IC 95% pelos quantis 2,5% e 97,5% | 10.000 | 20261128 |
| Torneios simulados do teste de consistência (por extremo de w) | 200.000 | 20261127 (a do `meta.json`) |
| Cartéis das referências | 200.000 por referência | 20261127 |

Mínimo para qualquer bootstrap: 10.000 réplicas.

### Detalhes PROPOSTOS para reprodutibilidade
- Gerador `numpy.random.default_rng(semente)`; antes de reamostrar, partidas ordenadas por
  rodada e, dentro dela, pelo seed inicial do melhor time.
- Percentil: fração dos torneios simulados com score menor ou igual ao observado (score
  menor é melhor).
- Se um cartel observado tiver probabilidade zero nas simulações, usar
  `1 / (2 x número de simulações)` e declarar.
