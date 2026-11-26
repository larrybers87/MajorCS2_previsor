# Previsor Major CS2 — Desenho v0.1 (26/11/2026)

## 1. Saídas do sistema
- Stages 1 e 2: probabilidade de cada time terminar 3-0, 3-1, 3-2, 2-3, 1-3, 0-3 (e P(avançar) = soma dos três primeiros).
- Stage 3: o mesmo + posição final na suíça + P(playoffs: QF, SF, final, campeão, 3º lugar).
- Atualização "ao vivo": resultados já jogados entram como fatos, o restante é simulado; os ratings são atualizados a cada partida.

## 2. Regras — status de verificação
**Confirmado em 2+ fontes (Wikipedia, Strafe, Insider Gaming, GlobalGameGuide):**
- 3 stages suíços de 16 times; 3 vitórias avança, 3 derrotas elimina; 8 avançam por stage.
- Stage 1: 16 times semeados pelo VRS (snapshot de 2/11/2026). Stage 2: 8 convidados + 8 do Stage 1, seed inicial por VRS. Stage 3: 8 convidados + 8 do Stage 2.
- Stages 1-2: Bo1, exceto partidas de avanço/eliminação (Bo3). Stage 3: tudo Bo3.
- Playoffs: 8 times, eliminatória simples, Bo3 até a final (Bo5), com disputa de 3º lugar (inédita).
- Rodada 1: seed 1v9, 2v10, ..., 8v16.

**Confirmado em 1 fonte (Strafe, 2023; Wikipedia 2026 concorda no geral):**
- A partir da R2, só jogam times com o mesmo registro V-D. Dentro do grupo, ordena-se por Buchholz (soma de V-D dos oponentes já enfrentados); desempate pelo seed inicial; melhor ordenado x pior ordenado, evitando rematches.

**NÃO verificado (não consegui abrir o rulebook da Valve daqui):**
- Algoritmo exato de emparelhamento quando "topo x fundo" gera rematch (o rulebook tem uma regra de prioridade específica).
- Seeding do bracket de playoffs. A Wikipedia diz "Buchholz final do Stage 3"; ESPECULAÇÃO: provavelmente registro primeiro, depois Buchholz.
- Chaveamento exato dos playoffs.
- Datas divergem entre fontes (Stage 1 começa em 24 ou 25/11).
**Ação:** baixar o Major-Supplemental-Rulebook.md do repo ValveSoftware/counter-strike_rules_and_regs, versionar em docs/ e implementar a engine a partir dele.

## 3. Arquitetura
1. **Ingestão** (raw → parquet/DuckDB): eventos, partidas, mapas, stats por jogador por mapa, rosters com data, rankings (HLTV + snapshots VRS).
2. **Features point-in-time**: tudo calculado só com dados anteriores à data da partida.
3. **Modelo de partida** (nível de mapa) → P(Bo1) e P(Bo3) via modelo de veto.
4. **Motor suíço + Monte Carlo** (100k+ simulações, vetorizado/numba).
5. **Backtest** walk-forward.
6. **Dashboard** e rotina de atualização.

### Modelo de partida
- B0: regressão logística em diferença de pontos VRS.
- B1: Elo/Glicko com decaimento temporal.
- M1 (candidato principal): rating bayesiano de time + força por mapa (shrinkage para a média do time) + força agregada dos 5 jogadores (rating ajustado por oponente, decaimento exponencial, LAN com peso maior) + contexto (mudança de roster, H2H com shrinkage forte) → regressão logística regularizada.
- M2 (comparação): gradient boosting (LightGBM) com restrições monotônicas.
- Rede neural: fora do escopo inicial. Poucos dados independentes (centenas de partidas relevantes por ano entre os top 50) e ganho esperado sobre M1 é pequeno; reavaliar só se M2 mostrar sinal.
- Calibração (Platt/isotônica) obrigatória: o simulador depende de probabilidades, não de classificação.
- Regra de aceite: um modelo só substitui o anterior se vencer em log loss no backtest; se M1/M2 não vencerem B1, usamos B1.
- Veto: P(mapa jogado) a partir do map pool de cada time; Bo1 = Σ p(mapa)·P(vitória no mapa); Bo3 = pick/ban + decider.

