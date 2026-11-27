# Registro de integridade: previsão oficial do Stage 2

Registrado em 27/11/2026, antes do primeiro jogo do Stage 2 (28/11 04:00 UTC).

## Identificação

| Item | Valor |
|---|---|
| Pasta | `predictions/stage2/20261127T161221Z` |
| Commit | `7f8835fd9ae3f99fe68717916329b6525ebb25e1` |
| Data do commit | 2026-11-27T13:13:30-03:00 (16:13:30 UTC; relógio local) |
| **Push (GitHub)** | **2026-11-27T16:13:36Z** (`d39cd1a` → `7f8835f`, `refs/heads/main`, atividade 52141261836) |
| Prazo | 2026-11-28T04:00:00Z |
| Tag | `stage2-oficial` (anotada; objeto `f122d520d21c88f26c2acc0232aceba4723ee2b0`), enviada ao GitHub |

O horário do push vem da API de atividade do repositório no GitHub
(`gh api repos/<dono>/<repo>/activity`), consultada em 27/11. É o horário que não depende
do relógio do computador.

**Tag enviada** em 27/11, por volta das 16:54 UTC, a pedido do Larry (exceção à regra de
enviar só `main`, válida para essa tag). Antes do envio foi conferido que `origin/main`
contém o commit. `git ls-remote origin` mostra a tag apontando para `7f8835f`.

## Arquivos (como estão no commit, com LF)

| Arquivo | SHA-256 | Blob git |
|---|---|---|
| `meta.json` | `d94fceb72d15bfdab4912148a5b443d71fc34e5f4138ec8f5716fb2d4c30668b` | `d1f204ef9d23` |
| `model_params.json` | `c2051462994d7ceb0f490e1a183c1f98557cff23c74327109c838b2ebfd6e03a` | `8f54d77e5fe6` |
| `opening_round.csv` | `a2c554de5f11920c40e1b4527b351b304008b65f4afdf7a2f77c64e7decd3fa4` | `be93d52536dd` |
| `probabilities.csv` | `1d3359e0867525ed116442084993fc8c5fc3d973ce6f2e6b24ace46df783da10` | `ad3b2369c51c` |
| `summary.md` | `fcc403e3bde0e59cb0f672de45dabf3889d1d3fe99837e542a30b7ac8d71cdc9` | `578e4f12a671` |

## Conferências automáticas (`tests/test_stage2_official.py`)
- A cópia local é igual à do commit.
- Commit anterior ao prazo.
- Soma de P(avançar) = 8,0 (média, w=0 e w=1).
- Número esperado de times por cartel = 2, 3, 3, 3, 3, 2.
- As 8 partidas da rodada 1 têm probabilidade commitada, coerente com os parâmetros e
  pontos VRS publicados.

## Cuidado (D28)
Vale a pasta mais recente de `predictions/stage2/` contida no último push **anterior ao
prazo**. Qualquer pasta nova ali, enviada antes das 04:00 UTC de 28/11, passaria a ser a
oficial. As atualizações por rodada vão para `predictions/stage2/round<N>/` e só existem a
partir da rodada 2.
