# Tarefas da sessão 02 (26/11/2026)

Marcado como concluído só o que foi testado ou conferido.

## A. Housekeeping
- [x] Subagentes com `tools: Read, Grep, Glob`, registrados; `leakage-reviewer` testado
- [x] Seção "Atualizações 26/11" em `claude/design-v0.md`; `docs/decisoes.md`; CLAUDE.md
- [x] Código e venv do spike removidos (fora do repo e `src/ingest/hltv_spike.py`)

## B. Seeds
- [x] Clone do VRS e `docs/fonte_vrs.md`
- [x] `data/processed/seeds_singapore.csv`; ordem de convites consistente
- [ ] Confirmar THE ONE = 1win e GOSH = BC.Game (D15)
- [ ] Validar a rodada 1 real (falta o CSV)
- [ ] V2 nas rodadas 2-5 (teste ativo, pulado sem o CSV)

## C. Resultados históricos
- [x] `data/processed/matches.parquet` a partir do VRS; cobertura e duplicatas relatadas
- [ ] Evento, tier, formato e placar (o VRS não informa; Liquipedia não consultada)

## D. Modelo B0
- [x] Calibração, escolha pontos x log, walk-forward com IC, `prob_fn`
- [x] Revisão com `leakage-reviewer` e correções
- [ ] Formato real das partidas (H10)

## E. V3 retrospectivo
- [x] Script testado com dados sintéticos
- [ ] Execução com o Stage 1 real (falta o CSV)

## F. Previsão do Stage 2
- [x] `predict_stage2` testado (completo, ao vivo e condicionado) com dados sintéticos
- [x] Modo condicionado executado com dados reais (0 partidas) e commitado
- [ ] Previsão com o Stage 1 completo (falta o CSV)
- [ ] Publicar com carimbo verificável antes da 1ª partida (D18)

## G. Entrega
- [x] pytest: 93 passam, 1 pulado
- [x] Relatório, dúvidas, commits locais
- [ ] Push (aguarda decisão sobre o e-mail dos autores)
