# Protocolo pré-registrado: H10 (formato) e B1

Escrito e enviado ao GitHub em 26/11/2026, **antes de abrir
`data/manual/stage1_results.csv` nesta sessão**. Já conhecidos ao escrever: os três
confrontos da rodada 5 do Stage 1, informados pelo Larry nas instruções, e as métricas
agregadas do walk-forward do B0 da sessão 02 (que incluem o período de teste abaixo).
Mudanças posteriores a este texto precisam ser declaradas no relatório.

## Comum
- Dados: `data/processed/matches.parquet` (VRS, commit fixado), de 2025-06-01 a antes de
  2026-11-23. **Nenhum dado do Stage 1 entra em ajuste ou seleção.**
- Alvo de avaliação: partidas com os dois times no top 100 do snapshot VRS anterior.
- **Desenvolvimento:** meses 2025-09 a 2026-05. **Teste:** 2026-06-01 a 2026-11-22.
- Walk-forward mensal: parâmetros ajustados só com partidas anteriores ao mês previsto.
- Hiperparâmetros escolhidos **só** pelo log loss no desenvolvimento; o teste é calculado
  depois, uma vez por modelo escolhido.
- IC 95% por bootstrap reamostrando dias; diferenças sempre pareadas.

## B0 (resolve D23)
- Grade: transformação {pontos, log} x população de treino {todas, top100}.
- A configuração escolhida no desenvolvimento é a usada no Stage 2, reajustada em todos os
  dados anteriores ao corte.

## H10: fração de Bo1
- `p = logística(beta * x)`; `P_série = w*p + (1-w)*p^2*(3-2p)`, `w` em [0, 1].
- `w` e `beta` por máxima verossimilhança conjunta, na população e transformação do B0.
- IC de `w`: perfil de verossimilhança (corte qui-quadrado, 1 grau de liberdade) e
  bootstrap por dias. **A regra usa o intervalo mais largo dos dois.**
- Regra (do Larry): largura <= 0,3: usar o `w` estimado. Senão: publicar a faixa com
  `w = 0` e `w = 1` (cada um com o beta ajustado para ele) e usar como número principal o
  **ponto médio das probabilidades dos dois extremos** (leitura nossa de "ponto médio").

## B1
Ratings atualizados partida a partida.

- **Identidade:** por elenco (3 jogadores em comum com o elenco mais recente), em ordem
  cronológica; elenco desconhecido: último time com o mesmo nome; senão, time novo.
- **Sem informação do mesmo dia:** todas as partidas de um dia são previstas com os
  ratings do fim do dia anterior; as atualizações entram depois (o VRS não dá o horário).
- **Prior:** `1500 + s*(pontos VRS - 1000)`, pontos do último snapshot anterior ao dia;
  sem pontos, 1500.
- **Elo:** esperado `1/(1+10^(-(Ra-Rb)/400))`; `R += K*(S - E)`; antes de cada dia, o
  desvio em relação ao prior decai com meia-vida `H`; nas 10 primeiras partidas, `K*m`.
  - `s` em {0; 0,25; 0,5; 0,75}, `K` em {10, 20, 30, 40, 60}, `H` em {60, 90, 180, sem},
    `m` em {1, 2}: 160 configurações.
- **Glicko-1** (uma partida por período, mesmo prior e mesma regra de dias):
  `RD` inicial em {200, 350}, crescimento por dia `c` em {10, 20, 40}, `s` em {0; 0,5}:
  12 configurações. O rating não decai para o prior depois de inicializado.
- **Calibração:** probabilidade final = `P_série(logística(beta1 * (Ra-Rb)/100))` com
  `beta1` ajustado no walk-forward mensal, nas partidas anteriores do alvo.
- Para comparar ratings e não formatos, B0 e B1 são avaliados com a mesma forma de série
  (`w = 0`).

### Regra de adoção (do Larry)
O B1 substitui o B0 no Stage 2 **somente se** o IC 95% da diferença pareada de log loss
(B1 - B0) no teste estiver inteiramente abaixo de zero **e** o B1 estiver concluído e
revisado pelo `leakage-reviewer` até **27/11/2026 18:00 BRT**. Senão, o B0 segue no
Stage 2 e o B1 fica para o Stage 3.

Se adotado: ratings do Stage 2 = histórico até o corte + resultados do Major no CSV,
aplicados na ordem das rodadas, sem ajustar hiperparâmetro algum.

## D21
No teste: calibração do favorito por faixas, com intervalo de Wilson 95%, incluindo o
agregado acima de 80%.
