# Documentos da Valve (não versionados)

O repositório <https://github.com/ValveSoftware/counter-strike_rules_and_regs> **não tem
licença** (conferido em 26/11/2026 pela API do GitHub: `license: null`, sem arquivo de
licença na raiz). Sem permissão para redistribuir, as cópias ficam só no disco, em
`docs/`, ignoradas pelo git, e foram removidas de todo o histórico antes do primeiro push.

Versão usada: commit `621b7d91b0a236044aed62a357fddc863dfaea49` (HEAD de `main` em
26/11/2026). As cópias locais são idênticas byte a byte a essa versão.

| Arquivo em `docs/` | Último commit do arquivo | Data (UTC) | SHA-256 |
|---|---|---|---|
| `major-supplemental-rulebook.md` | `745a40758ed7877483d5544605cda6c6e1a1cd65` | 2026-10-06 | `5ba14b7b62e74ea0909ca452c5882d09cb334e61af87e97597721d773a06b21d` |
| `tournament-operation-requirements.md` | `8594dc0cc8f8cd9ea9564af46e453fc673246cbd` | 2025-12-08 | `78232030bf475a9261feedf57a99e5af374f2d46cf0dcc1a7ca0032c7cefc5d4` |
| `tournament-operation-requirements-exceptions.md` | `621b7d91b0a236044aed62a357fddc863dfaea49` | 2026-10-07 | `8ed4d2b35ed61f192ec47092455f4fd331079a77113d1c58e14738027f8f9030` |
| `tournament-item-submission-guidelines.md` | `2bf7a6ca4268941d9a07edd7098beeaa245e93d0` | 2024-01-23 | `830ffc6f90bf7497a2e34e01315e89377dfc63a25c5482654bc80406d6e95d30` |
| `Declaration of Conflicts of Interest.pdf` | `eb7fa3a39a4d799915cdf128c7cdecbf5e81e604` | 2025-10-21 | `a39e02bad84f804dab1e62956e5001f3b8de614455d88d39336ab1685f29a5e6` |
| `.gitignore` (veio do mesmo repositório) | `af10cc848134543ba8f4e1693e10ee296f81f7fe` | 2024-07-16 | `b2187030f308ae401e5aea5789af9eb447cd24fe98c19fcbc045bd8404776b84` |

## Como baixar

Na raiz do projeto:

```
BASE=https://raw.githubusercontent.com/ValveSoftware/counter-strike_rules_and_regs/621b7d91b0a236044aed62a357fddc863dfaea49
for f in major-supplemental-rulebook.md tournament-operation-requirements.md \
         tournament-operation-requirements-exceptions.md tournament-item-submission-guidelines.md \
         "Declaration of Conflicts of Interest.pdf" .gitignore; do
  curl -sS -o "docs/$f" "$BASE/${f// /%20}"
done
sha256sum docs/major-supplemental-rulebook.md   # comparar com a tabela
```

As citações com número de linha em [regras_suica.md](regras_suica.md) referem-se a essas
versões.

## VRS

<https://github.com/ValveSoftware/counter-strike_regional_standings> também **não tem
licença**. Nenhum arquivo bruto dele está versionado: o clone fica fora do projeto (ver
[fonte_vrs.md](fonte_vrs.md)) e as tabelas derivadas ficam em `data/processed/`
(ignorada). O que há de derivado no repositório: pontos VRS dos times do Major numa coluna
das previsões, valores citados em documentos e nomes de times no código.
