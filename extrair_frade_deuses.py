# -*- coding: utf-8 -*-
r"""Extração da NOVA CLASSE: FRADE — *Deuses de Arton* (Cap. 1, págs 40–43).

Classe completa (`fonte="deuses-arton"`). Estrutura padrão (como a Treinador do Heróis):
"Características de Classe" (PV/PM/Perícias/Proficiências) → "Habilidades de Classe"
(habilidades nomeadas: rótulo negrito + efeito). Schema compatível com classes.json.
Saída: dados/frade_deuses.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = Path(__file__).parent / "dados" / "frade_deuses.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"
PG_INI, PG_FIM = 40, 43
CARAC = {"pontos de vida": "pv", "pontos de mana": "pm", "perícias": "pericias",
         "proficiências": "proficiencias"}


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
                    if "LetterGothic" in s["font"]:
                        continue                       # "NOVA CLASSE" selo
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
    resumo = []
    carac_txt = []
    habilidades = []
    modo = "resumo"          # resumo → caracteristicas → habilidades
    dropcap = ""
    hdr21 = []

    def flush_hdr():
        nonlocal modo
        if not hdr21:
            return
        nome = dehyph(juntar(hdr21)).strip().lower(); hdr21.clear()
        if "características" in nome:
            modo = "caracteristicas"
        elif "habilidades" in nome:
            modo = "habilidades"

    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["t20"] and 19 <= z < 24:
            hdr21.append(t)
            continue
        if hdr21:
            flush_hdr()
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        # habilidade nova: rótulo negrito curto terminando em "."
        if modo == "habilidades" and s["bold"] and re.match(r"^[A-ZÀ-Ú][\wÀ-ÿ ()\-]{1,30}\.$", dehyph(t).strip()):
            habilidades.append({"nome": dehyph(t).strip().rstrip("."), "efeito": []})
            continue
        # corpo
        if modo == "resumo":
            resumo.append(t)
        elif modo == "caracteristicas":
            carac_txt.append(t)
        elif modo == "habilidades" and habilidades:
            habilidades[-1]["efeito"].append(t)
    flush_hdr()

    ctxt = dehyph(juntar(carac_txt)).strip()
    def campo(rot, prox):
        m = re.search(rf"{rot}\.\s*(.*?)(?=\s*(?:{prox})\.|$)", ctxt, re.I | re.S)
        return dehyph(m.group(1)).strip() if m else ""
    caract = {
        "pv": campo("Pontos de Vida", "Pontos de Mana"),
        "pm": campo("Pontos de Mana", "Perícias"),
        "pericias": campo("Perícias", "Proficiências"),
        "proficiencias": campo("Proficiências", "$"),
    }
    habs = [{"nome": h["nome"], "efeito": dehyph(juntar(h["efeito"])).strip()} for h in habilidades]
    habs = [h for h in habs if h["efeito"]]
    banco = {"fonte": FONTE, "livro": "Deuses de Arton", "tipo": "classe", "nome": "Frade",
             "subtipo": "classe_nova", "pagina": PG_INI, "versao": "1.0",
             "resumo": dehyph(juntar(resumo)).strip()[:800],
             "caracteristicas": caract, "caracteristicas_texto": ctxt, "habilidades": habs}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Frade -> {OUT.name}\n  caracteristicas: {list(caract)}\n  {len(habs)} habilidades: "
          f"{', '.join(h['nome'] for h in habs)}")


if __name__ == "__main__":
    main()
