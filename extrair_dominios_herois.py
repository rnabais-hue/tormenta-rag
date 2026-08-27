# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do subsistema DOMÍNIOS — *Heróis de Arton* (Cap. 4, págs 316–329).

Regra opcional (fonte="herois-arton"). Subsistema de regência/reino. Três tipos de saída:
  1. **Módulos procedurais** (`tipo="regra_opcional"`, regra="Domínios"): Tornando-se Regente
     (+Criando/Conquistando um Domínio), Características (Níveis, Terreno, Corte, Popularidade,
     Fortificações), Turnos de Domínio (Etapas 1–3), Domínios Místicos, Eventos Aleatórios
     (Resolvendo Eventos, Batalhas Simplificadas, Revoltas).
  2. **Construções** (`tipo="construcao_dominio"`): cada prédio = nome (rótulo negrito
     terminando em ".") + descrição/efeito. Lista A→Z (págs 318–324).
  3. **Unidades Militares** (`tipo="tabela"`): a Tabela 4-11 (Tropa/Construção/Custo/
     Manutenção/Poder/Desl./Defesa/Dano) via find_tables (best-effort).

Máquina de estados dirigida pelos cabeçalhos Tormenta20 (27/21/16pt). Buffer de cabeçalho
com FLUSH-no-corpo separa títulos partidos ("Tornando-se"+"regente") de seções distintas
(entre elas há corpo). Duas colunas → ordenação por bloco; caixas (tabelas/sidebars) fora
do fluxo via get_drawings(). Drop-cap religado.

BACKLOG (sub-pendência): tabelas-resumo de custo (Terrenos 4-9, Construções 4-10) e a de
Eventos (4-13) — numéricas multi-coluna, ficam para um refino posterior.

Saída: dados/dominios_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "dominios_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 316, 329
RE_PREDIO = re.compile(r"^[A-ZÀ-Ú][\wÀ-ÿ][\wÀ-ÿ ()\-]{0,28}\.$")


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def juntar(parts):
    out = ""
    for t in parts:
        if not out:
            out = t; continue
        if re.search(r"[A-Za-zÀ-ÿ]-$", out):
            out = out[:-1] + t.lstrip()
        elif out.endswith((" ", "\n")) or t[:1].isspace():
            out = out + t
        else:
            out = out + " " + t
    return out


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _dentro(r, sx, sy):
    return r.x0 - 1 <= sx <= r.x1 + 1 and r.y0 - 1 <= sy <= r.y1 + 1


def coletar_spans(doc):
    out = []
    for pg in range(PG_INI - 1, PG_FIM):
        page = doc[pg]; W, H = page.rect.width, page.rect.height
        boxes = [d["rect"] for d in page.get_drawings()
                 if d.get("fill") is not None and d["rect"].width >= 100 and d["rect"].height >= 55]
        maxsz = [0.0] * len(boxes)
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    for i, r in enumerate(boxes):
                        if _dentro(r, s["bbox"][0], s["bbox"][1]):
                            maxsz[i] = max(maxsz[i], s["size"])
        boxes = [r for i, r in enumerate(boxes) if maxsz[i] < 24]
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            bx0, by0 = b["bbox"][0], b["bbox"][1]
            bcol = 0 if bx0 < W * 0.40 else 1
            for li, l in enumerate(b["lines"]):
                for si, s in enumerate(l["spans"]):
                    if not s["text"].strip() or "Spirals" in s["font"]:
                        continue
                    sx, sy = s["bbox"][0], s["bbox"][1]
                    if (sy < H * 0.06 or sy > H * 0.94) and s["size"] < 24:
                        continue
                    if any(_dentro(r, sx, sy) for r in boxes):
                        continue                          # conteúdo de caixa/tabela → fora do fluxo
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "size": s["size"], "font": s["font"],
                                "t20": "Tormenta20" in s["font"], "ios": "IowanOldStyle" in s["font"],
                                "bold": bool(s["flags"] & (2**4)) or "Bold" in s["font"],
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def extrair_tabela_unidades(doc):
    """Tabela 4-11 (Unidades Militares), 8 colunas. Reconstrução por GEOMETRIA (o
    find_tables funde linhas ímpares): posições-x das colunas vêm do cabeçalho; cada
    span vai à coluna de x mais próximo; linhas agrupadas por banda-y (gap)."""
    page = doc[324]  # p325
    tab = next((t for t in page.find_tables().tables if t.col_count >= 6), None)
    if not tab:
        return None
    x0, y0, x1, y1 = tab.bbox
    spans = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                sx, sy = s["bbox"][0], s["bbox"][1]
                if x0 - 2 <= sx <= x1 + 2 and y0 - 2 <= sy <= y1 + 2 and s["text"].strip():
                    spans.append((round(sy, 1), sx, s["text"].strip(),
                                  bool(s["flags"] & (2**4)) or "Bold" in s["font"]))
    if not spans:
        return None
    col_nm, out = _tabela_geometrica([(s[0], s[1], s[2]) for s in spans])
    return {"nome": "Unidades Militares (Tabela 4-11)", "pagina": 325,
            "colunas": col_nm, "linhas": out}


