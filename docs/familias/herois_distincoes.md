# Heróis de Arton — Capítulo 2: Distinções (parcial seguro)

`fonte="herois-arton"` · `capitulo="distincoes"` · págs 104–215 · versão 1.1

Extração estruturada das **36 Distinções** (entidade NOVA do sistema). Integrado o
recorte seguro; 18 poderes de efeito fino ficam no backlog (chunk `tipo="pendencia"`).

## O que é uma Distinção (anatomia)

Cada distinção ocupa **3 páginas**, começando na **página de splash** (nome gigante
Tormenta20 sz~58 + drop-cap). Estrutura interna, guiada por tipografia:

- **Conceito** — prosa de lore/introdução (corpo IowanOldStyle).
- **Admissão** (Tormenta20 sz~21) — o requisito para entrar na distinção.
- **Marca da Distinção** (sz~21) — 1 poder-marca (nome sz~16 + efeito).
- **Poderes da distinção** (sz~21) — N poderes (nome sz~15-16, tag de categoria
  opcional sz~11 tipo "Tormenta", + efeito).
- Caixa "X em Jogo" (SourceSansPro) — conselho de mestre → **descartada**.

## Pipeline

- `extrair_distincoes_herois.py` — PDF → `dados/distincoes_herois.json` (gitignored).
  **Descobertas-chave do layout:**
  1. O **TOC aponta para a página mecânica** (3ª), não o início visual → segmentação
     por detecção das **páginas de splash** (span Tormenta20 sz>=50), 36 a cada 3 idx.
  2. Processamento **linha-a-linha** preservando a ordem dos spans dentro da linha —
     senão as **refs inline itálicas** ("Tormenta20, p. X") deslocam e corrompem o efeito.
  3. Descartar `IowanOldStyle-BoldItalic` (epígrafes/pull-quotes flavor).
  4. Máquina de estados conceito→Admissão→Marca→Poderes; nomes de poder quebrados em
     2 linhas são mesclados **só quando a continuação começa em minúscula** (evita
     fundir poderes distintos em grids compactos).
- `gerar_distincoes_herois_html.py` — conferência visual (destaca efeito curto).
- `integrar_distincoes_herois.py` — embute e adiciona ao FAISS. **Idempotência ESTREITA**
  (`capitulo=="distincoes"`; não toca em Cap 1/Arsenal/núcleo). Recomputa `meta["fontes"]`.

## Integrado (recorte seguro — 215 chunks; `herois-arton` 869→1084; índice 2744→2959)

| Tipo | Qtd | Conteúdo |
|---|---|---|
| `distincao` (overview) | 36 | conceito + admissão + marca + lista de poderes |
| `distincao_poder` | 177 | poderes com efeito limpo (≥40 chars) |
| `distincao_lista` | 1 | lista das 36 distinções |
| `pendencia` (backlog) | 1 | os 18 poderes de efeito fino |

Validação E2E: `faiss==chunks==meta==2959`; overviews/poderes rank-1 (Amazona, Aeronauta
Goblin por descrição semântica); backlog recuperável; regressão núcleo (Fatigado) + Cap 1
(Sátiro) + Arsenal (Montante cinético) OK. Nota: nomes próprios que colidem com lore do
núcleo (Smokestone-cidade, "Tormenta") podem rankear o chunk do núcleo primeiro — os
chunks de distinção existem e aparecem com k maior.

## Backlog (NÃO integrado como chunk próprio)

**18 poderes de distinção com efeito não capturado** (layout compacto/grid — ex.: as
posturas do Campeão de Dojo, poderes da Amazona/Cavaleiro Feérico). Estão **nomeados no
overview** de cada distinção, mas o texto do efeito precisa de refino no extrator (o
efeito colou na coluna vizinha ou ficou vazio). Listados no chunk `tipo="pendencia"`.
