# Substitutos no PGL Major Singapore 2026 (consulta em 26/11/2026)

O modelo **não foi alterado** por causa desta lista. A manchete do Stage 2 é o B0 sem
ajuste; a sensibilidade para FUT e Astralis está no anexo
[anexo_d25_protocolo.md](anexo_d25_protocolo.md), emendado para uma grade 3x3
([emenda 1](anexo_d25_emenda_01.md)). Vitality e Legacy: só no Stage 3.

## FUT e Astralis: o mesmo jogador está no centro dos dois casos

"Sai / entra" na tabela abaixo é em relação ao elenco **registrado** (o do VRS). Pela
[Strafe (08/11)](https://www.strafe.com/news/read/astralis-announce-cmtrys-replacement-for-singapore-major-2026/)
e pela [Strafe (28/10)](https://www.strafe.com/news/read/astralis-bring-back-jabbi-to-avoid-singapore-major-roster-conflict/):

- **cmtry** foi contratado pela Astralis em outubro, mas **segue no elenco VRS da FUT**,
  porque o novo jogador da FUT, SunPayus, não tinha as 5 partidas em 10 necessárias.
- Por isso a **FUT** usa **SunPayus** como substituto registrado. Em campo, ele é quem
  substituiu cmtry no time desde outubro, e não um reserva chamado de última hora
  (**leitura nossa** das fontes e do histórico).
- A **Astralis** não pode inscrever cmtry; no elenco VRS dela está **jabbi**, que, segundo
  fontes citadas pela Strafe, não deve jogar. Entra **Anlelele**, emprestado pela Sashi.
  A Strafe diz que Anlelele substitui **cmtry**; a gambling.com e a lista registrada dizem
  **jabbi**. As duas descrições se referem a coisas diferentes (time real x registro).
- Cinco esperados na Astralis (Strafe, 08/11): phzy, Staehr, ryu, siuhy, Anlelele.

Histórico do VRS desde 01/09 (contagem nossa): cmtry, 4 partidas pela Astralis (14/10 a
27/10); SunPayus, 4 pela FUT (24/10 a 29/10), as 4 últimas do núcleo; jabbi, 16 pela
Astralis, incluindo as 3 últimas (28 e 29/10); Anlelele, só pela Sashi.

**Consequência para o anexo D25:** "reduzir pontos porque joga um substituto" tem sentido
mais claro para a Astralis (jogador emprestado, sem partidas com o time) do que para a FUT
(escalação que já vinha jogando). O modelo não foi alterado.

## Quem começa com o substituto registrado

| Time | Stage | Sai (está no elenco do VRS) | Entra | Partidas no histórico do VRS (2025-06 a 2026-11-01) |
|---|---|---|---|---|
| **FUT** | 2 | cmtry | SunPayus | SunPayus jogou 4 com este núcleo (última 29/10); cmtry, 123 (última 31/08) |
| **Astralis** | 2 | jabbi | Anlelele | Anlelele: nenhuma com a Astralis; jabbi, 70 de 74 |
| Vitality | 3 | jL | apEX | apEX: **112** das 119 do núcleo (última 11/10); jL: 13 (última 31/10) |
| Legacy | 3 | n1ssim | ksloks | ksloks: nenhuma com a Legacy; n1ssim, 132 de 132 |
| 9z | 1 (eliminada) | meyern | history | history: nenhuma com a 9z; meyern, 97 de 97 |

"Núcleo" = partidas com pelo menos 3 dos 5 jogadores do elenco usado no VRS. A contagem é
nossa, sobre `data/processed/matches.parquet`.

## Relevância para o Stage 2
- **FUT** é o favorito entre os convidados nas nossas previsões e joga com um substituto
  que tem 4 partidas registradas com o time. Os pontos VRS usados pelo B0 foram obtidos em
  grande parte com cmtry em campo.
- **Astralis** joga com um substituto sem partidas pelo time.
- **Vitality** (Stage 3): o caso é diferente; a maior parte do histórico é com apEX.

## Regra (rulebook da Valve, "Substitutions", L543-550)
> "Each team can substitute a player with their registered substitute once during the
> event."

A equipe pode seguir com o substituto até decidir voltar ao elenco principal; depois da
volta não pode substituir de novo. Logo, **a escalação pode mudar durante o Major**.

## Fontes e confiança

**Estado:** citado por duas fontes que reproduzem a lista oficial da PGL (gambling.com e
pley.gg, 9/11); a página da PGL continua sem verificação direta.

### Links citados no planejamento (abertos em 26/11)
| Link | Resultado |
|---|---|
| [gambling.com: PGL confirms rosters](https://www.gambling.com/news/pgl-confirms-rosters-for-all-32-teams-at-the-singapore-major) (09/11) | **abriu**; cita e linka a lista da PGL |
| [pley.gg, p=65983](https://pley.gg/?p=65983) | **não abriu (403)**; conteúdo não verificado por mim |
| [rg.org: nomes e elencos](https://rg.org/news/esports/pgl-singapore-major-official-name-changes-gosh-the-one-bb-team-pvision-rosters) | **não abriu (403)** |
| [rg.org: registro de Anlelele](https://rg.org/news/esports/astralis-anlelele-singapore-major-substitute-cmtry-vrs-report) | **não abriu (403)** |
| [rg.org: cmtry fora](https://rg.org/news/esports/cmtry-miss-singapore-major-astralis-fut-nemiga-sunpayus-coolio) | **não abriu (403)** |
| [Strafe: substituto de cmtry](https://www.strafe.com/news/read/astralis-announce-cmtrys-replacement-for-singapore-major-2026/) (08/11) | **abriu** |
| [Strafe: volta de jabbi](https://www.strafe.com/news/read/astralis-bring-back-jabbi-to-avoid-singapore-major-roster-conflict/) (28/10) | **abriu** |

Não se sabe qual das três páginas da rg.org foi a citada. Não houve nova tentativa nas que
recusaram.

### Divergências entre as fontes
- **Quantas trocas:** gambling.com fala em **quatro** (Legacy, Vitality, Astralis, FUT) e
  a frase sobre a 9z está truncada, com meyern listado e history como substituto. Shane
  the Gamer, Wikipedia e SkinsMonkey falam em **cinco**, incluindo history por meyern na
  9z (já eliminada).
- **Quem Anlelele substitui:** jabbi (gambling.com) x cmtry (Strafe); ver acima.
- **Partidas de SunPayus:** três (Strafe 28/10, até aquela data) e quatro (Strafe 08/11);
  o VRS mostra quatro.
- **Data:** a gambling.com diz em um trecho que o Major é "scheduled for November 9", o que
  contradiz o próprio início em 24/11.

### Também consultadas na sessão 03
- [Shane the Gamer](https://www.shanethegamer.com/news/pgl-major-singapore-2026-rosters-substitutes/)
  (09/11, atualizada 10/11): cinco times começam com o substituto; só dá o motivo para a
  Vitality (jL conta como titular no registro; apEX é o reserva que comanda).
- [Wikipedia](https://en.wikipedia.org/wiki/PGL_Major_Singapore_2026): "(replaced X)" nos
  mesmos cinco.
- [SkinsMonkey](https://skinsmonkey.com/blog/pgl-major-singapore-2026/) (25/11): idem.

**Sem verificação direta:** o anúncio da PGL
(<https://news.pglesports.com/news/1794219566606-pgl-major-singapore-2026-team-rosters>)
não trouxe conteúdo quando aberto (só "PGL News"). Não confirmamos se alguma troca foi
revertida, nem a escalação que de fato jogou. HLTV e páginas da Liquipedia não foram
acessados.

## Registrados como substitutos, mas sem começar
Segundo as mesmas fontes, cada um dos 32 times registrou um substituto: em 14 é o técnico;
os demais jogadores reservas (PVISION slaxejezzz, FaZe GruBy, Eternal Fire Hydro2K, M80
Munstur, DENDELE D10S, GOSH BnTeT, G2 tAk, THE ONE xeedo, Natus Vincere FAZERY, MOUZ
Nikodeon, Spirit S0tF1k, BB Team dmrr, Falcons NucleonZ) não foram anunciados como
titulares. Grafias divergem entre fontes (ex.: Munstur/M0nstr).