def _tabela_geometrica(spans):
    """Reconstrói uma tabela (spans = [(y, x, texto)]) por GEOMETRIA: colunas pelas
    posições-x do cabeçalho (1ª banda-y), linhas por banda-y (gap > 8pt), cada span
    na coluna de x mais próximo. Contorna o merge ímpar/par do find_tables."""
    if not spans:
        return [], []
    spans = sorted(spans)
    y_head = spans[0][0]
    # cabeçalho pode ter 2 linhas empilhadas ("Nível"/"Máximo") → banda maior + cluster por x
    head = [(sx, sy, tx) for (sy, sx, tx) in spans if sy < y_head + 16]
    grupos = []
    for sx, sy, tx in sorted(head, key=lambda h: h[0]):
        g = next((g for g in grupos if abs(g["x"] - sx) < 20), None)  # só junta linhas EMPILHADAS (mesmo x)
        if g:
            g["spans"].append((sy, tx)); g["x"] = min(g["x"], sx)
        else:
            grupos.append({"x": sx, "spans": [(sy, tx)]})
    grupos.sort(key=lambda g: g["x"])
    col_x = [g["x"] for g in grupos]
    col_nm = [" ".join(tx for _, tx in sorted(g["spans"])) for g in grupos]
    if not col_x:
        return [], []
    dados = [s for s in spans if s[0] > y_head + 16]
    linhas, atual, last_y = [], [], None
    for (sy, sx, tx) in dados:
        if last_y is not None and sy - last_y > 8:
            linhas.append(atual); atual = []
        atual.append((sx, tx)); last_y = sy
    if atual:
        linhas.append(atual)
    out = []
    for row in linhas:
        cells = [""] * len(col_x)
        for sx, tx in sorted(row):
            j = min(range(len(col_x)), key=lambda i: abs(col_x[i] - sx))
            cells[j] = (cells[j] + " " + tx).strip()
        if any(cells):
            out.append(" | ".join(f"{col_nm[i]}: {cells[i]}" for i in range(len(cells)) if cells[i]))
    return col_nm, out


def _spans_bbox(page, bbox):
    x0, y0, x1, y1 = bbox
    sps = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                sx, sy = s["bbox"][0], s["bbox"][1]
                if x0 - 2 <= sx <= x1 + 2 and y0 - 2 <= sy <= y1 + 2 and s["text"].strip():
                    sps.append((round(sy, 1), sx, s["text"].strip()))
    return sps


