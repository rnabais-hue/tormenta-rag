# Família estruturada: *Atlas de Arton* (3º livro de expansão)

> **Status: MECANICAMENTE COMPLETO — lore fora de escopo por decisão.** `fonte="atlas-arton"`
> (registrado em [`fontes.py`](../../fontes.py)). Livro grande (484 págs), **quase 100% lore/
> geografia**; a ÚNICA pegada mecânica é o apêndice de Origens Regionais — **já integrado**.
> Layout = Heróis/núcleo (corpo IowanOldStyle, nomes Tormenta20, caixas SourceSansPro).
>
> **Decisão (2026-08-27):** focar só em crunch (itens/poderes/regras/stat blocks) e pular a
> prosa. Uma varredura mecânica do livro inteiro (marcadores ND+Fort+Von, Pré-requisito, Custo,
> Item, recebe +N, CD, teste de) achou **zero** stat blocks, **zero** itens, **zero** poderes
> nas págs 46–471 — só as Origens Regionais (pg 472+). As menções esparsas a CD/Poder/teste no
> corpo são referências narrativas, não entidades extraíveis. Logo, **não há mais conteúdo
> mecânico a extrair**; a lore profunda (regiões/organizações/história) fica fora de escopo por
> ser baixo ROI para RAG (artigos de 10–16 págs/região, sem âncora tipográfica, e o núcleo
> `mundo_arton` já cobre o "o que é o reino X" em nível útil).

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

## Fora de escopo (LORE — decisão de não integrar)

Todo o corpo do livro é lore e **não será estruturado** (baixo ROI para RAG, sem crunch):
- **Regiões** (Caps. 1–3, ~58 regiões): artigos de 10–16 págs de prosa (geografia/regente/
  cultura/ganchos). O núcleo `mundo_arton` (30 regiões, 1 overview cada) já responde o essencial.
- **Organizações** (Cap. 4), **História/Linha do Tempo** (Introdução), **Vida em Arton** (Cap. 5).

Se algum dia o objetivo mudar (ex.: um modo "enciclopédia de ambientação" em vez de assistente
de regras), a fatia de maior valor seria um **passe raso**: 1 overview conciso por região tirado
só do resumo de abertura (não das 16 págs), ~30–50 chunks p/ os Caps 1–2. Não recomendado para o
uso atual (assistente de regras).
