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

## 26/11/2026 (sessão 03)

1. **Push autorizado** com o autor e o e-mail atuais (o Larry decidiu que o e-mail é
   público). Substitui a parte "parar e perguntar" da decisão 5 para esse e-mail.
2. **Reescrita autorizada, só para os arquivos da Valve:** o repositório deles não tem
   licença, então as cópias saíram de todo o histórico local antes do primeiro push
   ([fontes_valve.md](fontes_valve.md)). Autor, e-mail, datas e mensagens não mudaram. O
   "sem reescrita" dizia respeito ao autor. Push **somente de `main`**
   (nunca `--all`, `--tags` ou `--mirror`).
3. **D15 fechada:** THE ONE = 1win e GOSH = BC.Game (confirmado pelo Larry com base na
   PGL e na imprensa). O mapeamento é feito pelo **elenco**, não pelo nome: o "the ONE"
   #318 do VRS é outro time.
4. **`LIQUIPEDIA_CONTACT`** = `git config user.email` do repositório, lido em tempo de
   execução (nunca gravado). Antes de usar a API, ler os termos oficiais; se não abrirem,
   parar essa parte.
5. **Calendário:** rodada 5 do Stage 1 na sexta 27/11 (Lynn Vision x HEROIC, Imperial x
   Wildcard, M80 x 100 Thieves, Bo3); rodada 1 do Stage 2 no sábado 28/11 (horário não
   confirmado). A previsão do Stage 2 precisa estar commitada e **enviada ao GitHub**
   antes do primeiro jogo.
6. A previsão antecipada já commitada não é alterada.

### Mapa de hashes da reescrita (antigo → novo)

Relatórios da sessão 02 e o `meta.json` da previsão antecipada citam os hashes antigos.

| Antigo | Novo | Commit |
|---|---|---|
| `539b76b` | `0038d6d` | Fundação do projeto |
| `c26a37d` | `3b28241` | Engine suíça, simulador e testes |
| `7136693` | `3623009` | Regras da fase suíça |
| `ea0a88a` | `65354b8` | Spike do scraper |
| `5f4bfd1` | `8a04c05` | Relatório da sessão 01 |
| `66a5006` | `9b94e77` | Remove o spike do HLTV |
| `02703c4` | `0d19644` | Engine: Bo5 e identidades por simulação |
| `5789a60` | `fc4347b` | Ingestão do VRS |
| `fd011ac` | `9cb7abe` | Modelo B0 |
| `6bc9e0e` | `4e01e62` | Scripts do V3 e do Stage 2 |
| `fa2f72b` | `3753fae` | Decisões da sessão 02 |
| `488ce27` | `c029136` | Correções de vazamento |
| `b8b0c4e` | `4fc920a` | Documentação (commit do código no `meta.json` da previsão) |
| `c49c1b6` | `3ed704f` | **Previsão antecipada do Stage 2** |
| `e0d3820` | `4698032` | Relatório da sessão 02 |

A previsão antecipada não mudou (mesmos blobs git). SHA-256, nas duas formas:

| Arquivo | Arquivo local (CRLF; valor do relatório 02) | Como o GitHub serve (LF) |
|---|---|---|
| `probabilities.csv` | `8403a87e0039b58116ae5b68ab131be77c5f0297388e5c1200ad05ceb2e8cfb2` | `7bcb258bddaa5fd4c5c38b137c62bac3a90f5603918c1bae8b7ad13c1a4fd3d9` |
| `opening_round.csv` | `49e97592d40c623f6a9085f59e22cf32b066d8049c0f15cb4696753990beca4c` | `c52812841cc0b04d653a8ee0114492c2114e3ae7036efffc177946b718752b5e` |

## 26/11/2026, 21:30 BRT (sessão de planejamento, registrada na sessão 04)

