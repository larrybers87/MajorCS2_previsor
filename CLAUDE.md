# MajorCS2_previsor

## Objetivo
Prever o PGL Major Singapore 2026 de CS2: 3 stages suíços de 16 times + playoffs de 8.
Saída: probabilidade de cada time terminar 3-0, 3-1, 3-2, 2-3, 1-3, 0-3 em cada stage
suíço e, no Stage 3, também posição final e chances nos playoffs. Atualização ao vivo.

## Leitura obrigatória antes de agir
1. `claude/design-v0.md` (arquitetura, validação, roadmap; ver "Atualizações 26/11")
2. `claude/fontes-de-dados.md` (histórico de fontes; **as decisões abaixo prevalecem**)
3. `docs/` (rulebook da Valve e documentos de regras); `docs/regras_suica.md` resume com
   citações. As cópias da Valve ficam só no disco (sem licença): ver `docs/fontes_valve.md`
4. `docs/decisoes.md` (decisões adotadas; não reabrir sem pedir)
5. `docs/duvidas_abertas.md` (pontos em aberto e divergências)

**Se algo contradisser o rulebook (`docs/major-supplemental-rulebook.md`), o rulebook
vence: registre a divergência em `docs/duvidas_abertas.md`.** Exceção explícita: a
decisão 2 abaixo (Stage 3 em Bo3 e final em Bo5), tomada pelo Larry e configurável.

## Convenções
- Python 3.11 (conda, Windows). Ambiente: `majorcs2`.
- Comentários, docstrings e documentação em português; identificadores de código em inglês.
- Código em `src/{ingest,features,models,swiss,sim,backtest}`, dashboard em `app/`,
  testes em `tests/`, dados em `data/{raw,processed,manual}` (fora do git), previsões em
  `predictions/` (versionadas, nunca sobrescritas).
- Features sempre point-in-time: só dados anteriores à data da partida.

## Comandos
```
conda env create -f environment.yml     # primeira vez
conda activate majorcs2
pytest                                  # todos os testes
python -m swiss.exhaustive_check        # verificação exaustiva dos emparelhamentos (~20 min)

git clone --depth 1 https://github.com/ValveSoftware/counter-strike_regional_standings ../_external/counter-strike_regional_standings
python -m ingest.seeds                  # data/processed/seeds_singapore.csv
python -m ingest.vrs_matches            # data/processed/matches.parquet
python -m backtest.b0_calibration       # B0 congelado (V3) e docs/b0_calibracao.md
python -m backtest.h10_format           # modelo do Stage 2 e docs/h10_verossimilhanca.md
python -m backtest.b1_selection         # B1 contra B0 e docs/b1_avaliacao.md
python -m sim.b1_ratings --stage1 data/manual/stage1_results.csv   # ratings B1 do Major
python -m sim.v3_stage1 --results data/manual/stage1_results.csv
python -m backtest.v3_evaluation                         # docs/avaliacao_stage1.md
python -m sim.export_site                                # dados de app/index.html
python -m sim.site_server                                # site com Simulador (127.0.0.1:8000)
python -m sim.round_update                               # docs/roteiro_rodadas_stage2.md
python -m backtest.b1_decay_report                       # variantes do B1 (desenvolvimento)
python -m backtest.stage2_evaluation                     # fim do Stage 2 (emendas 1-3)
python -m sim.stage3_check                               # checagem de desastre (uma vez)
python -m sim.predict_stage3                             # previsão do Stage 3, sem playoffs
python -m sim.anexo_d25 --official <pasta da previsão>   # sensibilidade (não oficial)
python -m backtest.calibration_diagnostic                # docs/calibracao_teste_b0.md
predict_stage2 --stage1 data/manual/stage1_results.csv [--stage2 data/manual/stage2_results.csv]
predict_stage2 --conditioned [--stage1 <CSV parcial>]
```

## Regras de trabalho
- Não chute. Regra ou requisito ambíguo ou ausente: anotar em `docs/duvidas_abertas.md`
  e perguntar. Não preencher lacunas com suposições.
- Marcar explicitamente o que é VERIFICADO (com citação) e o que é HIPÓTESE.
- Usar lista de tarefas e marcar como concluído só o que foi testado.
- Nunca usar force push, `git reset --hard` nem apagar arquivos do usuário. Antes de
  qualquer operação git destrutiva, perguntar.
- Não commitar dados brutos, segredos nem e-mail em código (ver `.gitignore`).
- Antes de qualquer push, mostrar `git log --format='%an <%ae>'`. O autor e o e-mail
  atuais foram autorizados; outro e-mail pessoal: parar e perguntar. Push só de `main`
  (nunca `--all`, `--tags`, `--mirror`).
- Não versionar arquivos de terceiros sem licença que permita redistribuir.
- Coleta: salvar o bruto em disco na primeira vez e nunca coletar duas vezes; respeitar
  os limites da fonte. Coleta em massa só com aprovação explícita.
- Código de terceiros é auditado (`scraper-reviewer`) antes de ser instalado ou executado.

## Subagentes (`.claude/agents/`, todos somente leitura: Read, Grep, Glob)
- `rules-auditor`: extrai regras do rulebook com citação; nunca escreve código.
- `leakage-reviewer`: procura vazamento temporal em features/backtest.
- `scraper-reviewer`: audita código de terceiros.

## Decisões já tomadas (detalhes em `docs/decisoes.md`)
1. **Fontes somente permitidas.** Em uso: VRS oficial da Valve e resultados do Major;
   **nenhuma outra coleta** até nova decisão. GRID descartado; LiquipediaDB opcional, só se
   o Larry avisar que tem a chave; API MediaWiki e HTML da Liquipedia fora. Estatísticas
   por jogador e por mapa fora do escopo (`docs/fontes_dados.md`). **Proibido:** contornar
   Cloudflare/anti-bot, SeleniumBase UC, undetected-chromedriver e acesso automatizado ao
   HLTV.
2. Stage 3 todo Bo3 e final Bo5 ativos por configuração; 3º lugar em Bo3 (hipótese);
   playoffs Bo3 nas demais fases; Stages 1 e 2 pelo rulebook.
3. H1 provisória; H5 (posição final = seed final do stage); probabilidades fixas dentro
   de cada simulação na v1, ratings atualizados entre execuções.
4. V3 (Stage 1) é retrospectivo; teste prospectivo é o Stage 2, com previsões em commit
   antes da primeira partida.
5. Repositório público; push de `main` autorizado.
6. D15 fechada: THE ONE = 1win e GOSH = BC.Game, mapeados pelo elenco.
- Modelo do Stage 2: **B0** com a regra de formato (faixa w=0/w=1); o B1 não atingiu o
  critério pré-registrado e fica para o Stage 3.
- Previsão oficial do Stage 2: a última enviada antes de 28/11 04:00 UTC
  (`docs/avaliacao_stage2.md` + emendas; roteiro em `docs/roteiro_sexta.md`). Anexo D25
  (grade 3x3, emendas) não é oficial.
- Stage 3: média 50/50 de B0 e B1 com checagem de desastre
  (`docs/preregistro_stage3.md` + **emendas**; a 1 substitui a regra de 0,70); não usar o
  teste já visto como argumento. Pré-registros se mudam só por emenda em arquivo novo.
- B1 (D33): para prever uma rodada, passar a `b1_ratings` só as rodadas anteriores.
- Dados a partir de 2025-06-01 com decaimento temporal (half-life a testar a partir do
  B1); dashboard local; aceite de modelo por log loss no backtest; calibração
  obrigatória; sem rede neural no escopo inicial.
