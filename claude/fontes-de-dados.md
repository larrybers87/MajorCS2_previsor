# Fontes de dados e decisões de coleta (26/11/2026)

## Decisões do Larry
- Escopo temporal: a partir do Austin 2025 (jun/2025). Dados antigos pesam menos via decaimento exponencial (half-life como hiperparâmetro, testar ~60/90/180 dias no backtest).
- Dashboard: local por enquanto.
- Coleta: scraper (preferência por Selenium; ver abaixo).
- Último Major antes de Singapore: IEM Cologne 2026 (jun/2026). Budapest (dez/2025) também está na janela (não verificado).

## Resultado da pesquisa (nenhum dataset pronto cobre jun/2025–nov/2026)
- CounterQuant (HuggingFace): releases com atraso de 2 anos; 2024 sai em 2026, 2025 em 2027. Não serve.
- Kaggle: datasets antigos (2015-2020; nov/23-jan/24). Não servem.
- CounterQuant Demos: demos .dem brutas do HLTV (Tier 1/2). Pesado e desnecessário.
- VRS oficial (GitHub da Valve): standings e pontos por data. Usar para seed e ranking.
- PandaScore: free tier sem histórico/stats; stats de jogador exigem plano Historical (pago).
- Liquipedia: API MediaWiki (1 req/2s; HTML automatizado proibido). Bom para rosters e resultados, sem stats por mapa/jogador.
- GRID Open Access: gratuito para devs independentes, inclui CS2 e download de histórico. Requer aplicação; prazo desconhecido.
- balldontlie CS2: API com chave; stats por mapa/jogador parecem restritas ao tier pago mais caro (verificar).
- hltv-crawler (PyPI): curl_cffi, cache, 2s entre requests, filtro de data, resume, SQLite. Auditar o código antes de rodar.

## Plano
1. VRS (GitHub oficial): rankings por data.
2. hltv-crawler (ou scraper próprio) para partidas/mapas/stats desde 2025-06-01; testar com --max-pages; rodar em background.
3. Liquipedia API para datas de mudança de roster (opcional).
4. Aplicar ao GRID Open Access em paralelo.
5. Selenium/undetected-chromedriver como fallback se curl_cffi for bloqueado.
6. Odds históricas (ex.: OddsPapi) como benchmark opcional do modelo.
