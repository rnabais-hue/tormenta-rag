# Heróis de Arton — Capítulo 3: Arsenal dos Heróis (COMPLETO)

`fonte="herois-arton"` · págs 216–279 · versão 1.1 · **3 capítulos-de-integração:**
`capitulo="arsenal"` (Novos Equipamentos), `capitulo="arsenal-magico"` (Magias/Artefatos/
Itens Mágicos), `capitulo="arsenal-menor"` (Melhorias/Capangas/Veículos/Bases).

**Cap. 3 COMPLETO.** Extração estruturada de todo o Arsenal em três rodadas de integração,
cada uma com idempotência estreita própria (por `capitulo`).

## Pipeline

- `extrair_equipamentos_herois.py` — PDF → `dados/equipamentos_herois.json` (gitignored).
  As **tabelas** de stats saem com linhas fundidas no `find_tables` (layout adversarial),
  então as linhas são montadas por **posição-x das colunas** (`_linhas_por_y` + mapeamento de
  colunas por faixa de x). A **tabela é a lista autoritativa** de entidades; as **descrições**
  (nome em `IowanOldStyle-Bold` terminando em "." + corpo `Roman`) são casadas por slug.
- `gerar_equipamentos_herois_html.py` — ferramenta de conferência visual (`equipamentos_herois.html`).
- `integrar_equipamentos_herois.py` — embute e adiciona ao FAISS. **Idempotência ESTREITA**:
  remove só chunks com `capitulo=="arsenal"` (NÃO toca no Cap 1 `herois-arton` nem no núcleo).
  Recomputa `meta["fontes"]` do zero. Reconstrói apenas os vetores novos.

## 1ª rodada — Novos Equipamentos (`capitulo="arsenal"`, 205 chunks)

> Histórico desta rodada. O chunk `Pendência` abaixo listava o que faltava na época; hoje o
> Arsenal está COMPLETO (ver as rodadas 2 e 3 adiante). Índice na época: 2539→2744.

| Sub-parte | Registros | Tabela | Obs. |
|---|---|---|---|
| Armas | 39 | 3-1 | munição-padrão de referência (Virotes/Flechas/Balas) excluída |
| Munições especiais | 5 | 3-2 | coluna direita; descrições próprias |
| Armaduras & Escudos | 14 | 3-3 | 5 leves + 5 pesadas + 4 escudos |
| Itens Gerais | 128 | 3-4 | 13 subcategorias; **exclui 5 veículos-de-catálogo** sem descrição |
| Habilidades de arma | 2 | — | Ocultável, Surpreendente |
| Listas de recuperação | 16 | — | por seção/subcategoria |
| Pendência | 1 | — | `tipo="pendencia"` |

Descrições casadas: armas 39/39, munições 5/5, armaduras 14/14, itens gerais 118/128
(as 10 sem texto são serviços que **não têm descrição no livro** — linha de preço). Todos os
188 itens carregam dados estruturados completos (nome/preço/subcategoria/espaços/stats).

Validação E2E: `faiss==chunks==meta==2744`; recuperação rank-1 dos itens novos com fonte/página
corretas; regressão do núcleo (Fatigado) e do Cap 1 (Sátiro) OK; pendência recuperável.

## Arsenal Mágico — INTEGRADO (2ª rodada; `capitulo="arsenal-magico"`, 241 chunks)

Recorte de alto valor das pendências, em `integrar_arsenal_magico_herois.py` (idempotência
estreita PRÓPRIA por `capitulo=="arsenal-magico"` — não toca no `capitulo=="arsenal"` dos
Novos Equipamentos):

| Sub-parte | Registros | Extrator | Método |
|---|---|---|---|
| **Novas Magias Arcanas** | 22 | `extrair_magias_herois.py` | reusa o schema/stat-block do núcleo; a ORDEM DE BLOCOS do PyMuPDF já é a de leitura → segmenta por cabeçalho "Arcana N (Escola)". Normaliza versalete CAIXA-ALTA no nome |
| **Artefatos** | 8 | `extrair_artefatos_herois.py` | nome 21pt (às vezes partido) + descrição (lore+poderes) |
| **Novos Itens Mágicos** | 202 itens + 5 regras | `extrair_itens_magicos_herois.py` | 11 categorias (encantos/específicos/maldições) no padrão rótulo-bold-"." (como as construções de Domínio); categoria por palavra-chave no cabeçalho — **PROC antes de item** porque "amaldiçoados"/"removendo maldições" contêm "maldic"; filtro de legenda "Tabela N" |

Itens mágicos por categoria: encanto_armas 22, armas_especifico 17, encanto_armaduras 20,
armaduras_especifico 5, escudos_especifico 5, encanto_esotericos 26, esotericos_especifico 4,
encanto_acessorios 8, acessorios_especifico 64, maldicao_armas 14, maldicao_armaduras 17.
Regras procedurais: Itens Inteligentes, Criando um Item Mágico Inteligente, Ego, Itens
Amaldiçoados, Removendo Maldições. `gerar_arsenal_magico_html.py` = conferência combinada.

## Arsenal Menor — INTEGRADO (3ª rodada; `capitulo="arsenal-menor"`, 80 chunks)

Fecha o Cap. 3, em `extrair_arsenal_menor_herois.py` (reusa a máquina header-driven do
`itens_magicos`) + `integrar_arsenal_menor_herois.py`:

| Sub-parte | Registros | Tipo | Método |
|---|---|---|---|
| **Novas Melhorias** de item | 12 | `melhoria_item` | rótulo negrito-"." + descrição |
| **Capangas** (grupos p/ contratar) | 6 | `capanga` | idem |
| **Veículos** | 5 | `veiculo` | idem ("Animais de Tração" ficou no módulo Jogando com Veículos) |
| **Cômodos** de Base | 41 | `comodo_base` | idem |
| **Módulos procedurais** | 11 | `regra_opcional` | Itens Superiores, Capangas Convocados, regras de Veículos e de Bases (Adquirindo/Características/Tipos/Porte/Segurança/Manutenção) |
| **Mobílias** (Tabela 3-8) | 25 | `mobilia_lista` | geometria 2-col; nome de 2 linhas juntado por continuação minúscula |

Achado: **flush de cabeçalho entre níveis** (27→21pt) para não fundir "Itens Superiores"
(intro) com "Novas Melhorias" (lista). **CAP. 3 100% integrado** (só o núcleo/edição-base
não repete estas seções). Bases deixou de ser adiada.

Follow-up técnico: incluir o equipamento de Heróis no filtro híbrido
`detectar_filtro_equipamento()` de `perguntar.py`.
