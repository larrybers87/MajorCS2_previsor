# EMENDA 6 ao pré-registro do Stage 3 (candidatos a modelo)

Redigida e **aprovada pelo Larry em 27/11/2026** (itens A1 a A5, com a regra de erro
padrão de A3 e o texto de A4 definidos por ele), **enviada antes de rodar qualquer
candidato**. Não reescreve o [original](preregistro_stage3.md) nem as emendas 1 a 5.
Detalhes de execução fixados junto, sem criar regra:
[emenda_06_detalhes_execucao.md](emenda_06_detalhes_execucao.md).

## 0. Já conhecido ao redigir
- Resultados do Stage 1 e o desempenho de B0 e B1 nele
  ([adendo](adendo_preregistro_stage1.md)); desempenho de B0 e B1 no desenvolvimento e no
  teste (jun–nov/2026); Glicko-1 pior que o Elo no desenvolvimento.
- Nenhum resultado do Stage 2. Nenhuma previsão do Stage 3.
- **Nenhum candidato abaixo foi rodado**, e nenhuma métrica da combinação de referência
  foi calculada no desenvolvimento.

## 1. Alcance
- Esta emenda precisa ser enviada **antes de rodar qualquer candidato** e antes de
  qualquer previsão do Stage 3.
- A previsão oficial do **Stage 2 não muda**.
- Ela **supera o "sem reponderar"** do adendo de 27/11 e, condicionalmente, o modelo
  principal da seção 1 do original, **apenas para o procedimento descrito aqui**.
- Por que a decisão não usa o Stage 1: nenhuma partida dos Stages 1 e 2 entra em ajuste,
  escolha de hiperparâmetros ou aceitação (o histórico termina em 01/11); critérios e
  candidatos ficam fixos antes de rodar; pesos só por ajuste definido aqui; a única etapa
  que olha os Stages 1 e 2 é a checagem de desastre, que só pode **devolver** à combinação
  pré-registrada, nunca promover um candidato.
- **Limite:** a decisão de abrir este procedimento foi tomada depois de se saber que o B1
  foi melhor no Stage 1. As regras não eliminam isso.

## 2. Dados e protocolo comum
- `matches.parquet`, SHA-256
  `9439d9ba0325c71406af2877844b9e34ebdf5aa649108ea31cab1279e9e0bcd2`, do VRS no commit
  `f8c55f250fdef796d708aa32814587932154fa04`; histórico desde 01/06/2025; alvo: os dois
  times no top 100 do snapshot anterior.
- Desenvolvimento: 01/09/2025 a 31/05/2026 (2.877 partidas). **A decisão usa só ele.**
- Walk-forward mensal: tudo que é ajustado para o mês `m` usa apenas partidas anteriores a
  `m`; nenhuma previsão usa resultados do próprio dia.
- Formato (H10): todo preditor tem as variantes w=0 (forma Bo3) e w=1 (forma Bo1), cada
  uma ajustada na sua forma; a probabilidade avaliada é a média das duas.
- **[A1] Partidas avaliadas:** dez/2025 a mai/2026 (**1.670**). Set a nov/2025 servem de
  aquecimento das janelas aninhadas, porque os hiperparâmetros só podem ser escolhidos
  dentro do desenvolvimento. (Avaliar as 2.877 exigiria escolher os de set/2025 com dados
  de jun–ago, fora do desenvolvimento.)
- Janelas aninhadas: para o mês `m`, cada candidato com hiperparâmetros usa o de menor log
  loss nas previsões fora da amostra dos meses do desenvolvimento anteriores a `m` em que
  houver previsão.

## 3. Referência a vencer
A combinação B0/B1 definida na **seção 2, "Combinação", de
[preregistro_stage3.md](preregistro_stage3.md)**, confirmada na seção E1.2 da
[emenda 1](preregistro_stage3_emenda_01.md): média de quatro probabilidades (B0 w=0, B0
w=1, B1 w=0, B1 w=1), **peso 1/4 cada**, B1 com a configuração congelada, **sem a checagem
de desastre**.

- **[A2] "Sem refit":** os pesos 1/4 e a configuração do B1 não são reajustados; os betas
  do B0 e do B1 são ajustados **walk-forward**, mês a mês, como os dos candidatos. Os betas
  fixos do pré-registro foram ajustados com dados até 01/11/2026, que incluem o período
  avaliado e o teste: usá-los no desenvolvimento seria vazamento. Eles continuam valendo
  para a previsão do Stage 3.
### Vieses conhecidos
- **A favor da referência:** a configuração do B1 (entre 172) e a do B0 (entre 4) foram
  escolhidas no desenvolvimento inteiro, inclusive nos meses avaliados.
- A lista de candidatos foi desenhada já conhecendo o desenvolvimento, o teste e o
  Stage 1.
- **Calibração no desenvolvimento, vista antes de o C3 ser fixado nesta lista:** acima de
  80%, o B1 previu 84% e observou **93%** (59 partidas); o B0 previu 84% e observou 86%
  (28 partidas), na forma w=0. Ordem dos fatos: a "calibração walk-forward" já constava do
  pedido que originou a lista, anterior ao cálculo destes números; a definição do C3
  abaixo foi redigida depois de vê-los. Do teste já se conhecia também o excesso de
  confiança do B0 acima de 80% (D21).

## 4. Candidatos (lista fechada)

