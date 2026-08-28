# Família estruturada: Bestiário de *Ameaças de Arton* (livro de expansão)

> **Status: CRIATURAS + RAÇAS JOGÁVEIS INTEGRADAS.** Livro de expansão, `fonte="ameacas-arton"`.
> Escopo: **as CRIATURAS** do bestiário (Cap. 1, 344 no FAISS + 55 pendentes) **e as 27 RAÇAS
> JOGÁVEIS** (Apêndice A + caixas "Habilidades de Raça"), integradas em `capitulo="racas"`.

Primeira família do esforço **multi-livro**. Difere das do núcleo em dois pontos:
1. Vem de um livro que **não passou pela `ingestao.py`** → a integração é **aditiva**
   (não há texto corrido a substituir; embute os 377 chunks estruturados com `fonte="ameacas-arton"`).
2. Os 29 grupos temáticos compartilham a **mesma entidade** (criatura), **mesmo schema** e
   **mesmo extrator** linear com suporte a tabela larga e fusão contínua.

---

## 1. Fonte no livro

- Arquivo: `livro/Ameacas-de-Arton-v1.0-17-11-2023.pdf` (436 págs).
- **Cap. 1: Ameaças** (págs 12–373) = o bestiário, em ~28 grupos temáticos. Estimativa:
  **~250–400 criaturas** (3–5× o bestiário do núcleo).
- Cap. 2 (regras de criação de ameaças) e Cap. 3 (Bazar Monstruoso: equip/magia) ficam
  **fora** desta família.

---

## 2. Método de extração (`extrair_ameacas_arton.py`)