def extrair_tabelas_custo(doc):
    """Tabelas-resumo de custo: Terrenos (4-9, p318), Construções (4-10, p320–321),
    Eventos Aleatórios (4-13, p328) — reconstruídas por geometria."""
    tabs = []
    for nome, pno in [("Terrenos (Tabela 4-9)", 318), ("Eventos Aleatórios (Tabela 4-13)", 328)]:
        page = doc[pno - 1]
        t = next((t for t in page.find_tables().tables if t.row_count >= 8), None)
        if t:
            cn, ln = _tabela_geometrica(_spans_bbox(page, t.bbox))
            tabs.append({"nome": nome, "pagina": pno, "colunas": cn, "linhas": ln})
    cn0, ln0 = [], []
    for pno in (320, 321):
        page = doc[pno - 1]
        t = next((t for t in page.find_tables().tables if t.row_count >= 8), None)
        if t:
            cn, ln = _tabela_geometrica(_spans_bbox(page, t.bbox))
            if not cn0:
                cn0 = cn
            ln0 += ln
    tabs.append({"nome": "Construções (Tabela 4-10)", "pagina": 320, "colunas": cn0, "linhas": ln0})
    return tabs


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    modulos, construcoes = [], []
    hdr = []                 # buffer de cabeçalho (Tormenta20 ≥15pt)
    modo = "proc"
    cur_mod = None           # módulo procedural atual
    cur_pred = None          # construção atual
    dropcap = ""

    def fecha_mod():
        nonlocal cur_mod
        if cur_mod and cur_mod["corpo"]:
            nome = cur_mod["nome"]
            modulos.append({
                "id": f"dominio:herois:{slug(nome)}", "tipo": "regra_opcional",
                "subtipo": "dominios", "regra": "Domínios", "nome": nome,
                "fonte": FONTE, "versao": "1.1", "pagina": cur_mod["pg"] + 1,
                "efeito": dehyph(juntar(cur_mod["corpo"])).strip(),
            })
        cur_mod = None

    def fecha_pred():
        nonlocal cur_pred
        if cur_pred:
            nome = dehyph(cur_pred["nome"]).rstrip(". ")
            desc = dehyph(juntar(cur_pred["desc"])).strip()
            if nome and desc:
                construcoes.append({
                    "id": f"construcao:herois:{slug(nome)}", "tipo": "construcao_dominio",
                    "nome": nome, "fonte": FONTE, "versao": "1.1", "pagina": cur_pred["pg"] + 1,
                    "descricao": desc,
                })
        cur_pred = None

    def flush_hdr(pg):
        """Cabeçalho completo → decide modo / abre módulo."""
        nonlocal modo, cur_mod
        if not hdr:
            return
        nome = dehyph(juntar(hdr)).strip(); hdr.clear()
        low = nome.lower()
        if "lista de constru" in low:
            fecha_mod(); modo = "construcoes"; return
        if "lista de unidades" in low:
            fecha_pred(); fecha_mod(); modo = "tabela"; return
        # qualquer outro cabeçalho encerra construções/tabela e abre módulo procedural
        fecha_pred(); fecha_mod(); modo = "proc"
        cur_mod = {"nome": nome, "corpo": [], "pg": pg}

    for s in spans:
        t = s["text"]; z = s["size"]
        # drop-cap / splash de capítulo (≥40pt); 27pt ainda é cabeçalho de seção!
        if s["t20"] and z >= 40:
            tt = t.strip()
            if len(tt) == 1 and tt.isalpha():
                dropcap = tt
            else:
                flush_hdr(s["pg"])          # splash "Domínios" (66pt) — ignora o nome
            continue
        # cabeçalho Tormenta20 (16/21/27pt) → acumula
        if s["t20"] and 15 <= z < 40:
            hdr.append(t)
            continue
        # corpo/prédio → primeiro fecha o cabeçalho pendente
        flush_hdr(s["pg"])
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if modo == "construcoes":
            if s["bold"] and RE_PREDIO.match(dehyph(t).strip()):
                fecha_pred()
                cur_pred = {"nome": t, "desc": [], "pg": s["pg"]}
            elif cur_pred is not None:
                cur_pred["desc"].append(t)
        elif modo == "proc" and cur_mod is not None:
            cur_mod["corpo"].append(t)
    flush_hdr(PG_FIM); fecha_pred(); fecha_mod()

    tabela = extrair_tabela_unidades(doc)
    tabelas_custo = extrair_tabelas_custo(doc)

    banco = {
        "fonte": FONTE, "livro": "Heróis de Arton", "secao": "Domínios", "pagina": PG_INI,
        "total_modulos": len(modulos), "total_construcoes": len(construcoes),
        "modulos": modulos, "construcoes": construcoes,
        "tabela_unidades": tabela, "tabelas_custo": tabelas_custo,
    }
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(modulos)} módulos + {len(construcoes)} construções -> {OUT.name}\n")
    if tabela:
        print(f"  TABELA {tabela['nome']}: {len(tabela['linhas'])} linhas")
    for tc in tabelas_custo:
        print(f"  TABELA {tc['nome']}: {len(tc['linhas'])} linhas | cols={tc['colunas']}")


if __name__ == "__main__":
    main()
