# Família estruturada: *Heróis de Arton* — Cap. 1: Campeões de Arton

> **Status: PARCIALMENTE INTEGRADO (3 de ~5 sub-famílias no FAISS).** 2º livro de
> expansão, `fonte="herois-arton"`. Cap. 1 (págs 8–103) = opções de personagem
> (raças, classes, origens, poderes). Prioridade do usuário entre livros: **1 → 3 → 2 → 4**.

*Heróis de Arton* v1.1 (332 págs, 4 caps) é o "livro do jogador". Diferente dos outros PDFs,
tem **TOC nativo bom** (`doc.get_toc()`, 183 entradas) — a segmentação parte dele/da tipografia.

## 0. Particularidades de layout deste livro (reusar nas próximas famílias)

- O corpo é **IowanOldStyle** (não SourceSansPro como núcleo/Ameaças). Negrito detectado por
  flag OU `"Bold"` no nome da fonte. **SourceSansPro** = pull-quotes/caixas → **descartar**.
- **Drop-caps** decorativos (Tormenta20 ≥36pt, 1–2 letras, ex.: "Q", "P") → descartar.
- **Splash de capítulo** (Tormenta20 ≥40pt, "Novos Poderes...") → descartar.
- **Filtro de margem topo/rodapé (y<6% / >94%) só vale p/ spans <20pt** — títulos de seção
  grandes ficam no topo (ex.: "poderes de raça" 58pt em y≈39) e **não** podem ser filtrados.

---

## 1. Sub-famílias do Cap 1

| Sub-família | Págs | Extrator | Estado |
|---|---|---|---|
| **Novas Raças** (5) | 10–17 | `extrair_racas_herois.py` | ✅ integrado |
| **Novos Poderes** (443) | 56–97 | `extrair_poderes_herois.py` | ✅ integrado |
| **Nova Classe: Treinador** | 18–23 | `extrair_treinador_herois.py` | ✅ integrado |
| Classes Variantes (14) | 24–47 | — | ⏳ falta |
| Novas Origens (30) | 48–55 | — | ⏳ falta |
| Tabelas para Personagens | 98–103 | — | ⏳ falta |

---

## 2. Novas Raças (`extrair_racas_herois.py`)

5 raças (págs 10–17). Adapta o extrator do núcleo (`extrair_racas.py`): mesmo schema
(`modificadores{atr:±N}`, `resumo`, `habilidades[{nome,efeito}]`), âncora no nome Tormenta20
≥20pt, lore roman antes do 1º negrito = resumo.

- **Duende** (pág 10) é **procedural** ("monte sua raça": Natureza/Tamanho/Dons/Presentes) →
  marcada `procedural=True` e guardada como `texto_completo` (fragmentar em habilidades daria lixo).
- **Eiradaan, Galokk, Meio-Elfo, Sátiro** = padrão (mods + traços tipo "Festeiro Feérico").
- Conserto: modificador flexível generalizado p/ "+N em (um|dois|três|quatro) atributos, exceto X"
  (o Meio-Elfo é "+1 em dois atributos, exceto Constituição").

## 3. Novos Poderes (`extrair_poderes_herois.py`)

**443 poderes** (288 de classe ×14 classes + 155 gerais). Duas seções, mesmo layout: header
27/58pt = **classe** (Poderes de Classe, p56–79) ou **categoria** (Poderes Gerais, p80–97:
combate 25, destino 13, magia 14, tormenta 6, **raça 77**, **grupo 20**). Cada poder: nome
Tormenta20 16pt (âncora, spans multi-linha mesclados); efeito = corpo IowanOldStyle até o
próximo poder; **pré-requisito** (TEXTO) extraído do efeito — 287/443 têm. Schema compatível
com os poderes do núcleo (`tipo="poder"`, `categoria`, `classe`, `pre_requisito`).

## 4. Nova Classe: Treinador (`extrair_treinador_herois.py`)

Classe completa (não variante), págs 18–23. Delimitada pelos headers de seção 21/27pt
(Características de Classe → Habilidades de Classe → O Melhor Amigo → Truques). Schema
compatível com `classes.json`: `caracteristicas{pv,pm,pericias,proficiencias}`,
`atributo_principal` (Carisma), `habilidades[{nome,efeito}]` (7: Direcionar, Melhor Amigo,
Domar Criatura, Poder de Treinador, Treino Especializado, Sincronia de Combate/Perfeita), +
campo `melhor_amigo` (o pet da classe + Truques).

---

## 5. Integração (`integrar_herois_cap1.py`)

Aditiva, `fonte="herois-arton"`, idempotente (remove chunks herois-arton antes de reinserir);
reconstrói só os vetores novos (não reembute núcleo/ameacas-arton). Chunks:
- 1 por raça (`tipo="raca"`); 1 por poder (`tipo="poder"`) + listas por classe/categoria
  (`tipo="poder_lista"`); Treinador = visão geral + 1 por habilidade + melhor_amigo (`tipo="classe"`).
- **477 chunks** no total. Citação resolve o livro via `fontes.py` ("Heróis de Arton, pág. X").
- Os filtros híbridos existentes (`detectar_filtro` de raça/poder) já cobrem — só a procedência
  (`fonte`) distingue do núcleo. Poderes/raças repetidos entre livros coexistem.

Uso:
```
python extrair_racas_herois.py
python extrair_poderes_herois.py
python extrair_treinador_herois.py
python integrar_herois_cap1.py
```

---

## 6. Falta para fechar o Cap 1

Classes Variantes (14: Alquimista, Atleta, Duelista…), Novas Origens (30, reusa
`extrair_origens.py`) e Tabelas para Personagens. Depois: Cap 3 (Arsenal), Cap 2 (Distinções),
Cap 4 (Regras Opcionais).
