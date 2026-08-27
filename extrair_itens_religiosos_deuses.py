# -*- coding: utf-8 -*-
r"""Extração dos EQUIPAMENTOS RELIGIOSOS + ITENS LITÚRGICOS — *Deuses de Arton* (Cap. 1, 50–61).

`fonte="deuses-arton"`. Dois blocos:
  • **Equipamentos Religiosos** (50–56): itens comuns por subcategoria (Equipamento de Aventura,
    Ferramentas, Vestuário, Esotéricos, Alquímicos, Alimentação, Serviços, Itens Superiores) —
    rótulo negrito terminando em "." + descrição → `tipo="equipamento_religioso"`.
  • **Itens Litúrgicos** (57–61): itens mágicos religiosos — nome Tormenta20 ~16pt + descrição →
    `tipo="item_liturgico"`.

Máquina header-driven (reusa itens_magicos/arsenal_menor). Saída: dados/itens_religiosos_deuses.json.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = Path(__file__).parent / "dados" / "itens_religiosos_deuses.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"
PG_INI, PG_FIM = 50, 61
RE_LBL = re.compile(r"^[A-ZÀ-Ú][\wÀ-ÿ ()\-']{0,32}\.$")
SUBCATS = {"equipamento de aventura", "ferramentas", "vestuario", "esotericos", "alquimicos",
           "preparados", "catalisadores", "alimentacao", "servicos", "itens superiores", "melhorias"}


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


def _norm(s):
    return slug(s).replace("-", " ")


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
                    if not s["text"].strip() or "SourceSans" in s["font"] or "Spirals" in s["font"]:
                        continue
                    sx, sy = s["bbox"][0], s["bbox"][1]
                    if (sy < H * 0.06 or sy > H * 0.94) and s["size"] < 24:
                        continue
                    if any(_dentro(r, sx, sy) for r in boxes):
                        continue
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "size": s["size"], "font": s["font"],
                                "t20": "Tormenta20" in s["font"], "ios": "IowanOldStyle" in s["font"],
                                "bold": bool(s["flags"] & (2**4)) or "Bold" in s["font"], "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)
    itens = []
    modo = "equip"           # equip (bold-label) | liturgico (16pt nome)
    subcat = "Equipamento de Aventura"
    cur = None
    hdr, hdr_last = [], 0.0
    dropcap = ""
    ultima_nome = False

    def fecha():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ").strip()
        desc = dehyph(juntar(cur["desc"])).strip()
        if nome and desc:
            itens.append({"id": f"{cur['tipo']}:deuses:{slug(nome)}", "tipo": cur["tipo"],
                          "categoria": cur["cat"], "nome": nome, "fonte": FONTE, "versao": "1.0",
                          "pagina": cur["pg"] + 1, "descricao": desc})
        cur = None

    def flush_hdr(pg):
        nonlocal modo, subcat, cur
        if not hdr:
            return
        nome = dehyph(juntar(hdr)).strip(); hdr.clear()
        nn = _norm(nome)
        if "itens liturgicos" in nn:
            fecha(); modo = "liturgico"
            return
        if nn in SUBCATS:
            fecha(); modo = "equip"; subcat = nome
            return
        # outros títulos grandes (Equipamentos Religiosos etc.) → ignora

    for s in spans:
        t = s["text"]; z = s["size"]
        if modo != "liturgico" and s["pg"] >= 56:   # pág 57+ = Itens Litúrgicos (16pt-nome)
            fecha(); modo = "liturgico"
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            else:
                flush_hdr(s["pg"])
            continue
        if s["t20"] and 19 <= z < 24:              # subcategoria (27pt) ou "Itens Litúrgicos"
            if hdr and abs(z - hdr_last) > 3:
                flush_hdr(s["pg"])
            hdr.append(t); hdr_last = z
            continue
        if s["t20"] and 13 <= z < 19:              # nome 16pt (item litúrgico)
            if modo == "liturgico":
                _sem = cur is not None and not cur["desc"]
                if cur is not None and ultima_nome and (t[:1].islower() or _sem):
                    cur["nome"].append(t); continue
                fecha()
                cur = {"nome": [t], "desc": [], "pg": s["pg"], "tipo": "item_liturgico", "cat": "Itens Litúrgicos"}
                ultima_nome = True
                continue
            continue
        if hdr:
            flush_hdr(s["pg"])
        ultima_nome = False
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if modo == "equip":
            if s["bold"] and RE_LBL.match(dehyph(t).strip()):
                fecha()
                cur = {"nome": [t], "desc": [], "pg": s["pg"], "tipo": "equipamento_religioso", "cat": subcat}
            elif cur is not None:
                cur["desc"].append(t)
        elif cur is not None:
            cur["desc"].append(t)
    fecha()

    from collections import Counter
    banco = {"fonte": FONTE, "livro": "Deuses de Arton", "secao": "Equipamentos Religiosos + Itens Litúrgicos",
             "pagina": PG_INI, "total": len(itens),
             "por_tipo": dict(Counter(i["tipo"] for i in itens)),
             "por_categoria": dict(Counter(i["categoria"] for i in itens)), "itens": itens}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(itens)} itens -> {OUT.name}  {banco['por_tipo']}\n")
    for cat, n in banco["por_categoria"].items():
        print(f"  {cat:<26} {n}")


if __name__ == "__main__":
    main()