- **D17 (fechada):** primeiro jogo do Stage 2 no **sábado 28/11 às 01:00 BRT (04:00
  UTC)**. Os horários da HLTV estão em Brasília (conferido pelo Larry com o Stage 1: 05:00
  CET = 01:00 BRT). **Prazo do push oficial: antes de 04:00 UTC de 28/11.** O calendário do
  Stage 2 confirma Bo1 nas rodadas 1-2; na rodada 3, Bo1 nos jogos 1-4 e Bo3 nos jogos
  5-8; Bo3 nas rodadas 4-5. (Compatível com a engine: 4 Bo1 e 4 Bo3 na rodada 3.)
- **D28:** vale como oficial a **última previsão enviada** (push com horário da API do
  GitHub) antes do primeiro jogo do Stage 2. Métricas primárias: **log loss por partida**
  (Brier secundária) e **log score da distribuição do cartel final**, com IC por bootstrap
  de simulações (os 16 times são dependentes). Referências: 50% e maior VRS fixo.
  Atualizações ao vivo ficam em tabela separada. Definições operacionais:
  [avaliacao_stage2.md](avaliacao_stage2.md).
- **D25:** B0 **sem ajuste** na manchete. Anexo de sensibilidade, pré-registrado antes do
  jogo, com redução de 0, -50 e -100 pontos VRS para FUT e Astralis (**valores
  arbitrários**): [anexo_d25_protocolo.md](anexo_d25_protocolo.md). Vitality e Legacy só
  no Stage 3.
- **D27:** "ponto médio" = **média das probabilidades** de w=0 e w=1. Só os dois extremos,
  sem grade.
- **D24 (atualizada na mesma noite; substitui "pedir LiquipediaDB e GRID em
  paralelo"):** **GRID descartado** (o site só oferece contato com vendas, sem cadastro).
  **LiquipediaDB opcional**, não bloqueia nada: se o Larry pedir a chave pelo formulário
  de contato, ele avisa; até lá, **nenhuma coleta além do VRS e dos resultados do
  Major**. Estatísticas por jogador e por mapa ficam **fora do escopo** até haver fonte
  permitida: [fontes_dados.md](fontes_dados.md).
- **D26:** no Stage 3 o modelo principal é a **média 50/50 de B0 e B1**, com checagem de
  desastre; o teste já visto não pode ser usado como argumento. Pré-registro (commit antes
  de 02/12): [preregistro_stage3.md](preregistro_stage3.md).

## 26/11/2026, 21:45 BRT (respostas da sessão de planejamento)

- **D30 (corrigida):** o limiar 0,70 foi erro do planejamento. Voltar ao B0 puro só se a
  média 50/50 for pior que o 50% com significância unilateral de 95% (bootstrap por
  partidas) **e** o B1 sozinho for pior que o B0; se só a primeira valer, relatar falha
  dos dois sem trocar nada. [Emenda 1 do Stage 3](preregistro_stage3_emenda_01.md).
- **D29:** aprovada; 59,5% conferido (só dados pré-evento); comparação com as referências
  por bootstrap pareado por partidas; o intervalo por simulações é teste de consistência.
  [Emenda 1 da avaliação](avaliacao_stage2_emenda_01.md).
- **D31:** confirmada: peso 1/4 por (B0, B1) x (w=0, w=1); hiperparâmetros e código do B1
  congelados; ratings em walk-forward até a véspera de cada rodada.
- **D32:** grade 3x3 no anexo, reexecutada na sexta.
  [Emenda 1 do anexo](anexo_d25_emenda_01.md).
- **Horários da rodada 5 do Stage 1:** sexta 27/11 às **03:00, 05:30 e 08:00 BRT**.

## Anteriores
- Escopo temporal: a partir de 2025-06-01 (`claude/fontes-de-dados.md`).
- Dashboard local por enquanto.
- Um modelo só substitui o anterior se vencer em log loss no backtest; senão fica o B1.
  Calibração obrigatória. Rede neural fora do escopo inicial (`claude/design-v0.md`).
