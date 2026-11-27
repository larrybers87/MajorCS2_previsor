# Adendo ao pré-registro do Stage 3: o que já se sabia do Stage 1

**Data: 27/11/2026**, antes do primeiro jogo do Stage 2 e do Stage 3.

O [pré-registro](preregistro_stage3.md) e as emendas
[1](preregistro_stage3_emenda_01.md) e [2](preregistro_stage3_emenda_02.md) **não foram
editados**. Este adendo só registra conhecimento adquirido; **não muda regra alguma**.

## Registro

O desempenho do B1 e do B0 nas 33 partidas do Stage 1 **já era conhecido antes do Stage
3**. É **retrospectivo**: calculado depois dos jogos. Média das probabilidades de w=0 e
w=1; EP = erro padrão entre partidas.

| Modelo | log loss | EP | Brier | EP | Favorito venceu |
|---|---:|---:|---:|---:|---:|
| B0 | 0,6865 (0,686498) | 0,0300 | 0,2466 | 0,0145 | 21/33 |
| B1 | 0,6412 (0,641230) | 0,0191 | 0,2245 | 0,0094 | 23/33 |
| B1 − B0 | −0,0453 | 0,0245 | −0,0222 | 0,0118 | |

- Com três casas, o B0 é **0,686**. O valor 0,687 que circulou em 27/11 veio de um
  arredondamento duplo (0,686498 → 0,6865 → 0,687).
- Também conhecidos: as variantes w=0 e w=1 separadas, os resultados por formato e as
  métricas de cartel final dos dois modelos.
- Fonte: `predictions/v3_stage1/20261127T165555Z` (commit `d9e5a49`, sem código
  pendente), com arquivos de resultado idênticos aos da primeira execução,
  `20261127T163922Z` (27/11 16:39 UTC).

## O que segue valendo

**A combinação B0/B1 e a checagem de desastre do Stage 3 seguem a regra pré-registrada,
sem reponderar.**

- Combinação: peso **1/4** para cada par (B0, B1) x (w=0, w=1); betas do B0 0,155760 e
  0,236080; betas do B1 0,350419 e 0,532006; configuração e código do B1 congelados (em
  27/11, `ratings.py` e `b1_ratings.py` são iguais aos do commit `30a519a`).
- Checagem de desastre ([emenda 1](preregistro_stage3_emenda_01.md)): voltar ao B0 puro
  **somente se** (a) a média 50/50 for pior que o 50% com significância unilateral de 95%
  (bootstrap por partidas, 10.000 réplicas, semente 20261202) **e** (b) o B1 sozinho for
  pior que o B0. Partidas dos Stages 1 e 2 **juntas**; cálculo depois do fim do Stage 2 e
  antes do primeiro jogo do Stage 3; corte de informação do B1 pela
  [emenda 2](preregistro_stage3_emenda_02.md).
- Nem o teste já visto (06 a 11/2026) nem este resultado do Stage 1 servem de argumento
  para mudar pesos, betas, configuração ou limiares.

## Consequências para a leitura
- A seção 3 do original diz que o log loss do B1 e o da média **não** haviam sido
  calculados. Para o B1 isso deixou de valer em 27/11. **A média 50/50 em partidas deste
  Major continua não calculada.**
- A checagem de desastre inclui o Stage 1, cujo resultado retrospectivo favoreceu o B1.
  Isso pesa na condição (b), que junta os dois stages. Como o original já dizia, a
  checagem não é um teste prospectivo para o Stage 1.
