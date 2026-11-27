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

## Conferência secundária (opcional)
Salvar o texto da Wikipedia uma vez em uma pasta nova de `data/raw/wikipedia/` e passar
`--wiki <arquivo>`. As diferenças são só listadas; vale o CSV.

## Site
`python -m sim.site_server` e abrir `http://127.0.0.1:8000` (os dados são refeitos a cada
recarga). Sem o servidor, `python -m sim.export_site` e abrir `app/index.html` (sem o
Simulador).
