# Família estruturada: *Atlas de Arton* (3º livro de expansão)

> **Status: EM CURSO.** `fonte="atlas-arton"` (registrado em [`fontes.py`](../../fontes.py)).
> Livro grande (484 págs), majoritariamente **lore/geografia** + um apêndice mecânico.
> Layout = Heróis/núcleo (corpo IowanOldStyle, nomes Tormenta20, caixas SourceSansPro).

## Estrutura do livro (TOC nativo, 70 entradas)

- **Introdução** (12–45): Uma Breve História de Arton, Tempo & Calendário, Linha do Tempo.
- **Cap. 1: O Reinado** (46–171): 10 regiões-núcleo (Deheon, Valkaria, Bielefeld, Namalkah,
  Wynlla, Ahlen, Zakharov, Pondsmânia, Academia Arcana, Vectora) — LORE detalhada.
- **Cap. 2: Além do Reinado** (172–323): ~17 nações/regiões (Supremacia Purista, Aslothia,
  Salistick, Império de Tauron, Smokestone…).
- **Cap. 3: Além de Arton** (324–423): ~11 continentes/planos (Lamnor, Khalifor, Galrasia,
  Tamu-ra, Moreania, Doherimm, Éter Divino…).
- **Cap. 4: Organizações** (424–447): Exércitos & Mercenários, Igrejas & Ordens, Guildas.
- **Cap. 5: Vida em Arton** (448–471): sociedade, viagens, comércio, lei, aventura.
- **Apêndice: Origens Regionais** (472–483): **conteúdo MECÂNICO** — origens ligadas a regiões.

**Nota de procedência:** o núcleo já tem a família `mundo_arton` (30 regiões, Cap. 9 da edição
base). O Atlas EXPANDE essas regiões com muito mais detalhe → registros próprios `fonte=
"atlas-arton"` que COEXISTEM com o núcleo (contrato multi-livro), nunca sobrescrevem.

## Integrado

### Origens Regionais — Apêndice (`capitulo="origens-regionais"`, 68 chunks)

`extrair_origens_regionais_atlas.py` → `dados/origens_regionais_atlas.json` (gitignored) →
`gerar_origens_regionais_atlas_html.py` → `integrar_origens_regionais_atlas.py` (idempotência
estreita própria).

**66 origens regionais** (`tipo="origem"`, `subtipo="regional"`): cada uma = nome (Tormenta20
~16pt, 2 linhas juntadas) + **região** (tag Tormenta20 ~11pt) + Itens + Benefício; perícias
concedidas canonizadas contra as 29 reais. Reusa a máquina das origens do núcleo/Heróis.
**Achado:** nome de 2 linhas junta por continuação minúscula **OU** quando o registro anterior
ainda está sem conteúdo (ex.: "Catador da"+"Cidade Velha", continuação maiúscula). 41 regiões
distintas. Índice 3602→**3670**; `atlas-arton` estreia com 68 chunks. Recuperação rank-1
(Amazona de Hippion — coexiste com a distinção Amazona do Heróis; Anão de Armas; Assistente
Forense de Salistick). Cosmético: kerning do PDF às vezes injeta espaço no meio de nomes
próprios ("Duyshid akk", "Emissár io").

## Backlog (não integrado) — o grosso do livro é LORE

- **Regiões** (Caps. 1–3, ~58 regiões): cada região = candidata a 1+ chunk de overview
  (geografia/regente/cultura/ganchos), expandindo a `mundo_arton` do núcleo. É o volume maior.
- **Organizações** (Cap. 4): exércitos, igrejas/ordens, guildas.
- **História / Linha do Tempo** (Introdução): lore cronológica.
- **Vida em Arton** (Cap. 5): sociedade, viagens, comércio, lei.

**Decisão de escopo pendente com o usuário:** como modelar as regiões (1 overview por região
vs. sub-seções), dado o tamanho (ex.: Deheon = 16 págs).
