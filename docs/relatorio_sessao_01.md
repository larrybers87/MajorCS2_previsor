# Relatório da sessão 01 — fundação (26/11/2026)

## Resumo
- Repositório local, ambiente, regras documentadas e engine suíça prontos e testados.
- **O HLTV bloqueou o scraper na primeira requisição** (Cloudflare). Não há dados.
- O rulebook da Valve **não sustenta** três pontos do design: Stage 3 todo em Bo3, final
  em Bo5 e disputa de 3º lugar.
- Pela imprensa, o **Stage 1 está em andamento** e o Stage 2 começa em 28/11. Ainda não
  há modelo.
- Nada foi enviado ao GitHub.

## 1. Feito e testado

### A. Repositório
- A pasta não era um repositório git. Criado com branch `main` e `origin` configurado.
  O remoto está **vazio e é público**: nada a integrar.
- Estrutura criada; `claude/` e `docs/` não foram movidos nem renomeados.
- Ambiente `majorcs2` (Python 3.11.18, numpy 2.4.6, pytest 9.2.0), `environment.yml`,
  `pyproject.toml`, `.gitignore` (inclui também `*.sqlite`/`*.db`), `CLAUDE.md`.
- Três subagentes em `.claude/agents/`. O Claude Code só os registrou no meio da sessão:
  as duas auditorias rodaram em um agente genérico instruído a seguir o arquivo de
  definição (somente leitura por instrução, **não** imposta pela ferramenta).
  `leakage-reviewer` não foi usado (ainda não há features).

### B. Regras ([regras_suica.md](regras_suica.md))
| Ponto pedido | Resultado |
|---|---|
| 1. Rematch no "melhor x pior" | R2-R3: "pior disponível sem rematch"; R4-R5: tabela de 15 prioridades. O beco sem saída da R3 **não é coberto** (hipótese H1) |
| 2. Buchholz | Soma de (V - D) dos adversários; maior é melhor; desempate pelo seed inicial. Verificado |
| 3. Seeding | R1 1v9...8v16; Stages 2-3: convidados 1-8 (VRS), classificados 9-16 (seed final anterior) |
| 4. Formato | Bo3 só em avanço/eliminação; **sem exceção para o Stage 3** no RB |
| 5. Playoffs | Seed final do Stage 3; A: 1v8, 4v5; B: 2v7, 3v6; tudo Bo3. **Bo5 não consta; 3º lugar não coberto** |

O rulebook local é idêntico ao atual da Valve (commit `745a40758e`, 06/10/2026).

### C. Engine ([src/swiss](../src/swiss))
- Estado imutável, `pair_round`, `apply_results`, `announce_pairings`, `check_pairings`,
  `buchholz`, `standings`, `is_decider_match`, `advancing_teams`.
- `simulate_stage(prob_fn, estado, n_sims, rng)`: numpy; 100 mil simulações de um stage
  completo em **1,6 s** nesta máquina. Devolve cartéis, P(avançar) e posição final.
- **pytest: 71 passam, 1 pulado** (gancho V2). Inclui: rodada 1; invariantes em 2.000
  stages aleatórios; caminho completo derivado à mão, com o caso de rematch na rodada 5;
  beco sem saída da rodada 3; vetorizado igual à referência em 1.500 stages; 200 mil
  simulações com somas exatas; comparação com a distribuição analítica de moeda justa.
- Verificação exaustiva: o "melhor x pior" literal trava na R3 em 400 de 65.536
  combinações (0,61%); R4 e R5 sempre têm emparelhamento sem rematch (até
  1.073.741.824 históricos).
- Distribuição 2/3/3/3/3/2 e 33 partidas: **confirmadas como consequência do formato**;
  o RB não as afirma. A tabela de Austin confirma a parte dos eliminados.

Limites: a correção frente a **emparelhamentos reais** não foi testada (V2 sem dados);
H1-H9 são hipóteses; playoffs não implementados; `prob_fn` de teste não é modelo.

## 2. Spike do scraper

### Auditoria do `hltv-crawler` 0.1.0 — APROVADO COM CONDIÇÕES
- Só existe *sdist*; `pip download` executaria o build, então o arquivo foi baixado
  direto, com SHA-256 conferido
  (`c33c315da09e96b4384641a89c490bcfb133a2a9412d002cdb20c5ed7287e700`), e extraído sem
  executar, fora do repositório.
- Nada malicioso encontrado. Único host: `www.hltv.org`.
- Problemas: sem CLI `--max-pages` (e o parâmetro não limita o total de páginas); o
  intervalo de 2 s é violado em retries; 403 gera 3 tentativas; desafio com status 200
  seria gravado como página válida; entry point quebrado; path traversal no cache.
- A aprovação vale só para esse arquivo; `curl_cffi` e demais dependências não foram
  auditadas.
- Condições cumpridas: código carregado sem instalar, sem o orquestrador, venv isolado
  com versões e hashes, guarda própria
  ([hltv_spike.py](../src/ingest/hltv_spike.py), 15 testes sem rede) com teto de 3
  requisições, intervalo, sem redirect e sem retry.