| Id | Candidato | Definição | Hiperparâmetros (janelas aninhadas) |
|---|---|---|---|
| C1 | Elo com margem de rounds | **Não executável:** o placar está vazio nas 16.225 partidas. Fora; não pode ser acrescentado depois sem nova emenda | — |
| C2 | Glicko-2 (desvio e volatilidade por time) | Algoritmo de Glickman; período = 1 dia; identidade por elenco como no B1; prior `1500 + s x (VRS − 1000)`; volatilidade inicial 0,06; sem jogar, o desvio cresce com a volatilidade, por dia, até o inicial. `p = logística(beta x g x (rA − rB)/100)`, `g = 1/raiz(1 + 3(fA² + fB²)/π²)`, `f` = desvios na escala interna do Glicko-2 | desvio inicial {200, 350}; τ {0,3; 0,6; 1,2}; s {0; 0,5}: 12 |
| C3 | Calibração walk-forward da referência | Ajustada nas previsões fora da amostra da referência em meses anteriores. Platt sem intercepto, `p' = logística(a x logit p)`; ou isotônica no lado do favorito (não decrescente, limitada a [0,5; 0,999]). Sem intercepto porque a ordem dos times é arbitrária | método {Platt, isotônica}: 2 |
| C4 | Empilhamento B0/B1 | `p = logística(a x logit pB0 + b x logit pB1)`, `a, b ≥ 0`, sem intercepto, máxima verossimilhança nas previsões fora da amostra dos meses anteriores (pB0 e pB1 = média de w). **Nenhum peso escolhido à mão** | nenhum |
| C5 | B1 com elencos | `p = logística(beta x ΔB1/100 + c1 x Δexp + c2 x Δidade)`, sem intercepto; `exp = ln(1 + partidas anteriores do núcleo)` (núcleo: 3 jogadores em comum); `idade = ln(1 + dias desde a primeira partida da escalação de 5 atual)`; só dias anteriores; elenco desconhecido: diferença zero | nenhum |

**LAN não é usada:** o campo só aparece em vitórias que entram nas 10 melhores do time, ou
seja, depende do resultado e do futuro ([fonte_vrs.md](fonte_vrs.md)). C5 passa por
revisão de vazamento antes de o resultado ser aceito.

## 5. Métrica e aceitação
- `d_i = log loss do candidato − log loss da referência`, nas partidas de [A1]; `d` =
  média. Brier relatado, sem papel na regra.
- **[A3] Erro padrão:** o bootstrap **por torneio** pedido não é possível, porque o VRS
  **não identifica o torneio** (campo `event` vazio em todas as partidas; os arquivos de
  origem não trazem nome nem id de evento). `EP` = **o maior** entre:
  - o EP por bootstrap de **blocos de semana ISO** (10.000 réplicas, semente 20261203;
    desvio padrão das médias reamostradas);
  - o EP **pareado por partida** (desvio padrão de `d_i`, divisor `n − 1`, sobre a raiz de
    `n`).

  **Os dois são registrados na tabela.** O EP por bootstrap de dias é relatado, sem papel
  na regra.
- **Aceito se `d < −2 x EP`.** No máximo **um** aceito: entre os que passam, o de menor log
  loss nessas partidas.
- Tabela obrigatória, nas mesmas partidas: referência, **B1 sozinho** e **B0 sozinho** (sem
  valor de regra) e cada candidato. Se um candidato vencer a referência mas não o B1
  sozinho, o relatório diz isso.

## 6. Teste jun–nov/2026 (só informação)
Depois de decidida a seleção, cada candidato e as referências rodam **uma vez** em
01/06 a 01/11/2026 (1.479 partidas), com os hiperparâmetros escolhidos no desenvolvimento
inteiro. **Não influencia** aceitação nem reabre a escolha, como exige o pré-registro.

## 7. Se um candidato for aceito
- Ele **vira o modelo oficial do Stage 3**. A combinação pré-registrada é calculada e
  publicada **ao lado**, como referência.
- Retreino final: hiperparâmetros escolhidos no desenvolvimento inteiro; pesos de C3 e C4
  ajustados só no desenvolvimento; betas e coeficientes de rating ajustados com dados até
  01/11/2026, como os pré-registrados; **resultados dos Stages 1 e 2 entram só agora**,
  nos ratings, rodada a rodada (D33).
- **[A4] Checagem de desastre do candidato**, no molde da
  [emenda 1](preregistro_stage3_emenda_01.md) (Stages 1 e 2 juntos, calculada uma vez,
  antes do primeiro jogo do Stage 3, 10.000 réplicas por partidas, semente 20261202). Ele
  **falha** se (a) o log loss dele for pior que o do 50% com significância unilateral de
  95% **e** (b) for pior que o da combinação pré-registrada (diferença pontual). Se
  falhar, o oficial **volta a ser a combinação pré-registrada**, que segue sujeita à
  própria checagem (pode virar B0 puro). **A checagem de desastre é uma proteção frouxa
  por desenho, não um teste de qualidade:** exige as duas condições, usa no máximo 66
  partidas e só detecta falha grosseira; passar nela não mostra que o modelo é bom.
- **[A5] Sensibilidade aos reservas** (emendas 4 e 5): aplicada ao modelo oficial; em C3 e
  C4, o desconto entra no B0 e no B1 de base; em C2 e C5, soma-se ao logit do time o mesmo
  deslocamento de log-odds do B0. A tabela suplementar com B0 e B1 continua.

## 8. Se nenhum for aceito
Nada muda: vale o pré-registro com as emendas 1 a 5.