## 4. Validação
**Problema:** o Stage 1 tem só 33 partidas (24 vitórias dos 8 classificados + 9 dos eliminados). Erro padrão do log loss com n=33 é ~0,08 (estimativa minha), maior que a diferença típica entre bons modelos (~0,01-0,02). O Stage 1 NÃO consegue ranquear modelos.
**Plano:**
- V1 — Backtest walk-forward em Majors e grandes LANs anteriores: treinar com dados até o dia anterior ao evento, avaliar nas partidas. Métricas: log loss, Brier, curva de calibração por partida; e log-score/RPS da distribuição de registros finais por time.
- V2 — Teste da engine suíça: reproduzir, a partir dos resultados reais, os emparelhamentos reais de todas as rodadas de Stage 1 de Majors passados e deste Major. Meta: 100% de coincidência. Isso valida as regras, independente do modelo.
- V3 — Stage 1 deste Major como "prova final" do pipeline: modelo congelado com dados até 23/11. Qualquer ajuste feito olhando o resultado do Stage 1 invalida o teste.
- Vazamento (leakage): as páginas de time/jogador do HLTV mostram estatísticas de HOJE. Usar isso para prever partidas passadas vaza o futuro. Precisamos reconstruir os stats a partir de partidas/mapas com corte por data.

## 5. Dados
- HLTV bloqueou o fetch automatizado (client_error, provável Cloudflare); o sandbox da nuvem também só acessa uma allowlist.
- Opções: (a) Claude in Chrome no seu navegador, lento, usa sua sessão; (b) scraper local no seu PC com cache em disco e rate limit baixo; (c) fontes alternativas (VRS oficial no GitHub da Valve, Liquipedia API, outras) — acesso e termos NÃO verificados.
- Verificar os termos de uso do HLTV antes de coleta em massa (ESPECULAÇÃO: provavelmente proíbem scraping automatizado).
- Regra de ouro: salvar o HTML/JSON bruto em disco na primeira coleta e nunca coletar duas vezes.
- Tabelas: teams, players, rosters(data), events, matches, maps, player_map_stats, rankings(data), vrs_snapshots.

## 6. Repositório
Estrutura sugerida: docs/ (rulebook, este desenho), data/raw, data/processed, src/ingest, src/features, src/models, src/swiss (engine), src/sim, src/backtest, app/, tests/.
Sincronização (rodar na pasta local):
```
git status                      # se "not a git repository": git init -b main
git remote -v                   # se vazio: git remote add origin https://github.com/larrybers87/MajorCS2_previsor.git
git fetch origin
git pull --rebase origin main --allow-unrelated-histories
git push -u origin main
```
Se a pasta local e o remoto tiverem arquivos com o mesmo nome (README, .gitignore), resolver o conflito antes do push.

## 7. Roadmap
- M0: sincronizar repo, versionar rulebook, congelar regras.
- M1: coleta mínima (resultados dos 3 eventos, rosters, rankings, 6-12 meses de partidas LAN).
- M2: engine suíça + testes V2 + simulador Monte Carlo com ratings fixos.
- M3: baselines B0/B1 + backtest V1.
- M4: M1/M2 com features de mapa e jogador; comparação.
- M5: previsão Stage 2 ao vivo.
- M6: dashboard.
- M7: Stage 3 + playoffs.

## 8. Perguntas abertas
1. Como coletar dados do HLTV (Chrome, scraper local, outra fonte)?
2. Formato do dashboard: Streamlit local ou site estático (GitHub Pages) atualizado por script?
3. Tempo de histórico a coletar (12 meses? desde o Austin 2025?).

## Atualizações 26/11
Onde esta seção divergir do texto acima, vale esta seção. Detalhes em
`docs/decisoes.md`, `docs/regras_suica.md` e `docs/duvidas_abertas.md`.

### Correções de regras (o rulebook vence)
- **D4 — emparelhamento:** "melhor ordenado x pior ordenado disponível sem rematch" vale
  só nas rodadas 2 e 3. Nas rodadas 4 e 5 vale a tabela de 15 prioridades do rulebook
  (primeira linha sem rematch).
- **D5 — seeds dos Stages 2 e 3:** convidados são os seeds 1-8 (pelo VRS); os 8
  classificados são os seeds 9-16 **pelo seed final do stage anterior** (cartel,
  Difficulty, seed inicial), não pelo VRS.

### Decisões
- Fontes somente permitidas (VRS oficial, API da Liquipedia, GRID). HLTV automatizado,
  contorno de anti-bot, SeleniumBase UC e undetected-chromedriver: proibidos.
- Stage 3 todo em Bo3 e final em Bo5 ativos por configuração (não constam no rulebook);
  3º lugar em Bo3 como hipótese; demais partidas dos playoffs em Bo3.
- Posição final = seed final do stage. Probabilidades fixas dentro de cada simulação (v1).
- V3 (Stage 1) é retrospectivo; o teste prospectivo é o Stage 2, com previsões em commit
  antes da primeira partida.
