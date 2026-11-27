# EMENDA 4 ao pré-registro do Stage 3 (sensibilidade aos reservas: grade 3x3)

Escrita em 27/11/2026, antes do primeiro jogo do Stage 2 e **antes de qualquer previsão do
Stage 3 ser calculada** (não existe `predictions/stage3/`). O original e as emendas
[1](preregistro_stage3_emenda_01.md), [2](preregistro_stage3_emenda_02.md) e
[3](preregistro_stage3_emenda_03.md) **não foram reescritos**. Esta emenda fixa o que a
seção E3.2 da emenda 3 deixou pendente e **substitui a proposta** que estava lá.

## E4.1 Modelo oficial
**O modelo oficial do Stage 3 NÃO tem desconto algum.** Segue a regra pré-registrada
(combinação B0/B1 e checagem de desastre), sem reponderar.

## E4.2 Grade da sensibilidade (decidida pelo Larry)

**Vitality** em {0, −25, −50} e **Legacy** em {0, −50, −100} **pontos VRS**,
separadamente: 9 cenários. **Os valores são arbitrários:** não foram estimados de dado
algum e não medem o efeito real de uma troca de jogador.

No B1, o desconto equivalente é o que produz o mesmo deslocamento de log-odds do B0:
`desconto no B1 (w) = desconto VRS x beta0(w) / beta1(w)`, com os betas pré-registrados.

| Desconto VRS (B0) | B1, w=0 | B1, w=1 | Aproximado |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| −25 | −11,11 | −11,09 | −11 |
| −50 | −22,22 | −22,19 | −22 |
| −100 | −44,45 | −44,38 | −44 |

Vitality usa as linhas 0, −25 e −50; Legacy, 0, −50 e −100. O cálculo usa a fórmula, não
o valor arredondado.

## E4.3 O que se publica
No relatório e na pasta da previsão: **só o resultado oficial e, para cada time, a faixa
mínima-máxima de P(avançar)** nos 9 cenários. Os cenários individuais **não** são
publicados.

## E4.4 Fatos registrados
- **A troca de titular não foi confirmada pela PGL** (Vitality: apEX no lugar de jL;
  Legacy: ksloks no lugar de n1ssim). A informação é de imprensa
  ([substitutos.md](substitutos.md)).
- **O histórico de ksloks na Legacy é nulo:** nenhuma partida com o time no histórico do
  VRS usado (n1ssim: 132 de 132 partidas do núcleo).
- Para a Vitality, apEX está em 112 das 119 partidas do núcleo nesse histórico; jL, em 13.

## E4.5 Definições operacionais
- O desconto entra **só nos ratings usados nas probabilidades de partida** da previsão: nos
  pontos VRS do B0 e no rating do B1 já atualizado até o momento da previsão. O histórico,
  as atualizações do B1 e os **seeds** não mudam.
- Cada cenário usa o mesmo modelo, número de simulações e semente da oficial; o cenário
  sem desconto tem de reproduzi-la.
- Se a checagem de desastre mandar usar o B0 puro, só os descontos do B0 se aplicam.
- A sensibilidade não é a previsão oficial, não entra na avaliação nem na checagem de
  desastre.
