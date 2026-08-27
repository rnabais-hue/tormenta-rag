# -*- coding: utf-8 -*-
r"""Extração das VARIANTES DE CLASSE DIVINA — *Deuses de Arton* (Cap. 1, págs 14–34).

1º recorte do 4º livro de expansão (`fonte="deuses-arton"`). Variantes de classe por deus:
**Sacerdote de X** (clérigo devoto, 20), **Druida de X** (6), **Paladino de X** (9). Cada
uma = nome "Classe de Deus" (Tormenta20 ~21pt) + habilidades nomeadas (rótulo negrito
IowanOldStyle terminando em "." + efeito). `tipo="devoto_variante"`, com `classe` e `deus`.

Layout = Heróis/núcleo. Duas colunas → ordenação por bloco; caixas/pull-quotes (SourceSansPro)
e drop-caps fora do fluxo. Ignora "Autoridade Eclesiástica" (só nomes de deus, sem "Classe de").
Saída: dados/devotos_deuses.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = Path(__file__).parent / "dados" / "devotos_deuses.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"
PG_INI, PG_FIM = 14, 34
RE_VAR = re.compile(r"^\s*(Sacerdote|Druida|Paladino)\s+d[eo]\s+(.+)$", re.I)


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


def cap_deus(s):
    def capw(w):
        return "-".join(p.capitalize() if p.islower() else p for p in w.split("-"))
    return " ".join(capw(w) if w[:1].islower() or "-" in w else w for w in dehyph(s).split())


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
    variantes = []
    cur = None
    dropcap = ""
    hdr21 = []

    def fecha():
        nonlocal cur
        if not cur:
            return
        habs = []
        for lbl, ef in cur["habs"]:
            lbl = dehyph(lbl).strip().rstrip(".")
            ef = dehyph(juntar(ef)).strip()
            if lbl and ef:
                habs.append({"nome": lbl, "efeito": ef})
        if cur["classe"] and cur["deus"] and habs:
            variantes.append({
                "id": f"devoto:deuses:{slug(cur['classe'])}-{slug(cur['deus'])}",
                "tipo": "devoto_variante", "classe": cur["classe"], "deus": cur["deus"],
                "nome": f"{cur['classe']} de {cur['deus']}", "fonte": FONTE, "versao": "1.0",
                "pagina": cur["pg"] + 1, "habilidades": habs,
            })
        cur = None

    def flush_hdr(pg):
        nonlocal cur
        if not hdr21:
            return
        nome = dehyph(juntar(hdr21)).strip(); hdr21.clear()
        m = RE_VAR.match(nome)
        if m:
            fecha()
            cur = {"classe": m.group(1).capitalize(), "deus": cap_deus(m.group(2)),
                   "habs": [], "pg": pg}
        # cabeçalho 21pt que não casa (ex.: "Autoridade Eclesiástica") → encerra variante
        elif cur is not None:
            fecha()

    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            else:                                  # título de seção grande → encerra a variante
                flush_hdr(s["pg"]); fecha()        # (ex.: "Autoridades Divinas" após o Panteão)
            continue
        if s["t20"] and 19 <= z < 24:              # nome de variante (21pt, pode partir)
            hdr21.append(t)
            continue
        if hdr21:
            flush_hdr(s["pg"])
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if cur is None:
            continue
        if s["bold"] and re.match(r"^[A-ZÀ-Ú][\wÀ-ÿ ()\-]{1,30}\.$", dehyph(t).strip()):
            cur["habs"].append([t, []])            # novo rótulo de habilidade
        elif cur["habs"]:
            cur["habs"][-1][1].append(t)
    flush_hdr(PG_FIM); fecha()

    from collections import Counter
    porc = Counter(v["classe"] for v in variantes)
    banco = {"fonte": FONTE, "livro": "Deuses de Arton", "secao": "Variantes de Classe Divina",
             "pagina": PG_INI, "total": len(variantes), "por_classe": dict(porc), "variantes": variantes}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(variantes)} variantes -> {OUT.name}  {dict(porc)}\n")
    for v in variantes:
        print(f"  {v['nome']:<28} pg{v['pagina']} | {len(v['habilidades'])} habs: "
              f"{', '.join(h['nome'] for h in v['habilidades'])[:60]}")


if __name__ == "__main__":
    main()
