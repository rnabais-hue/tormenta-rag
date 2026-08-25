# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA dos OBJETIVOS HEROICOS — *Heróis de Arton* (Cap. 4, págs 294–295).

Regra opcional (fonte="herois-arton"). Um objetivo heroico é uma meta grandiosa que o
personagem escolhe; enquanto persegue, recebe um Benefício em cenas ligadas a ele, sofre
uma Penalidade ao se afastar, e ganha uma Conclusão permanente ao alcançá-lo. Entidade
nova: `tipo="objetivo_heroico"`.

Layout (duas colunas → ordenação por bloco). Âncoras:
  • nome do objetivo = Tormenta20 ~16pt;
  • campos = rótulos negrito IowanOldStyle "Benefício.", "Penalidade.", "Conclusão.";
  • descrição = corpo roman antes do 1º rótulo;
  • cabeçalhos 21pt (Benefícios de Objetivo, Penalidades de Objetivo, Concluindo um
    Objetivo, Tipos de Objetivos) + a legenda dos campos = `introducao` (antes do 1º nome);
  • drop-cap 78pt religado; título de seção 55pt descartado;
  • caixa SourceSans ≥12.5pt ("Abandonando um Objetivo") → regras_extra.

Saída: dados/objetivos_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "objetivos_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 294, 295


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


def caixas_da_pagina(page):
    """Retângulos preenchidos (caixas/sidebars tingidas) grandes o suficiente para
    conter texto. Servem para separar o conteúdo BOXED do fluxo principal (senão a
    caixa, que fica no topo da coluna, rouba o texto que a contorna)."""
    boxes = []
    for d in page.get_drawings():
        if d.get("fill") is None:
            continue
        r = d["rect"]
        if r.width >= 100 and r.height >= 55:
            boxes.append(r)
    return boxes


def _dentro(r, sx, sy):
    return r.x0 - 1 <= sx <= r.x1 + 1 and r.y0 - 1 <= sy <= r.y1 + 1


def coletar_spans(doc):
    out = []
    for pg in range(PG_INI - 1, PG_FIM):
        page = doc[pg]; W, H = page.rect.width, page.rect.height
        boxes = caixas_da_pagina(page)
        # descarta caixas DECORATIVAS (banner de título): as que contêm um span ≥24pt.
        # só sobram caixas de sidebar (header ≤13pt + corpo) que devem sair do fluxo.
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
                    box = next((i for i, r in enumerate(boxes) if _dentro(r, sx, sy)), None)
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "box": (pg, box) if box is not None else None,
                                "size": s["size"], "font": s["font"],
                                "ss": "SourceSans" in s["font"],
                                "t20": "Tormenta20" in s["font"],
                                "ios": "IowanOldStyle" in s["font"],
                                "bold": bool(s["flags"] & (2**4)) or "Bold" in s["font"],
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


CAMPO = [("benefício", "beneficio"), ("beneficio", "beneficio"),
         ("penalidade", "penalidade"), ("conclusão", "conclusao"), ("conclusao", "conclusao")]


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    objetivos = []
    intro = []
    cur = None
    campo = None
    dropcap = ""
    caixas = {}          # (pg,box) -> lista de spans dentro da caixa

    def fecha():
        nonlocal cur, campo
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ")
        if nome:
            objetivos.append({
                "id": f"objetivo:herois:{slug(nome)}", "tipo": "objetivo_heroico", "nome": nome,
                "fonte": FONTE, "versao": "1.1", "pagina": cur["pg"] + 1,
                "descricao": dehyph(juntar(cur["desc"])).strip(),
                "beneficio": dehyph(juntar(cur["beneficio"])).strip(),
                "penalidade": dehyph(juntar(cur["penalidade"])).strip(),
                "conclusao": dehyph(juntar(cur["conclusao"])).strip(),
            })
        cur = None; campo = None

    for s in spans:
        # spans DENTRO de uma caixa saem do fluxo principal (viram sidebar)
        if s["box"] is not None:
            caixas.setdefault(s["box"], []).append(s)
            continue
        t = s["text"]; z = s["size"]
        if s["ss"]:
            continue
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["t20"] and 19 <= z < 24:              # cabeçalho 21pt (overview/rules)
            if cur is None:
                intro.append(t)
            continue
        if s["t20"] and 13 <= z < 19:              # nome de objetivo (16pt)
            fecha()
            cur = {"nome": [t], "pg": s["pg"], "desc": [],
                   "beneficio": [], "penalidade": [], "conclusao": []}
            campo = "desc"
            continue
        if s["ios"]:
            if dropcap:
                t = dropcap + t.lstrip(); dropcap = ""
            low = dehyph(t).lower()
            if s["bold"] and cur is not None:
                achou = next((dst for key, dst in CAMPO if low.startswith(key)), None)
                if achou:
                    campo = achou
                    continue
            if cur is not None:
                cur[campo].append(t)
            else:
                intro.append(t)
    fecha()

    # monta as caixas (sidebars): título = 1º span T20/negrito grande; corpo = resto
    sidebars = []
    for (pg, _), sps in caixas.items():
        titulo, corpo = "", []
        for s in sps:
            if not titulo and (s["ss"] or s["t20"] or s["bold"]) and s["size"] >= 12:
                titulo = s["text"]
            else:
                corpo.append(s["text"])
        if corpo:
            sidebars.append({"titulo": dehyph(titulo).strip(),
                             "texto": dehyph(juntar(corpo)).strip(), "pagina": pg + 1})

    banco = {
        "fonte": FONTE, "livro": "Heróis de Arton", "secao": "Objetivos Heroicos",
        "pagina": PG_INI, "total": len(objetivos),
        "introducao": dehyph(juntar(intro)).strip(),
        "objetivos": objetivos,
        "regras_extra": sidebars,
    }
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(objetivos)} objetivos -> {OUT.name}")
    print(f"  intro {len(banco['introducao'])}c · {len(sidebars)} caixa(s): "
          f"{[s['titulo'] for s in sidebars]}\n")
    for o in objetivos:
        print(f"  {o['nome']:<14} pg{o['pagina']} | desc {len(o['descricao']):>3}c "
              f"ben {len(o['beneficio']):>3}c pen {len(o['penalidade']):>3}c con {len(o['conclusao']):>3}c")


if __name__ == "__main__":
    main()
