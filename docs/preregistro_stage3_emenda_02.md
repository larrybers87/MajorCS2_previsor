# EMENDA 2 ao pré-registro do Stage 3 (D33 e parâmetros fixos)

Escrita em 26/11/2026, 22:00 BRT, antes de 02/12. O [original](preregistro_stage3.md) e a
[emenda 1](preregistro_stage3_emenda_01.md) **não foram reescritos**. Onde houver
diferença, vale esta emenda.

## E2.1 Corte de informação do B1 (D33, decidido)
- O corte é o **início do primeiro jogo da rodada**.
- Usa-se **tudo que terminou antes**, inclusive rodadas anteriores do mesmo dia.
- Jogos **da mesma rodada não entram**.
- Vale para o **uso ao vivo** e para a **checagem de desastre** dos Stages 1 e 2.

Isso é um pouco **mais fino** que a fronteira de **dia** do backtest do B1, em que nenhuma
partida via outra do mesmo dia (regra "Sem informação do mesmo dia" do
[protocolo da sessão 03](protocolo_sessao_03.md); a resposta a citou como P2, que no
relatório 03 é o desvio sobre a ordem das atualizações dentro do dia). Efeito esperado
**pequeno (estimativa, não medido)**.

No formato suíço uma rodada só é emparelhada depois que a anterior termina; portanto "tudo
que terminou antes" equivale a todas as rodadas anteriores.

### Aplicação ao código congelado
`src/sim/b1_ratings.py` aplica **qualquer** partida decidida que receber, inclusive da
rodada em andamento (conferido em 26/11: com um jogo da rodada 4 incluído, os ratings dos
dois times mudaram). Para cumprir a regra, **quem o chama deve passar só as rodadas
anteriores à que será prevista**. O código congelado **não é alterado**; o CSV completo
com uma rodada pela metade não deve ser usado para prever essa rodada.

*Proposto:* resultados já conhecidos da rodada em andamento entram na simulação como
fatos, mas não nos ratings.

## E2.2 Parâmetros fixados antes de ver dados
| Cálculo | Réplicas | Semente |
|---|---:|---:|
| Bootstrap por partidas da condição (a) da checagem de desastre (quantil de 5%) | 10.000 | 20261202 |

Mínimo para qualquer bootstrap: 10.000 réplicas.

*Proposto:* gerador `numpy.random.default_rng(semente)`; antes de reamostrar, partidas
ordenadas por stage, rodada e seed inicial do melhor time.
