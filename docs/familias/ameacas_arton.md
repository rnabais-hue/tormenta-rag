# Família estruturada: Bestiário de *Ameaças de Arton* (livro de expansão)

> **Status: EM CURSO (piloto validado no método).** Livro de expansão, `fonte="ameacas-arton"`.
> Escopo desta família: **só as CRIATURAS** do bestiário (Cap. 1). As raças variantes
> (espalhadas em caixas soltas) ficam **fora** por decisão de projeto.

Primeira família do esforço **multi-livro**. Difere das do núcleo em dois pontos:
1. Vem de um livro que **não passou pela `ingestao.py`** → a integração é **aditiva**
   (não há texto corrido a substituir; só embute os chunks novos).
2. Os ~28 grupos temáticos são a **mesma entidade** (criatura), **mesmo schema**,
   **mesmo extrator** → a paralelização é **por lote de grupos**, não por arquivo (ver §6).

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

**Dois consertos de raiz (aprendidos por diagnóstico, não palpite):**
- **Banda de coluna = 205pt** (< ~221pt entre as duas colunas): impede fundir as colunas e
  captura a **linha de atributos centralizada** (o x0 dela varia muito).
- **Família completa de traços** nos atributos: o PDF usa **em-dash (U+2014)** para "sem
  atributo" em mortos-vivos sem mente — não só hyphen/en-dash.

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
Gera `dados/ameacas_arton.json`. Conferência offline: `dados/ameacas_arton.html`
(gerada por `gerar_ameacas_arton_html.py`).

---

## 5. Estado do piloto (Dragões + Mortos-Vivos)

- **33 criaturas | ND 30/33 | atributos 24/33 | Def/PV/tipo/tamanho ~85%.**
- **Resíduos conhecidos** (a resolver na conferência ou em nova passada de parser):
  - Nome de **variante de dragão truncado ao sufixo** ("Bosque" em vez de "Dragão Filhote do
    Bosque") — o prefixo está no título 27pt destacado, cuja geometria varia.
  - **PV de colossal** que quebra entre colunas (ex.: Sckhar) captura só o 1º dígito.
  - Vazamento ocasional de **cabeçalho de grupo** no nome.

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
