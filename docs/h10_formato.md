# H10: rotulagem de formato pela Liquipedia (tarefa D) — NÃO executada

**Estado em 26/11/2026: bloqueada pelos termos. Nenhuma requisição à API foi feita.** A
estimativa estatística de `w` (tarefa C) está em
[h10_verossimilhanca.md](h10_verossimilhanca.md).

## O que os termos dizem

Fonte: <https://liquipedia.net/api-terms-of-use>, aberta uma vez em 26/11/2026 (HTTP 200,
sem data de atualização visível). Trechos curtos, em inglês:

| Assunto | Trecho |
|---|---|
| API MediaWiki para ler dados | "Use of the API for non-editing purposes is not supported" |
| Alternativa indicada | "please see our data API if you are interested in using data from Liquipedia for other purposes" |
| HTML | "Automated access to non-API endpoints (i.e., generated HTML pages) is not permitted." |
| Limite | "Rate limit all HTTP requests to no more than 1 request per 2 seconds." |
| `action=parse` | não mais que 1 requisição a cada 30 segundos |
| Identificação | User-Agent próprio, com contato; clientes genéricos tendem a ser bloqueados |
| Licença | "Liquipedia content is licensed under CC-BY-SA 3.0", com atribuição obrigatória |
| LiquipediaDB (data API) | acesso mediante pedido aprovado; chaves não compartilháveis |

## Decisão

A tarefa D só deveria rodar "se os termos permitirem". Nosso uso (coletar o best-of de
partidas) não é edição, e o texto diz que esse uso da API MediaWiki **não é suportado** e
encaminha para a LiquipediaDB. Não lemos isso como permissão; ler como proibição ou como
"sem suporte, por sua conta" é uma decisão do Larry (D24).

Isso também afeta a decisão 1 da sessão 02, que lista a API MediaWiki como fonte
permitida, e `claude/fontes-de-dados.md` ("Liquipedia: API MediaWiki (1 req/2s...)").

`LIQUIPEDIA_CONTACT` não foi usado.

## Caminhos

1. Pedir acesso à **LiquipediaDB API** (aprovação necessária; prazo desconhecido).
2. Usar o **GRID Open Access** quando aprovado (formato e mapas por série: a confirmar).
3. Digitar à mão o formato de uma amostra pequena (sem automação).
