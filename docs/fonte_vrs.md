# Fonte: VRS oficial da Valve

Repositório: <https://github.com/ValveSoftware/counter-strike_regional_standings>
Clone usado: commit `f8c55f250fdef796d708aa32814587932154fa04` (02/11/2026, "Updating
Regional Standings for 11/2/2026"), cerca de 314 MB, `--depth 1`.

```
git clone --depth 1 https://github.com/ValveSoftware/counter-strike_regional_standings \
    ../_external/counter-strike_regional_standings
```

O código procura o clone em `../_external/counter-strike_regional_standings` (ao lado do
projeto) ou em `VRS_REPO_DIR`. Só se leem arquivos Markdown; o código JavaScript do
repositório não é executado.

O rodapé dos arquivos de detalhes diz: *"Event data for Regional Standings provided by
HLTV.org"*. Os dados chegam por publicação da Valve; não há acesso nosso ao HLTV.

## Estrutura (verificada)

| Pasta | Conteúdo |
|---|---|
| `invitation/<ano>/` | `standings_<global\|europe\|americas\|asia>_<AAAA_MM_DD>.md` e `details/<data>/` |
| `live/<ano>/` | mesmo formato; datas semanais em 2024 e começo de 2025, mensais depois |
| `model/` | código JavaScript do modelo da Valve (não usado) |
| `data/` | só `matchdata_sample_20230829.json` (amostra de 2023, fora do escopo) |
| raiz | `readme.md`, `modelfit.png` |

- **Datas:** `invitation` mensal de 2024_08_06 a **2026_11_02** (último). Em 2026 há 11
  datas: 01-05, 02-02, 03-02, 04-06, 05-04, 06-01, 07-06, 08-03, 09-07, 10-05, 11-02.
- **Classificação:** tabela `Standing | Points | Team Name | Roster | link`.
- **Detalhes:** um arquivo por roster ranqueado
  (`<posição>--<time>--<jogadores>.md`) com o cálculo dos pontos e a tabela de partidas.
- O TOR §1.1 (`tournament-operation-requirements.md`) aponta `invitation` como a versão
  relevante para convites.

## Há histórico de partidas? Sim

Colunas da tabela de partidas: `Match Played, Match ID, Date, Opponent, W/L, Age Weight,
Event Weight, Bounty Collected, Opponent Network, LAN Wins, H2H Adj., Roster`.

| Informação | Disponível? |
|---|---|
| Data, adversário, vitória/derrota, elenco usado | sim |
| Os dois lados da partida | pelo `Match ID` **dentro** do snapshot (os ids são renumerados a cada snapshot) |
| LAN | só nas vitórias que entram nas 10 melhores do time; fora disso é desconhecido |
| Formato (Bo1/Bo3), placar, mapas | **não** |
| Evento, tier | **não** |
| Estatísticas por jogador | **não** |

## Uso no projeto

`python -m ingest.vrs_matches` → `data/processed/matches.parquet`.

- Snapshots de 2025-06-02 a 2026-11-02 (um por data; `invitation` tem preferência).
- Cada snapshot cobre cerca de 6 meses; a união é deduplicada por (data, elenco ou nome
  de cada lado), preservando partidas repetidas no mesmo dia.
- **Normalização de nomes:** só espaços nas pontas e maiúsculas/minúsculas. A identidade
  de um time é o **elenco** (pelo menos 3 jogadores em comum), como na regra de roster do
  VRS; o nome só é usado quando o elenco é desconhecido.
- **Rating point-in-time:** pontos do último snapshot **estritamente anterior** à data da
  partida.

### Cobertura obtida (execução de 26/11/2026)

| Item | Valor |
|---|---:|
| Partidas, 2025-06-01 a 2026-11-01 | 16.225 |
| Com rating dos dois lados | 13.127 |
| Lados com rating achado pelo elenco / pelo nome / não achado | 28.808 / 72 / 3.570 |
| Partidas com elenco desconhecido em algum lado | 1.191 |
| Visões repetidas entre snapshots, unificadas | 60.259 |
| `Match ID` inconsistentes | 0 |
| Linhas com mesmo par no mesmo dia | 300 |

- As linhas "mesmo par no mesmo dia" não excedem o que um único snapshot já mostra: não
  são duplicatas criadas pela união. Se o VRS repetir partidas internamente, não há como
  detectar.
- **Datas:** o VRS grava o dia no fuso `America/Los_Angeles` (`model/report.js` L206 e
  `model/main.js` L26 do repositório). Singapura está 16 h à frente em novembro; por isso
  o corte da calibração é **exclusivo em 2026-11-23**.
- **Vazamento:** 16 linhas têm data igual à do próprio snapshot (2025-09-01 e
  2026-01-05), nenhuma posterior; a ingestão falha se aparecer uma posterior. O rating
  usado é sempre de snapshot anterior à partida. Snapshots publicados a partir do corte
  não são lidos.
- **Commit fixado:** `ingest.seeds` e `ingest.vrs_matches` falham se o clone estiver em
  outro commit (`VRS_ALLOW_OTHER_COMMIT=1` libera uma atualização intencional).
- **Não verificado (clone raso):** a data no nome do arquivo não prova quando ele foi
  publicado, nem que arquivos antigos não tenham sido regenerados depois. Daria para
  conferir com o histórico completo do git.
- **Viés de seleção:** a união usa snapshots posteriores à partida. No treino do B0 só 2
  de 5.196 partidas são vistas por um único lado; sem elas o beta vai de 0,1558 a 0,1557.
- **`lan` não pode ser feature:** só aparece em vitórias que entram nas 10 melhores do
  time, logo depende do resultado e do futuro.
- **Lacunas:** nada de 02/11 a 23/11/2026 (não há snapshot posterior); rosters que nunca
  aparecem ranqueados não têm arquivo próprio; LAN, formato e evento ausentes.
