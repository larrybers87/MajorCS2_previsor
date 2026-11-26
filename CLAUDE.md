# MajorCS2_previsor

## Objetivo
Prever o PGL Major Singapore 2026 de CS2: 3 stages suíços de 16 times + playoffs de 8.
Saída: probabilidade de cada time terminar 3-0, 3-1, 3-2, 2-3, 1-3, 0-3 em cada stage
suíço e, no Stage 3, também posição final e chances nos playoffs. Atualização ao vivo.

## Leitura obrigatória antes de agir
1. `claude/design-v0.md` (arquitetura, validação, roadmap)
2. `claude/fontes-de-dados.md` (fontes de dados e decisões)
3. `docs/` (rulebook da Valve e documentos de regras); `docs/regras_suica.md` resume com citações
4. `docs/duvidas_abertas.md` (pontos em aberto e divergências)

**Se algo contradisser o rulebook (`docs/major-supplemental-rulebook.md`), o rulebook
vence: registre a divergência em `docs/duvidas_abertas.md`.**

## Convenções
- Python 3.11 (conda, Windows). Ambiente: `majorcs2`.
- Comentários, docstrings e documentação em português; identificadores de código em inglês.
- Código em `src/{ingest,features,models,swiss,sim,backtest}`, dashboard em `app/`,
  testes em `tests/`, dados em `data/{raw,processed}` (fora do git).
- Features sempre point-in-time: só dados anteriores à data da partida.

## Comandos
```
conda env create -f environment.yml     # primeira vez
conda activate majorcs2
pytest                                  # todos os testes
pytest tests/test_swiss_rules.py -v     # um arquivo
python -m swiss.exhaustive_check        # verificação exaustiva dos emparelhamentos (~20 min)
```

## Regras de trabalho
- Não chute. Regra ou requisito ambíguo ou ausente: anotar em `docs/duvidas_abertas.md`
  e perguntar. Não preencher lacunas com suposições.
- Marcar explicitamente o que é VERIFICADO (com citação da seção do rulebook) e o que é HIPÓTESE.
- Usar lista de tarefas e marcar como concluído só o que foi testado.
- Nunca usar force push, `git reset --hard` nem apagar arquivos do usuário. Antes de
  qualquer operação git destrutiva, perguntar.
- Não commitar dados brutos nem segredos (ver `.gitignore`).
- Coleta: salvar o bruto em disco na primeira vez e nunca coletar duas vezes; rate limit
  baixo. Coleta em massa só com aprovação explícita.
- Código de terceiros é auditado (`scraper-reviewer`) antes de ser instalado ou executado.

## Subagentes (`.claude/agents/`)
- `rules-auditor`: extrai regras do rulebook com citação; nunca escreve código.
- `leakage-reviewer`: procura vazamento temporal em features/backtest; somente leitura.
- `scraper-reviewer`: audita código de terceiros; somente leitura.

## Decisões já tomadas
- Escopo temporal dos dados: a partir do Major de Austin 2025 (2025-06-01), com
  decaimento exponencial (half-life é hiperparâmetro; testar ~60/90/180 dias).
- Dashboard local por enquanto.
- Coleta por scraper (preferência por Selenium como fallback). Candidato: `hltv-crawler`
  (auditar antes). Rankings: VRS oficial da Valve. Liquipedia API opcional (rosters).
  GRID Open Access: candidatar em paralelo.
- Aceite de modelos: só substitui o anterior quem vencer em log loss no backtest; se
  M1/M2 não vencerem o B1, usamos o B1. Calibração obrigatória.
- Rede neural fora do escopo inicial.
- V3: modelo do Stage 1 congelado com dados até 2026-11-23; nenhum ajuste olhando o
  resultado do Stage 1.
