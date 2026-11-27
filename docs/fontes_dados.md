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

**27/11 (sessão 05):** a rodada 5 do Stage 1 foi completada a partir do texto bruto da
Wikipedia (CC BY-SA; cópia em `data/raw/wikipedia/`), a pedido de fechamento do Stage 1.
Os vencedores foram informados pelo Larry; da Wikipedia vieram só os placares, que não
alimentam o modelo. **Confirmado pelo Larry** (D37). Daqui em diante os resultados vêm do
CSV dele; a Wikipedia serve só de conferência secundária (`sim.wiki_check`, arquivo salvo
à mão; nada é baixado por script).

**27/11 (sessão 06):** a pedido, nova tentativa na página oficial da PGL sobre formato e
horário (cópias em `data/raw/pgl/`), sem conteúdo legível; a consulta ao serviço de dados
do site foi bloqueada pela permissão da sessão e não foi repetida.

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
