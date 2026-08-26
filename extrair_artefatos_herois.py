# -*- coding: utf-8 -*-
r"""Extração dos ARTEFATOS — *Heróis de Arton* (Cap. 3, págs 276–279).

8 artefatos lendários (A Armadura de Crânio Negro, O Escudo Impérvio, O Kailash, Lorde
Enxame, O Monóculo da Verdade, Slash Calliber, A Vingança de Khinlanas, Wakizashi da Morte).
Cada um = nome Tormenta20 ~21pt (às vezes partido em 2 spans) + descrição (lore + poderes,
corpo IowanOldStyle). `tipo="artefato"`, `fonte="herois-arton"`.

Layout: duas colunas (ordenação por bloco); splash "Artefatos" (58pt) descartado; drop-cap
religado; caixas fora do fluxo via get_drawings(). Saída: dados/artefatos_herois.json.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "artefatos_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 276, 279


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    return re.sub(r"\s+", " ", s).strip()


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
                        continue
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "size": s["size"], "font": s["font"],
                                "t20": "Tormenta20" in s["font"], "ios": "IowanOldStyle" in s["font"],
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)
    artefatos = []
    hdr, cur, dropcap = [], None, ""

    def fecha():
        nonlocal cur
        if cur:
            nome = dehyph(juntar(cur["nome"])).strip()
            desc = dehyph(juntar(cur["desc"])).strip()
            if nome and desc:
                artefatos.append({"id": f"artefato:herois:{slug(nome)}", "tipo": "artefato",
                                  "nome": nome, "fonte": FONTE, "versao": "1.1",
                                  "pagina": cur["pg"] + 1, "descricao": desc})
        cur = None

    def flush_hdr(pg):
        nonlocal cur
        if not hdr:
            return
        fecha()
        cur = {"nome": list(hdr), "desc": [], "pg": pg}
        hdr.clear()

    for s in spans:
        z = s["size"]; t = s["text"]
        if s["t20"] and z >= 40:                 # splash "Artefatos" (58pt) ou drop-cap
            tt = t.strip()
            if len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["t20"] and 19 <= z < 40:            # nome de artefato (21pt, pode partir)
            hdr.append(t)
            continue
        if hdr:
            flush_hdr(s["pg"])
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if cur is not None:
            cur["desc"].append(t)
    fecha()

    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "secao": "Artefatos",
             "pagina": PG_INI, "total": len(artefatos), "artefatos": artefatos}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(artefatos)} artefatos -> {OUT.name}\n")
    for a in artefatos:
        print(f"  {a['nome']:<28} pg{a['pagina']} | {len(a['descricao']):>5}c")


if __name__ == "__main__":
    main()
