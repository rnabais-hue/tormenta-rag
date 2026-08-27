# -*- coding: utf-8 -*-
r"""Extração dos MENORES do Cap. 1 — *Deuses de Arton* (fecha o capítulo).

`fonte="deuses-arton"`. Quatro blocos pequenos e heterogêneos:
  • **Autoridade Eclesiástica** (24–25): por deus, o título/hierarquia do clero — rótulo
    negrito (deus) + texto. → `tipo="autoridade_eclesiastica"`.
  • **Outros Devotos** (36–37): por deus, quais Raças/Classes podem cultuá-lo — nome do deus
    (Tormenta20 ~16pt) + "Raças."/"Classes." → `tipo="devotos_permitidos"`.
  • **Nova Linhagem: Abençoada** (35): linhagem com sangue divino — habilidades nomeadas.
    → `tipo="linhagem"`.
  • **Suraggel Variantes** (38–39): heranças do Suraggel — "• Herança de X." + efeito.
    → `tipo="heranca_suraggel"`.

Saída: dados/devotos_menores_deuses.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = Path(__file__).parent / "dados" / "devotos_menores_deuses.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"
DEUSES = {"aharadak", "allihanna", "arsenal", "azgher", "hyninn", "kallyadranoch", "khalmyr",
          "lena", "lin-wu", "marah", "megalokk", "nimb", "oceano", "sszzaas", "tanna-toh",
          "tenebra", "thwor", "thyatis", "valkaria", "wynna"}


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


def coletar_spans(doc, p0, p1):
    out = []
    for pg in range(p0 - 1, p1):
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
                    if "LetterGothic" in s["font"]:
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


def parse_outros_devotos(doc):
    """Nome do deus (Tormenta20 16pt) + 'Raças.'/'Classes.' (rótulos negrito)."""
    spans = coletar_spans(doc, 36, 37)
    regs = []
    cur = None; campo = None
    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and 13 <= z < 20 and slug(dehyph(t)) in DEUSES:
            if cur:
                regs.append(cur)
            cur = {"deus": dehyph(t).strip(), "racas": [], "classes": []}; campo = None
            continue
        if not s["ios"] or cur is None:
            continue
        low = dehyph(t).lower()
        if s["bold"] and low.startswith("raça"):
            campo = "racas"; continue
        if s["bold"] and low.startswith("classe"):
            campo = "classes"; continue
        if campo:
            cur[campo].append(t)
    if cur:
        regs.append(cur)
    out = []
    for r in regs:
        racas = dehyph(juntar(r["racas"])).strip(" .")
        classes = dehyph(juntar(r["classes"])).strip(" .")
        if r["deus"] and (racas or classes):
            out.append({"id": f"devotos-permitidos:deuses:{slug(r['deus'])}", "tipo": "devotos_permitidos",
                        "deus": r["deus"], "racas": racas, "classes": classes,
                        "fonte": FONTE, "versao": "1.0", "pagina": 36})
    return out


def parse_autoridade(doc):
    """Rótulo negrito = deus (ex.: 'Aharadak.') + texto do título/hierarquia do clero."""
    spans = coletar_spans(doc, 24, 25)
    regs = []
    cur = None
    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 24:
            continue
        if s["ios"] and s["bold"] and re.match(r"^[A-ZÀ-Ú][\wÀ-ÿ\-]{2,20}\.$", dehyph(t).strip()) \
                and slug(dehyph(t).rstrip(".")) in DEUSES:
            if cur:
                regs.append(cur)
            cur = {"deus": dehyph(t).rstrip(". ").strip(), "texto": []}
            continue
        if s["ios"] and cur is not None:
            cur["texto"].append(t)
    if cur:
        regs.append(cur)
    out = []
    for r in regs:
        txt = dehyph(juntar(r["texto"])).strip()
        if r["deus"] and txt:
            out.append({"id": f"autoridade-eclesiastica:deuses:{slug(r['deus'])}",
                        "tipo": "autoridade_eclesiastica", "deus": r["deus"], "texto": txt,
                        "fonte": FONTE, "versao": "1.0", "pagina": 24})
    return out


def parse_abencoada(doc):
    """Linhagem única (pág 35) + habilidades nomeadas (rótulo negrito)."""
    spans = coletar_spans(doc, 35, 35)
    resumo, habs = [], []
    dropcap = ""
    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 36 and len(t.strip()) == 1 and t.strip().isalpha():
            dropcap = t.strip(); continue
        if s["t20"] and z >= 15:
            continue                 # títulos "Linhagem Abençoada" etc.
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        # rótulos da Abençoada são ITÁLICOS com bullet ("• Básica."), não negrito
        m = re.match(r"^•\s*([A-ZÀ-Ú][\wÀ-ÿ ()\-]{1,30})\.$", dehyph(t).strip())
        if m and (s["bold"] or "Italic" in s["font"]):
            habs.append([m.group(1), []])
        elif habs:
            habs[-1][1].append(t)
        else:
            resumo.append(t)
    H = [{"nome": dehyph(n).rstrip("."), "efeito": dehyph(juntar(e)).strip()} for n, e in habs]
    H = [h for h in H if h["efeito"]]
    return {"tipo": "linhagem", "nome": "Linhagem Abençoada", "fonte": FONTE, "versao": "1.0",
            "pagina": 35, "resumo": dehyph(juntar(resumo)).strip(), "habilidades": H}


def parse_suraggel(doc):
    """'• Herança de X.' (rótulo negrito) + efeito."""
    spans = coletar_spans(doc, 38, 39)
    heran = []
    cur = None
    modo = False
    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and 19 <= z < 24 and "habilidade" in dehyph(t).lower():
            modo = True; continue
        if not modo or not s["ios"]:
            continue
        m = re.match(r"^•?\s*(Herança de [\wÀ-ÿ\-'’ ]+?)\.\s*(.*)$", dehyph(t).strip())
        if s["bold"] and m:
            if cur:
                heran.append(cur)
            cur = {"nome": m.group(1).strip(), "efeito": [m.group(2)] if m.group(2) else []}
            continue
        if cur is not None:
            cur["efeito"].append(t)
    if cur:
        heran.append(cur)
    return [{"id": f"heranca-suraggel:deuses:{slug(h['nome'])}", "tipo": "heranca_suraggel",
             "nome": h["nome"], "efeito": dehyph(juntar(h["efeito"])).strip(),
             "fonte": FONTE, "versao": "1.0", "pagina": 38}
            for h in heran if dehyph(juntar(h["efeito"])).strip()]


def main():
    doc = pymupdf.open(str(PDF))
    outros = parse_outros_devotos(doc)
    autor = parse_autoridade(doc)
    abenc = parse_abencoada(doc)
    surag = parse_suraggel(doc)
    banco = {"fonte": FONTE, "livro": "Deuses de Arton", "secao": "Cap. 1 — menores",
             "outros_devotos": outros, "autoridade_eclesiastica": autor,
             "linhagem_abencoada": abenc, "heranca_suraggel": surag}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"outros_devotos={len(outros)} autoridade={len(autor)} "
          f"abencoada_habs={len(abenc['habilidades'])} suraggel_herancas={len(surag)} -> {OUT.name}\n")
    print("  Outros Devotos:", ", ".join(o["deus"] for o in outros))
    print("  Autoridade:", ", ".join(a["deus"] for a in autor))
    print("  Suraggel:", ", ".join(h["nome"] for h in surag))


if __name__ == "__main__":
    main()
