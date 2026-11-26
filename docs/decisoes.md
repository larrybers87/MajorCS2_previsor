# Decisões adotadas

Não reabrir sem pedir ao Larry.

## 26/11/2026 (sessão 02)

1. **Fontes: somente permitidas.** VRS oficial da Valve (git clone), API MediaWiki da
   Liquipedia (sem HTML; ler antes os termos em liquipedia.net/api-terms-of-use e
   respeitar o limite; se não abrir, parar e pedir) e GRID Open Access (aplicação em
   andamento; sem código para GRID ainda). **Proibido:** contornar Cloudflare/anti-bot,
   SeleniumBase UC, undetected-chromedriver, acesso automatizado ao HLTV. O
   `hltv-crawler` e o código do spike foram descartados; fica o relato em
   `relatorio_sessao_01.md`.
2. **Formato (configurável em `src/sim/format_config.py`):** Stage 3 todo em Bo3 e final
   em Bo5 ativos por padrão; disputa de 3º lugar em Bo3 como **hipótese**; demais fases
   dos playoffs em Bo3. Stages 1 e 2 seguem o rulebook. *Stage 3 em Bo3 e final em Bo5
   não constam no rulebook da Valve.*
3. **H1** aceita como provisória (resolver com V2 se aparecer um caso real). **H5:**
   posição final = seed final do stage (cartel, Difficulty, seed inicial); para os 8 que
   avançam no Stage 3 é o seed dos playoffs. **D11:** probabilidades fixas dentro de cada
   simulação na v1; ratings atualizados entre execuções, a cada resultado real.
4. **V3 é retrospectivo** (B0 usa só VRS pré-evento; nenhum parâmetro ajustado olhando o
   Stage 1). O teste **prospectivo é o Stage 2**: previsões em commit com carimbo de
   tempo ANTES da primeira partida do Stage 2.
5. O repositório pode continuar público. **Antes do push**, mostrar
   `git log --format='%an <%ae>'`; se algum autor for e-mail pessoal real, parar e
   perguntar. Nunca commitar dados brutos, segredos ou e-mail em código.

## Anteriores
- Escopo temporal: a partir de 2025-06-01 (`claude/fontes-de-dados.md`).
- Dashboard local por enquanto.
- Um modelo só substitui o anterior se vencer em log loss no backtest; senão fica o B1.
  Calibração obrigatória. Rede neural fora do escopo inicial (`claude/design-v0.md`).
