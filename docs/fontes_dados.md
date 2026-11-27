# Fontes de dados: estado atual (26/11/2026)

Prevalece sobre `claude/fontes-de-dados.md` (histórico da pesquisa inicial). Decisões em
[decisoes.md](decisoes.md).

## Em uso

| Fonte | O que traz | Onde |
|---|---|---|
| VRS oficial da Valve (clone fora do projeto, commit fixado) | pontos e elencos por data; partidas com data, vitória/derrota e elenco | [fonte_vrs.md](fonte_vrs.md) |
| Resultados do Major, digitados pelo Larry | rodada, times, placar, formato | `data/manual/` (fora do git) |

**Até nova decisão, nenhuma coleta além dessas duas.** Consultas pontuais à imprensa para
contexto (formato, substitutos) são registradas com a fonte e não alimentam o modelo.

## Fora

| Fonte | Situação |
|---|---|
| **GRID Open Access** | **descartado** por decisão do Larry (26/11): o site só oferece contato com vendas, sem cadastro |
| **LiquipediaDB** | **opcional, não bloqueia nada.** Se o Larry pedir a chave pelo formulário de contato, ele avisa; até lá, não usar |
| Liquipedia, API MediaWiki | os termos dizem que não é suportada para fins que não sejam edição ([h10_formato.md](h10_formato.md)); não usar |
| Liquipedia, páginas HTML | acesso automatizado proibido pelos termos |
| HLTV | acesso automatizado e contorno de anti-bot proibidos por decisão |

## Fora do escopo enquanto não houver fonte permitida
- **Estatísticas por jogador** (kills, mortes, ADR, KAST, rating).
- **Estatísticas por mapa** (resultado e rounds por mapa, picks e bans).

Consequências sobre o desenho (`claude/design-v0.md`):
- O M1 como descrito (força por mapa e dos cinco jogadores) e o M2 com essas variáveis
  **não podem ser construídos**.
- Não há modelo de veto: Bo3 e Bo5 usam mapas independentes com a mesma probabilidade.
- Substitutos não podem ser ajustados por força individual (ver D25).
- O formato das partidas históricas (H10) continua desconhecido.
