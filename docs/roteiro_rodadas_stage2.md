# Roteiro: atualização por rodada do Stage 2

A previsão oficial não muda. Cada atualização é uma tabela separada (D28).

## Antes de começar
- Não enviar nada novo em `predictions/stage2/` antes das 04:00 UTC de 28/11.
- `data/manual/stage2_results.csv`, mesmo formato do Stage 1:
  `round,team_a,team_b,score_a,score_b,best_of` (rounds num Bo1, mapas num Bo3).

## A cada rodada encerrada (rodadas 1 a 4)
1. Acrescentar ao CSV os resultados da rodada.
2. Se a próxima rodada já foi anunciada, é possível listá-la também, inteira, com os
   placares vazios (`2,FUT,PVISION,,,1`). Necessário se o anúncio **diferir** da engine.
3. Gerar:
   ```
   conda activate majorcs2
   python -m sim.round_update
   ```
4. Ler `summary.md`: a seção V2 precisa dizer "Sem divergências"; se houver, anotar e
   **não ajustar a engine**. Conferir os confrontos de origem `engine` com o anúncio.
5. Commitar e enviar **antes do primeiro jogo da rodada** (o script mostra o comando; ele
   não faz commit sozinho). Antes do push: `git log --format='%an <%ae>'`.

Rodar durante uma rodada gera uma saída marcada como PARCIAL: os resultados já conhecidos
entram na simulação, mas não nos ratings do B1 (D33).

Depois da rodada 5, o mesmo comando grava `predictions/stage2/final/` com a classificação,
os ratings e os seeds do Stage 3.

## Quando o Larry cola os resultados na conversa
Os resultados entram no CSV, roda-se o passo 3, conferem-se os confrontos reais com a
engine e a pasta fica pronta em `predictions/stage2/round<N>/`. **Nada é commitado até ele
pedir.** Sem commit enviado antes do primeiro jogo da rodada, a saída não conta como
previsão anterior a ela.

## Depois do fim do Stage 2 (antes do Stage 3), nesta ordem
1. `python -m backtest.stage2_evaluation` → `docs/resultado_stage2.md` (emendas 1 a 3).
   Preencher os campos ⟨…⟩.
2. `python -m sim.stage3_check` → checagem de desastre, **uma única vez**. Commit e push
   do resultado e da decisão.
3. `python -m sim.predict_stage3` → previsão do Stage 3 (oficial e faixa da emenda 4),
   sem playoffs. Commit e push **antes do primeiro jogo**.

Os passos 2 e 3 precisam dos mesmos arquivos de entrada (conferido por hash).

## Conferência secundária (opcional)
Salvar o texto da Wikipedia uma vez em uma pasta nova de `data/raw/wikipedia/` e passar
`--wiki <arquivo>`. As diferenças são só listadas; vale o CSV.

## Site
- **Recomendado:** `python -m sim.site_server` e abrir `http://127.0.0.1:8000`. A página
  se recarrega sozinha (em cerca de 10 s) quando o CSV, as pastas de previsão ou o commit
  mudam, mantendo a visão escolhida. Tem o Simulador.
- **Arquivo local** (`app/index.html`, sem Simulador): `sim.round_update` já atualiza os
  dados no fim da execução; recarregar a página (F5). Para mostrar resultados **sem**
  gerar previsão (por exemplo, rodada pela metade): `python -m sim.export_site`.
- Se a exportação falhar, a atualização da rodada continua gravada e o script avisa.
- Um ensaio com `--stage2` ou `--out` próprios não mexe no site real (use `--site-dir`).

O que aparece: **Ao vivo**, resultados da última rodada ao lado dos confrontos pendentes
com probabilidades; **Previsor**, acerto da rodada, tabela rodada a rodada e acumulado
(parcial, não é a avaliação oficial); **Simulador**, resultados reais fixos.
