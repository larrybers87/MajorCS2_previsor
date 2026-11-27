# Relatório da sessão 06 — integridade, rodadas do Stage 2, Simulador e playoffs (27/11/2026)

## Resumo
- Previsão oficial intacta, marcada com a tag local `stage2-oficial`
  ([registro](previsao_oficial_stage2.md)).
- V3 retrospectivo das 33 partidas com B0 e B1 lado a lado.
- Rotina por rodada, Simulador, Stage 2 ao vivo, Stage 3 e playoffs prontos.
- **Sem confirmação oficial** do formato e do horário do Stage 3.
- Modelos, engine (`src/swiss`) e pastas existentes de `predictions/` **não foram
  alterados**. Commit, push e envio da tag foram feitos depois, a pedido do Larry.

## 1. Integridade
`claude/regras-verificadas.md` **não foi fornecida**. Falta no repositório; em `claude/`
há só `design-v0.md` e `fontes-de-dados.md`. As citações do rulebook em uso estão em
[regras_suica.md](regras_suica.md). Se o arquivo do Project tiver itens além desses, eles
não foram considerados.

## 2. Testes da previsão oficial
13 testes, todos passam. As probabilidades por partida da rodada 1 estavam commitadas.

## 3. V3 retrospectivo (`predictions/v3_stage1/20261127T163922Z`)
33 partidas, depois dos jogos. Variante "média" de w=0 e w=1; EP = erro padrão entre
partidas.

| Modelo | log loss | Brier | Favorito venceu | log score dos cartéis (soma) |
|---|---|---|---|---:|
| B0 | 0,6865 (EP 0,030) | 0,2466 (EP 0,0145) | 21/33 | 28,17 |
| B1 | 0,6412 (EP 0,019) | 0,2245 (EP 0,0094) | 23/33 | 26,67 |
| Sem informação | 0,6931 | 0,2500 | - | 28,41 |

B1 − B0: log loss -0,045 (EP 0,025); Brier -0,022 (EP 0,012).

**Como ler:** retrospectivo, um único torneio, partidas e times dependentes, n = 33. A
diferença é menor que 2 erros padrão. Não ordena modelos e **não mudou nada**. O número
0,6855 do B0 com w=0 aparece nas primeiras seções do relatório da pasta; o 0,6734 da
sessão 03 era das 30 primeiras partidas.

**Consequência para o pré-registro do Stage 3:** o log loss do B1 nas partidas do Stage 1,
parte da checagem de desastre, passou a ser conhecido antes da data prevista. A regra não
mudou e a média 50/50 não foi calculada (D39).

A pasta registra `git_uncommitted_code: true` (o código da comparação ainda não estava
commitado). Entradas: `matches.parquet` SHA-256 `9439d9ba...bcd2`, `b1_params.json`
`720ffff6...c549`.

**Atualização:** depois do commit `d9e5a49`, a pasta foi regerada
(`predictions/v3_stage1/20261127T165555Z`, `git_uncommitted_code: false`), com
`matches.csv`, `teams.csv`, `comparison.csv`, `summary.md` e `model_params.json` idênticos
e as mesmas entradas. A pasta anterior foi mantida.

### Variantes de decaimento ([tabela completa](b1_decaimento_desenvolvimento.md))
Só desenvolvimento (2025-09 a 2026-05, 2877 partidas); a escolhida foi reproduzida.

| Meia-vida (mesmos s, K, m) | log loss |
|---|---:|
| sem decaimento (congelada) | 0,656347 |
| 180 dias | 0,656354 |
| 90 dias | 0,657061 |
| 60 dias | 0,657848 |

Melhor Glicko-1: 0,662127. Não calculei variantes no Major.

## 4. Rotina por rodada
`python -m sim.round_update` ([roteiro](roteiro_rodadas_stage2.md)). Ensaiada com
resultados **fictícios** da rodada 1 em pasta temporária. Escolhas minhas, a confirmar:
- probabilidades com o **B0 da oficial** (modelo do Stage 2); o B1 só é atualizado e salvo;
- saída em `round<N>/<carimbo>/`, para nunca sobrescrever;
- recusa a rodada 1, coberta pela oficial.

## 5. Site
- `python -m sim.site_server` (só 127.0.0.1). Modos: Ao vivo/Detalhado, Previsor,
  Simulador. O navegador envia escolhas; a chave vem da engine em Python.
- Simulador cobre os Stages 1 e 2; **não** cobre Stage 3 nem playoffs.
- Testado com cliques em navegador sem interface (completar o stage, mudar escolha
  anterior, limpar, começar do zero), sem erros no console. Ao vivo e Previsor do Stage 2
  conferidos com resultados fictícios.

## 6. Stage 3 e playoffs
- `src/sim/format_config.py`: `ACTIVE_FORMAT` = `anunciado` (atual) ou `rulebook`.
- `src/sim/playoffs.py`: seeds finais do Stage 3; quartas 1v8, 4v5, 2v7, 3v6; semifinais
  por chave (**H7, hipótese**); 3º lugar em Bo3 (**hipótese**) e final em Bo5 conforme a
  configuração. Simulação do Stage 3 encadeada com os playoffs; resultados reais de
  playoffs entram como fatos.
- **Falta** o script de previsão do Stage 3 (combinação pré-registrada B0/B1 e checagem de
  desastre).

### Tentativa na página oficial da PGL
- A página abre (HTTP 200), mas o HTML é só uma casca: o texto é carregado por script.
- Renderizar em navegador sem interface travou, sem saída.
- A consulta direta ao serviço de dados do site foi **bloqueada pela permissão desta
  sessão** e não foi repetida nem contornada.
- Busca na web: nenhum horário oficial do Stage 3; a imprensa segue dizendo Stage 3 todo
  em Bo3 (**não verificado**). Há fonte com datas divergentes (2 a 13/12, incluindo os
  playoffs).
- **Continuam sem confirmação:** Stage 3 todo em Bo3, final em Bo5, existência e formato
  do 3º lugar (a imprensa atribui o anúncio à PGL) e horários.
- Como resolver: abrir no navegador a
  [página do anúncio](https://news.pglesports.com/news/1775727332131-pgl-major-singapore-2026-introduces-3rd-place-decider-match-vrs-ranking-set-for-november-2)
  e a programação, e colar o texto.

## Em aberto
Ver [duvidas_abertas.md](duvidas_abertas.md): D36, D39, D40, D41; D35 (resolvida na
prática pelo filtro de rodadas, a confirmar); código da avaliação do Stage 2 e da previsão
do Stage 3.
