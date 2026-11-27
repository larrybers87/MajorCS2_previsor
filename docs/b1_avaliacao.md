# B1 (Elo/Glicko) contra o B0

Gerado por `python -m backtest.b1_selection` (não editar à mão). Protocolo em [protocolo_sessao_03.md](protocolo_sessao_03.md).

Histórico: 16225 partidas até 2026-11-01.

## Desenvolvimento (2877 partidas, 172 configurações)

B0 (top100/points): log loss 0.6664. Dez melhores do B1:

| Configuração | log loss |
|---|---:|
| elo s=0.5 K=20 H=sem m=2 | 0.6563 |
| elo s=0.5 K=20 H=180 m=2 | 0.6564 |
| elo s=0.5 K=20 H=180 m=1 | 0.6566 |
| elo s=0.25 K=10 H=180 m=2 | 0.6569 |
| elo s=0.75 K=30 H=180 m=2 | 0.6569 |
| elo s=0.5 K=20 H=sem m=1 | 0.6570 |
| elo s=0.75 K=30 H=sem m=2 | 0.6570 |
| elo s=0.5 K=20 H=90 m=2 | 0.6571 |
| elo s=0.75 K=30 H=180 m=1 | 0.6571 |
| elo s=0.5 K=20 H=90 m=1 | 0.6573 |

Escolhido: **elo s=0.5 K=20 H=sem m=2**.

## Teste (1479 partidas, 2026-06-01 a 2026-11-01)

| Modelo | log loss | IC 95% | Brier | IC 95% |
|---|---:|---|---:|---|
| B0 | 0.6601 | [0.6478; 0.6733] | 0.2337 | [0.2280; 0.2395] |
| B1 | 0.6571 | [0.6435; 0.6709] | 0.2320 | [0.2257; 0.2383] |

**B1 - B0, log loss: -0.0029 [-0.0115; 0.0057]** (NÃO inteiramente abaixo de zero). Brier: -0.0016 [-0.0056; 0.0024].

## Calibração do favorito no teste (B1)

| Faixa | n | previsto | observado | IC 95% (Wilson) |
|---|---:|---:|---:|---|
| 50%-60% | 925 | 54.7% | 56.9% | [53.7%; 60.0%] |
| 60%-70% | 397 | 63.9% | 68.5% | [63.8%; 72.9%] |
| 70%-80% | 124 | 73.8% | 75.8% | [67.6%; 82.5%] |
| 80%-90% | 29 | 83.6% | 72.4% | [54.3%; 85.3%] |
| 90%-100% | 4 | 91.8% | 50.0% | [15.0%; 85.0%] |
| >= 80% | 33 | 84.6% | 69.7% | [52.7%; 82.6%] |

A decisão de adoção também exige revisão do `leakage-reviewer` até 27/11 18:00 BRT; ver o relatório da sessão.
