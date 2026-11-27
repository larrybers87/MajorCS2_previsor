# EMENDA 3 ao pré-registro do Stage 3 (reservas de Vitality e Legacy)

Escrita em 27/11/2026, antes de qualquer previsão do Stage 3 existir. O
[original](preregistro_stage3.md) e as emendas [1](preregistro_stage3_emenda_01.md) e
[2](preregistro_stage3_emenda_02.md) **não foram reescritos**. A seção 4 do original
deixava os substitutos como "não coberto".

## Já conhecido ao escrever
Resultados do Stage 1 e o desempenho de B0 e B1 nele
([adendo](adendo_preregistro_stage1.md)); previsão oficial do Stage 2. Nenhum resultado do
Stage 2 e **nenhuma previsão do Stage 3**.

## E3.1 Decisão (do Larry)
- **Modelo oficial do Stage 3: sem ajuste** pelos reservas. Segue a regra pré-registrada
  (combinação B0/B1 e checagem de desastre).
- **Sensibilidade reportada**, **com e sem desconto de rating**, definida **antes** de ver
  a previsão do Stage 3.
- A sensibilidade não é a previsão oficial, não entra na avaliação e não alimenta a
  checagem de desastre.

## Contexto (imprensa, sem confirmação da PGL; ver [substitutos.md](substitutos.md))

| Time | Sai (elenco no VRS) | Entra | Partidas no histórico do VRS com o núcleo (contagem nossa) |
|---|---|---|---|
| Vitality | jL | apEX | apEX: 112 de 119; jL: 13 |
| Legacy | n1ssim | ksloks | ksloks: nenhuma; n1ssim: 132 de 132 |

## E3.2 PENDENTE: o tamanho do desconto e como aplicá-lo
A decisão não fixa valores. **Precisam ser fixados em emenda antes de a previsão do
Stage 3 ser calculada**; sem isso, a sensibilidade não pode ser chamada de pré-definida.

**PROPOSTA (não adotada; aguarda o Larry):**
- Grade 3x3, como no anexo do Stage 2: Vitality e Legacy, separadamente, em {0, −50,
  −100} pontos VRS. **Valores arbitrários**, não estimados.
- O desconto entra só nas probabilidades de partida (suíça e playoffs); seeds inalterados.
- No B1, a escala é outra: aplicar o desconto que produz o mesmo deslocamento de
  log-odds do B0, `pontos do B1 = pontos VRS x beta0 / beta1` (cerca de −22 para −50 e
  −44 para −100, com os betas pré-registrados).
- Mesmo modelo, simulações e semente da oficial; a célula (0, 0) tem de reproduzi-la.
