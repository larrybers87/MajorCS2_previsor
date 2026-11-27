# Roteiro de sexta 27/11: previsão oficial do Stage 2

**Prazo:** push antes de **sábado 28/11, 01:00 BRT (04:00 UTC)**.
**Meta:** enviar até **sexta 18:00 BRT**. **Limite prático:** 23:00 BRT.

Ensaiado em 26/11 com um desfecho fictício da rodada 5: V2, previsão, anexo, V3,
conferência do `git push` (`--dry-run`) e a variante com a rodada 1 anunciada rodaram em
**88 s** no total. Os 8 desfechos possíveis da rodada 5 foram ensaiados na sessão 03
(previsão e V3). O tempo que importa é o seu: preencher o CSV e conferir, uns 10 a 15
minutos (estimativa).

## Antes
```
conda activate majorcs2
cd C:\Users\Usuário\Pessoal\MajorCS2_previsor
git status            # deve estar limpo
```

## Passos
1. Preencher os três placares da rodada 5 em `data/manual/stage1_results.csv` (mapas:
   2-0, 2-1, 1-2 ou 0-2).
2. V2: `pytest tests/test_v2_real.py`. Se falhar, **não ajuste nada**: anote a divergência
   e siga (a previsão usa os confrontos do CSV como fatos).
3. Previsão:
   `predict_stage2 --stage1 data/manual/stage1_results.csv`
   Anote a pasta mostrada em "Gravado em" (`<PASTA>`). Se aparecer "Atenção:
   divergências", leia antes de continuar.
4. Anexo: `python -m sim.anexo_d25 --stage1 data/manual/stage1_results.csv --official <PASTA>`
5. V3: `python -m sim.v3_stage1`
6. **Rodada 1 oficial do Stage 2:** comparar com `<PASTA>/opening_round.csv`.
   Se for diferente, criar `data/manual/stage2_results.csv` com o cabeçalho
   `round,team_a,team_b,score_a,score_b,best_of` e as 8 partidas com placares vazios
   (`1,FUT,Adversário,,,1`), e repetir os passos 3 e 4 acrescentando
   `--stage2 data/manual/stage2_results.csv`. Vale a pasta nova.
7. Enviar (adicione só as pastas desta execução):
```
git add predictions/stage2/<PASTA> predictions/anexo_d25/<PASTA_ANEXO> predictions/v3_stage1/<PASTA_V3>
git commit -m "Previsão do Stage 2 com o Stage 1 completo"
git log --format='%an <%ae>' | sort | uniq -c
git push origin main
```
8. Confirmar o horário (tem de ser anterior a `2026-11-28T04:00:00Z`):
```
gh api repos/larrybers87/MajorCS2_previsor/activity --jq ".[0].timestamp"
```

## Cuidados
- **A última pasta de `predictions/stage2/` enviada antes do prazo é a oficial** (D28).
  Não envie pasta de teste ali.
- **Se algo falhar ou a rodada 5 não terminar:** a previsão condicionada já enviada
  (`predictions/stage2/20261127T001433Z`, 30 partidas) é a oficial enquanto nenhuma outra
  for enviada. Para incluir resultados parciais da rodada 5:
  `predict_stage2 --conditioned` (liste a rodada inteira, pendentes com placar vazio).
- Depois do primeiro jogo, execuções com resultados do Stage 2 são **atualizações ao
  vivo**: tabela separada, não substituem a oficial.