O venv, o código auditado e o `requirements-spike.lock` estão na pasta temporária da
sessão (fora do repositório, como pedido; o auditor sugeria um local estável), que pode
ser apagada pelo sistema.

### Teste real: 1 de 3 requisições usadas
`GET https://www.hltv.org/results?startDate=2026-11-01&endDate=2026-11-23` (filtro até
23/11 para não puxar resultados do Stage 1).

| Pergunta | Resposta |
|---|---|
| (a) Cloudflare bloqueou? | **Sim.** HTTP 403, `cf-mitigated: challenge`, `server: cloudflare`, página "Just a moment..." (desafio `managed`, exige JavaScript e cookies), `cf-ray` `a60b4fb54e93b4e8-GRU`, 70 ms |
| (b) Campos extraídos | **Nenhum.** Pelo código: partida (id, URL, times, placar, evento, bo, vencedor, data), mapas (nome, rounds, CT/T), jogadores (kills, mortes, ADR, KAST, swing, rating) |
| (c) Stats por jogador **por mapa**? | **Pelo pacote, não**: só o agregado da série (`map_id` nulo). Se o HTML do HLTV permite obtê-las: **não verificado** |
| (d) Data em cada partida? | Pelo código, só vinda da página da partida (`data-unix`), e um upsert da listagem pode apagá-la. **Não verificado ao vivo** |
| (e) SQLite | `user_version` 2; tabelas `teams`, `players`, `events`, `matches`, `maps`, `player_match_stats`. Gerado **vazio**, offline |

Colunas: `matches`(match_id, event_id, event_name, match_datetime, team1_id, team2_id,
team1_score, team2_score, best_of, winner_team_id); `maps`(map_id, match_id, map_name,
team1_rounds, team2_rounds, team1/2_ct_rounds, team1/2_t_rounds, winner_team_id);
`player_match_stats`(id, match_id, map_id, player_id, team_id, rating, adr, kast, swing,
kd_diff, kills, deaths); `teams`(team_id, team_name, world_rank, updated_at);
`players`(player_id, player_name, nickname, team_id, updated_at); `events`(event_id,
event_name, start_date, end_date).

Resposta bruta em `data/raw/spike/` (fora do git). O livro-caixa de lá impede novas
requisições depois da falha.

### Fallback proposto (não implementado)
1. **SeleniumBase em modo UC** (preferido ao `undetected-chromedriver`, por ser, até onde
   sabemos, mais ativamente mantido; **não verificado** nesta sessão): navegador real,
   perfil dedicado, 1 aba, intervalo de vários segundos, cache em disco, parada no
   primeiro desafio não resolvido. Mesmo teto de 3 páginas no próximo spike. Auditar o
   pacote antes. Não há garantia de que passe pelo desafio `managed`.
2. Parser próprio, porque o pacote atual não serve para stats por mapa.

**Ressalva:** isso contorna uma proteção anti-bot que o site ativou de propósito. Os
termos de uso do HLTV **não foram verificados** (uma busca não encontrou o texto).
Recomendação: antes de implementar, ler os termos e priorizar fontes permitidas:
VRS oficial, API da Liquipedia (resultados e rosters) e GRID Open Access (aplicar já).
Para um baseline B0/B1 a tempo, VRS e resultados de séries podem bastar (hipótese).

## 3. Não feito
- Push para o GitHub.
- Qualquer coleta de dados úteis; V2; playoffs; ranking final do Major; modelo.
- Confirmação em fonte oficial de Stage 3 Bo3, final Bo5, 3º lugar e datas.

## 4. Dúvidas abertas
Lista completa em [duvidas_abertas.md](duvidas_abertas.md).

## 5. Perguntas para o Larry e o Claude (chat do projeto)

**Urgentes**
1. **Alvo:** com o Stage 1 em andamento e o Stage 2 em 28/11, o primeiro entregável é a
   previsão do Stage 2? Aceita um B0 (só VRS) para ter algo a tempo? (D10)
2. **Dados:** SeleniumBase UC no HLTV (após ler os termos) ou só fontes permitidas
   (VRS, Liquipedia, GRID)? Já aplicou ao GRID? (D12, D13)
3. **Stage 3, final e 3º lugar:** há regulamento ou anúncio oficial da PGL? Podemos
   adotar Stage 3 Bo3 e final Bo5 contra o texto do RB? Qual o formato da disputa de
   3º lugar? (D1, D2, D3, D9)
4. **Seeds:** qual a lista oficial dos 32 seeds (VRS de qual data)? Os emparelhamentos
   reais do Stage 1 servem para o primeiro teste V2 (testa H1-H6). (D6, H4)

**Importantes**

5. Aceita a hipótese H1 para o beco sem saída da rodada 3?
6. "Posição final no Stage 3" é o seed final do stage? (H5)
7. Probabilidades fixas dentro de cada simulação bastam? (D11)
8. Push no repositório público ou torná-lo privado antes? (D14)
9. O teste V3 continua valendo (modelo cortado em 23/11, feito depois do Stage 1)?

**Parado aqui, aguardando respostas.**
