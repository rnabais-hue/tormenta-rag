# -*- coding: utf-8 -*-
r"""Extração dos NOVOS PODERES CONCEDIDOS — *Deuses de Arton* (Cap. 1, págs 44–49).

Poderes que um devoto pode receber de seu deus (`fonte="deuses-arton"`). Cada um:
  • nome — Tormenta20 ~16pt (pode ocupar 2 linhas);
  • deus — tag Tormenta20 ~11pt logo após o nome (o deus concedente);
  • efeito — corpo IowanOldStyle.
`tipo="poder"`, `categoria="concedido"`, campo `deuses` (lista, p/ compatibilidade com os
poderes concedidos do núcleo). Saída: dados/poderes_concedidos_deuses.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = Path(__file__).parent / "dados" / "poderes_concedidos_deuses.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"
PG_INI, PG_FIM = 44, 49
STOP = re.compile(r"^(Novos Poderes|Poderes Concedidos)", re.I)


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
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)
    poderes = []
    cur = None
    dropcap = ""
    ultima_nome = False

    def fecha():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ").strip()
        efeito = dehyph(juntar(cur["efeito"])).strip()
        deus = dehyph(juntar(cur["deus"])).strip()
        deuses = [d.strip() for d in re.split(r"\s*(?:[,;]|\be\b)\s*", deus) if d.strip()]
        if nome and not STOP.match(nome) and efeito:
            poderes.append({
                "id": f"poder-concedido:deuses:{slug(nome)}", "tipo": "poder", "categoria": "concedido",
                "nome": nome, "deuses": deuses, "fonte": FONTE, "versao": "1.0",
                "pagina": cur["pg"] + 1, "efeito": efeito,
            })
        cur = None

    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["t20"] and 13 <= z < 20:              # nome de poder (16pt; pode partir)
            _sem = cur is not None and not (cur["deus"] or cur["efeito"])
            if cur is not None and ultima_nome and (t[:1].islower() or _sem):
                cur["nome"].append(t); continue
            fecha()
            cur = {"nome": [t], "deus": [], "efeito": [], "pg": s["pg"]}
            ultima_nome = True
            continue
        ultima_nome = False
        if s["t20"] and 10 <= z < 13:              # tag de DEUS
            if cur is not None:
                cur["deus"].append(t)
            continue
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if cur is not None:
            cur["efeito"].append(t)
    fecha()

    from collections import Counter
    banco = {"fonte": FONTE, "livro": "Deuses de Arton", "secao": "Novos Poderes Concedidos",
             "pagina": PG_INI, "total": len(poderes),
             "por_deus": dict(Counter(p["deuses"][0] if p["deuses"] else "—" for p in poderes)),
             "poderes": poderes}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(poderes)} poderes concedidos -> {OUT.name}\n")
    for p in poderes:
        print(f"  {p['nome']:<26} [{(p['deuses'][0] if p['deuses'] else '—')[:14]:<14}] pg{p['pagina']} | {len(p['efeito'])}c")


if __name__ == "__main__":
    main()
