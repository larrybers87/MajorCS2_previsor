# Tarefas da sessão 01 (26/11/2026)

Marcado como concluído só o que foi testado ou conferido.

## A. Repositório e estrutura
- [x] Conferir git e remoto (pasta não era repo; remoto vazio, nada a integrar)
- [x] `git init -b main`, `origin` configurado, `git fetch`
- [x] Estrutura de pastas
- [x] Ambiente `majorcs2` (Python 3.11.18) a partir de `environment.yml`; pytest roda
- [x] CLAUDE.md
- [x] Subagentes em `.claude/agents/` (registrados pelo Claude Code só no meio da sessão)
- [x] Commit inicial
- [ ] Push (aguarda resposta: repositório público, ver D14)

## B. Regras
- [x] `docs/regras_suica.md` com citações (auditoria + conferência)
- [x] Comparação do rulebook local com o upstream da Valve (idênticos)
- [x] Divergências em `docs/duvidas_abertas.md`

## C. Engine suíça
- [x] Estado, `pair_round`, `apply_results`, `buchholz`, `is_decider_match`
- [x] `simulate_stage` vetorizado, com resultados já jogados
- [x] Testes pedidos (71 passam no total)
- [x] Verificação exaustiva dos emparelhamentos
- [ ] V2 com emparelhamentos reais (teste `skip`: sem dados)
- [ ] Playoffs (fora do escopo desta sessão)

## D. Spike do scraper
- [x] Download sem instalar, SHA-256 conferido
- [x] Auditoria (`scraper-reviewer`): aprovado com condições
- [x] Venv isolado com versões e hashes; guarda de requisições testada
- [x] Teste real: 1 requisição, bloqueada pelo Cloudflare (403)
- [x] (a) respondida: bloqueou
- [ ] (b)-(d) verificar com HTML real (impedido pelo bloqueio; só leitura do código)
- [x] (e) esquema SQLite documentado (banco vazio, gerado offline)
