# Detalhes de execução da emenda 6

Escrito em 27/11/2026, **antes de rodar qualquer candidato**. Fixa pontos que a
[emenda 6](preregistro_stage3_emenda_06.md) não detalha; escolhas do assistente, sem criar
nem mudar regra. Em caso de conflito, vale a emenda.

## Comum
- Previsões fora da amostra mensais de set/2025 a mai/2026 (desenvolvimento) e de jun a
  nov/2026 (teste). Avaliação: partidas do alvo de dez/2025 a mai/2026; métricas pela média
  sobre partidas (meses ponderados pelo número delas).
- B0: beta ajustado nas partidas anteriores ao mês entre times do top 100 com rating; B1 e
  candidatos baseados em rating: nas partidas anteriores do alvo. Busca do beta como em
  `models.b0.fit_beta`.

## Candidatos
- **C2, Glicko-2:** todas as partidas de um dia formam o período do time, com os valores
  dele e dos adversários anteriores ao dia; volatilidade pelo método de Illinois do artigo
  de Glickman (tolerância 1e-6). Antes de um dia, depois de `k` dias sem jogar desde a
  última atualização, o desvio é `raiz(f² + (k − 1) σ²)`, limitado ao inicial; a
  probabilidade usa esse desvio. Rating não volta ao prior.
- **C3:** o favorito é o time com `p ≥ 0,5` (empate: `team_a`). Platt: `a` por máxima
  verossimilhança, mesma busca do beta. Isotônica: algoritmo PAV sobre
  (`max(p, 1 − p)`, favorito venceu), valores iguais de entrada agrupados; entre os pontos
  ajustados, interpolação linear; fora deles, o valor da ponta; resultado limitado a
  [0,5; 0,999]. Mês sem previsão anterior da referência não tem calibrador (set/2025).
- **C4:** máxima verossimilhança por Newton; se um coeficiente sair negativo, fixa-se em
  zero e reajusta-se o outro; probabilidades limitadas a [1e-12, 1 − 1e-12] antes do logit.
- **C5:** identidade do time como no B1; `exp` conta as partidas dessa identidade em dias
  anteriores, contra qualquer adversário, desde 01/06/2025; a escalação é o conjunto exato
  de nomes (sem diferenciar maiúsculas) e a idade conta do primeiro dia anterior em que
  apareceu (nunca: zero); se um dos dois elencos for desconhecido, as duas diferenças são
  zero. Coeficientes ajustados em conjunto por máxima verossimilhança (Newton com busca em
  linha), nas formas w=0 e w=1.
- **Escolha de hiperparâmetros:** menor log loss somado nos meses do desenvolvimento
  anteriores com previsão; empate: ordem da grade. "Desenvolvimento inteiro" = todos os
  meses do desenvolvimento com previsão.

## Erro padrão
- Blocos: semana ISO (ano, semana) da data da partida. Cada réplica sorteia, com
  reposição, tantas semanas quantas há nas partidas avaliadas e calcula a soma de `d_i`
  dividida pelo número de partidas sorteadas. Gerador `numpy.random.default_rng(20261203)`,
  os mesmos sorteios para todos os modelos. O bootstrap de dias, informativo, segue igual.
