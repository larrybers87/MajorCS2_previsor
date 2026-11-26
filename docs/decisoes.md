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

## Anteriores
- Escopo temporal: a partir de 2025-06-01 (`claude/fontes-de-dados.md`).
- Dashboard local por enquanto.
- Um modelo só substitui o anterior se vencer em log loss no backtest; senão fica o B1.
  Calibração obrigatória. Rede neural fora do escopo inicial (`claude/design-v0.md`).