O núcleo usava uma **tabela hard-coded** de 80 criaturas. Aqui são ~300 → **auto-descoberta
por tipografia + geometria**. O layout deste livro é adversarial (2 colunas, variantes por
página, texto-sombra decorativo, nomes quebrados/concatenados, blocos fora de ordem,
marca-d'água). Estratégia que funcionou:

1. **Manter só os spans do stat block:** `Tormenta20` (nome/ND/tipo, ≥13pt) + `SourceSansPro`
   (ficha, ~9pt). Descartar `IowanOldStyle` (lore/caixas), `Helvetica` (marca-d'água),
   `SourceSansPro` ≤8.5pt (sombra) e nº de página (`Tormenta20` ≤12.5pt).
2. **Âncora geométrica:** cada NOME (span `Tormenta20` ≥13pt) ancora uma criatura; o **corpo**
   são os spans **abaixo** dele, na **mesma faixa de coluna**, até o próximo nome.
3. **Reconstruir o texto por linha visual** (faixa de y) → x, corrigindo a ordem de leitura
   (o que perdia ND/atributos fora de fluxo e PV que quebra de coluna).
4. **Campos por regex** (mesmo formato do núcleo): tipo/tamanho/papel, Iniciativa, Percepção,
   Defesa, Fort/Ref/Von, PV/PM, Deslocamento, ataques, atributos, perícias, tesouro.

**Consertos de raiz (aprendidos por diagnóstico, não palpite):**
- **Banda de coluna = 205pt** (< ~221pt entre as duas colunas): impede fundir as colunas e
  captura a **linha de atributos centralizada** (o x0 dela varia muito).
- **Família completa de traços** nos atributos: o PDF usa **em-dash (U+2014)** para "sem
  atributo" em mortos-vivos sem mente — não só hyphen/en-dash.
- **Descartar o título-splash decorativo (Tormenta20 ≥20pt)**: cada criatura tem um NOME de
  ficha (16pt) e, no topo da página, um **título-splash gigante (21–27pt)** que DUPLICA o nome
  (ou repete o cabeçalho do grupo). Esse splash era a causa dos **"merges"** — grudava no nome
  real e, na tabela larga, fundia criaturas vizinhas. Regra: numa página que tem nome de ficha
  (16pt), os spans ≥20pt são splash → descarta; em página de **BOSS** (só nome grande, sem
  16pt) o ≥20pt é o único nome → mantém. Isso recuperou ~20 criaturas antes perdidas/fundidas.
- **`limpar_nome(nome, grupo)`**: tira prefixo = nome-do-grupo vazado, e deduplica n-grama
  liderante / sufixo==prefixo (variantes cujo título 27pt sobra no nome).

Schema de cada criatura (carimba `fonte="ameacas-arton"`):
```
id, tipo="ameaca", fonte, nome, grupo, nd, pagina,
tipo_criatura, subtipo, tamanho, papel, iniciativa, percepcao, sentidos,
defesa, fortitude, reflexos, vontade, resistencias, pv, pm, deslocamento,
corpo_a_corpo, distancia, atributos{for,des,con,int,sab,car}, pericias, equipamento, tesouro
```

---

## 3. Grupos do bestiário (partição para paralelizar)

| # | Grupo | Págs | # | Grupo | Págs |
|---|---|---|---|---|---|
| 1 | Brutos & Indomáveis | 32–43 | 15 | Mascotes & Familiares | 192–199 |
| 2 | Capangas & Bandoleiros | 44–53 | 16 | Masmorras | 200–211 |
| 3 | Culto de Aharadak | 54–65 | 17 | Montarias | 212–229 |
| 4 | **Dragões** (piloto) | 66–79 | 18 | **Mortos-Vivos** (piloto) | 230–243 |
| 5 | Duyshidakk | 80–89 | 19 | Mundo Perdido | 244–253 |
| 6 | Elementais | 90–103 | 20 | Piratas & Pistoleiros | 254–265 |
| 7 | Ermos | 104–115 | 21 | Povos-Trovão | 266–275 |
| 8 | Gnolls | 116–125 | 22 | Puristas | 276–285 |
| 9 | Golens | 126–137 | 23 | Reino dos Mortos | 286–297 |
| 10 | Igreja de Arsenal | 138–145 | 24 | Reinos de Moreania | 298–307 |
| 11 | Igreja de Kallyadranoch | 146–155 | 25 | Sanguinárias | 308–315 |
| 12 | Império de Jade | 156–169 | 26 | Sob as Ondas | 316–327 |
| 13 | Império de Tauron | 170–179 | 27 | Sszzaazitas | 328–339 |
| 14 | Kobolds | 180–191 | 28 | Trolls Nobres | 340–349 |
|   |   |   | 29 | Uivantes | 350–359 |

A lista canônica (`GRUPOS`) vive em `extrair_ameacas_arton.py`.

---

## 4. Como rodar

```
python extrair_ameacas_arton.py            # grupos-piloto (Dragões + Mortos-Vivos)
python extrair_ameacas_arton.py --todos    # todos os grupos de criatura
```
O extrator já **particiona** a saída: criaturas **completas** (ND+Defesa+PV+≥4 atributos) vão
para `dados/ameacas_arton.json` (as que entram no índice); as **incompletas** vão para
`dados/ameacas_arton_pendentes.json` (isoladas, fora do FAISS). O split é reprodutível — não é
mais um passo manual perdido. Conferência offline: `dados/ameacas_arton.html`
(gerada por `gerar_ameacas_arton_html.py`).

---

## 5. Estado da FASE 1 (todos os grupos integrados)

- **344 criaturas completas integradas no FAISS** (`fonte="ameacas-arton"`), + 29 chunks-lista
  por grupo + 4 chunks-lista por faixa de ND = **377 chunks**. As **55 criaturas** incompletas
  ficam isoladas em `dados/ameacas_arton_pendentes.json` (**fora** do índice).
- **Qualidade** (via `diagnostico_ameacas.py`): nomes limpos na origem — **4 resíduos** só, dos
  quais 2 são falsos positivos (nomes legítimos "Estouro de Fúrias de Tauron" e "tigre-de-Hyninn"
  — o livro grafa minúsculo). O conserto do splash + `limpar_nome(nome,grupo)` derrubou os nomes
  ruins de **47 → ~2** e **recuperou ~20 criaturas** antes fundidas (ex.: "Goblin de Sombreiro"
  ND2 + "Líder Goblin de Sombreiro" ND6; "Caçador de Impuros" ND8; "Glooop"; "Mímico"; "Cavalo
  Glacial"; "Kobold Xamã").
- **Resíduos conhecidos** (validação 2026-08-24, agora no parser, não só no JSON):
  - **1 merge duro:** pág. 63 **Avatar de Aharadak** — boss multi-parte (Armadura/Asas/Flagelo/
    Mente/Olhos do Devorador) num layout especial; o registro ficou como "Avatar de Aharadak"
    (renome manual no JSON) mas as partes não viraram registros próprios.
  - **~5 habilidades perdidas em TABELA-LARGA:** quando 2 criaturas dividem linhas interleaved
    (ex.: pág. 300 "Mantícora" vs "Mantícora Primal"), as habilidades vão todas para a 1ª;
    a 2ª fica sem. Afeta Mantícora, Nereida, Mamute Esqueleto, Gali-Gali, Stagh. Os demais
    "sem habilidades" (Orc Combatente, Bandido, Pirata, Cavalo, Glop) são **corretamente vazios**.
  - **PV/ND de colossais** que quebram entre colunas → vão para pendentes (ex.: Sckhar, Tarso,
    Avatar de Kallyadranoch, Senhor do Gigante). Catalogados, mas incompletos.
  - **`de Bullton`** (pág. 304): o prefixo "Búfalo Paladino" era splash e foi descartado;
    renome manual no JSON para "Búfalo Paladino de Bullton".

---

## 6. Convenção de PARALELIZAÇÃO (importante)

Como todos os grupos compartilham **um extrator** e **um schema**:
- **Só UMA frente edita `extrair_ameacas_arton.py`** (a dona do parser). Quirk de grupo que
  exija mexer no código passa por ela.
- Cada frente pega um **lote de grupos**, roda o extrator (congelado) no seu lote, gera um
  **JSON próprio** (sugestão: `dados/ameacas_arton_<lote>.json`), confere no HTML e corrige
  resíduos **no seu JSON**.
- Um passo de **merge** junta os JSONs de lote → `dados/ameacas_arton.json`.
- **Integração única** (`integrar_ameacas_arton.py`, uma frente só) adiciona os chunks ao
  índice com `fonte="ameacas-arton"`. Aditivo: não remove nada do núcleo; criaturas repetidas
  entre livros (Orc, Esqueleto) coexistem, distinguidas pela procedência.
- Regras gerais de paralelismo do projeto valem: antes de commitar, `git branch --show-current`;
  só uma frente edita `perguntar.py`/índice.

---

## 7. Filtro e consulta

Não precisa de filtro novo: as criaturas usam `tipo="ameaca"`, então o
`detectar_filtro_ameaca` existente (ND/faixa/grupo) já as cobre. A procedência (`fonte`)
distingue do bestiário do núcleo e aparece na citação ("segundo *Ameaças de Arton*, pág. X").
Follow-up opcional: `detectar_filtro_fonte` para escopar por livro.

---

## 8. Raças Jogáveis (Apêndice A) — `capitulo="racas"`, 28 chunks

`extrair_racas_ameacas.py` → `integrar_racas_ameacas.py`. **27 raças jogáveis** (`tipo="raca"`,
`subtipo="ameacas"`) — as ameaças do bestiário que podem ser usadas como personagem — + 1 lista.
Eram "o pior caso de extração" (caixas soltas espalhadas no bestiário), agora resolvido.

**Chave da extração:** o **Apêndice A (pg 418)** traz a **Tabela A-1: Raças para Personagens**
(nome + modificadores de atributo + página), que serve de índice autoritativo. Cada raça tem, na
sua página, uma **caixa "{Nome}: Habilidades de Raça"** com: linha de modificadores por extenso +
habilidades raciais no padrão rótulo-bold ("Nome. descrição" em IowanOldStyle-Black) — o MESMO
formato das raças do núcleo (`Longevidade.`/`Devotos.` fecham a caixa).

**Motor** (`extrair_racas_ameacas.py`): acha os headers "Habilidades de Raça" (SourceSansPro-Bold
~13pt ou Mansalva ~20pt, NÃO Tormenta20; filtro por tamanho exclui as menções 9.5pt no corpo),
delimita a caixa via `get_drawings()` (com **fallback sintético** quando não há retângulo, ex.:
Kobolds), ordena o texto em 2 colunas e parseia modificadores + habilidades. **Descobertas:**
(1) header pode vir em 2 linhas ("Tengu: Habilidades" + "de Raça") → junta a linha seguinte;
(2) variantes usam "**Raça Variante: X**" (Trog Anão, Soterrado — referenciam uma base como
osteon/golem); (3) o negrito do rótulo é IowanOldStyle-**Black**, não *-Bold; (4) nome limpo pelas
1–3 palavras capitalizadas, com dedup ("Trog Anão Trog"→"Trog Anão"); entradas sem habilidade são
descartadas (ruído). Golem (construct "mais especial") e Moreau (3 sub-caixas macho/fêmea a 9.5pt)
ficam de fora — casos irregulares de baixo valor marginal.

Raças: Meio-Orc, Orc, Tabrachi, Trog Anão, Ogro, Bugbear, Hobgoblin, Centauro, Gnoll, Kallyanach,
Kaijin, Kappa, Mashin, Nezumi, Tengu, Minauro, Kobolds, Harpia, Ceratops, Pteros, Velocis, Voracis,
Yidishan, Elfo-do-Mar, Nagah, Finntroll, Soterrado. Recuperação rank-1 validada.
