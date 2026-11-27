# Anexo de sensibilidade D25: substitutos de FUT e Astralis

Pré-registrado em 26/11/2026, antes do primeiro jogo do Stage 2 (04:00 UTC de 28/11).

## Pergunta
Quanto a previsão do Stage 2 mudaria se FUT e Astralis, que começam o Major com um
substituto ([substitutos.md](substitutos.md)), valessem menos pontos VRS?

## Cenários

| Cenário | Pontos VRS de FUT | Pontos VRS de Astralis |
|---|---|---|
| 0 (igual à manchete) | 1721 | 1572 |
| -50 | 1671 | 1522 |
| -100 | 1621 | 1472 |

**Os valores -50 e -100 são arbitrários.** Não foram estimados de dado algum e não medem
o efeito real de um substituto. O anexo mostra só a sensibilidade do resultado.

## Regras
- A **manchete** continua sendo o B0 sem ajuste. O anexo não é a previsão oficial e não
  entra na avaliação (D28).
- A redução entra **só nas probabilidades de partida**. Os seeds não mudam (vêm do VRS
  oficial).
- As duas equipes recebem a mesma redução em cada cenário. Combinações cruzadas (só uma
  delas, ou reduções diferentes) **não** são calculadas.
- Mesmo modelo, mesmas simulações e mesma semente da previsão oficial; média de w=0 e w=1.
  Por isso o cenário 0 deve reproduzir a manchete exatamente, e o script confere isso com
  `--official`.
- Vitality e Legacy ficam para o Stage 3.

## Código e saída
`python -m sim.anexo_d25` (`src/sim/anexo_d25.py`). Grava em
`predictions/anexo_d25/<carimbo UTC>/`: `scenarios.csv` (cartéis e P(avançar) dos times em
cada cenário), `matches.csv` (probabilidade de FUT e Astralis nos confrontos de abertura),
`summary.md`, `meta.json` e `model_params.json`.
