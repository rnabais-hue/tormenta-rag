# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA dos PAPÉIS NO GRUPO — *Heróis de Arton* (Cap. 4, págs 296–297).

Regra opcional (fonte="herois-arton"). Cada "papel" é uma função que um jogador
assume na mesa (Advogado, Arquivista, …), com uma descrição e um **benefício
mecânico** ("Se for o X, você recebe +1 em Diplomacia."). Entidade nova:
`tipo="papel_grupo"`.

Layout (reusa o método de extrair_origens_herois.py): duas colunas → ordenação por
bloco (bcol = 0 se x0 < 40% da largura, senão 1). Corpo IowanOldStyle; nome em
Tormenta20 ~21pt; título de seção 66pt e drop-cap 78pt (Tormenta20 ≥24) descartados.
Dentro de cada papel: corpo **não-negrito** = descrição; corpo **negrito** = benefício.

Saída: dados/papeis_grupo_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "papeis_grupo_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
BOLD = 2**4
PG_INI, PG_FIM = 296, 297            # 1-based, inclusive
SECAO = re.compile(r"^Pap[eé]is\s+no\s+grupo$", re.I)


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def juntar(parts):
    """Cada span é uma LINHA. Junta reconstruindo o fluxo: hífen de quebra
    (letra-'-' no fim da linha) → remove o hífen e cola; senão insere um espaço
    quando nenhum dos lados já tem separador. Resolve 'responsabi-lidade' e o
    'tesoureiro.Bens' (linhas sem espaço final)."""
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


def coletar_spans(doc):
    out = []
    for pg in range(PG_INI - 1, PG_FIM):
        page = doc[pg]; W, H = page.rect.width, page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            bx0, by0 = b["bbox"][0], b["bbox"][1]
            bcol = 0 if bx0 < W * 0.40 else 1
            for li, l in enumerate(b["lines"]):
                for si, s in enumerate(l["spans"]):
                    if not s["text"].strip() or s["size"] <= 8.4:
                        continue
                    if "SourceSans" in s["font"] or "Spirals" in s["font"]:
                        continue
                    y = s["bbox"][1]
                    if (y < H * 0.06 or y > H * 0.94) and s["size"] < 24:
                        continue
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "size": s["size"], "font": s["font"],
                                "bold": bool(s["flags"] & BOLD) or "Bold" in s["font"],
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def tipo_span(s):
    t20 = "Tormenta20" in s["font"]
    z = s["size"]
    if t20 and z >= 24:
        return "secao"          # "Papéis no grupo" (66pt) / drop-cap (78pt) — ignora
    if t20 and 19 <= z < 24:
        return "nome"
    if "IowanOldStyle" in s["font"]:
        return "corpo"
    return "ign"


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    papeis = []
    intro = []
    cur = None
    dropcap = ""       # letra capitular (Tormenta20 ≥36pt, 1 letra) a religar ao corpo

    def fecha():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ")
        if not nome or SECAO.match(nome):
            cur = None; return
        rec = {
            "id": f"papel:herois:{slug(nome)}", "tipo": "papel_grupo", "nome": nome,
            "fonte": FONTE, "versao": "1.1", "pagina": cur["pg"] + 1,
            "descricao": dehyph(juntar(cur["desc"])).strip(),
            "beneficio": dehyph(juntar(cur["benef"])).strip(),
        }
        papeis.append(rec)
        cur = None

    for s in spans:
        tp = tipo_span(s)
        if tp in ("secao", "ign"):
            t = s["text"].strip()
            if tp == "secao" and s["size"] >= 36 and len(t) == 1 and t.isalpha():
                dropcap = t                    # letra capitular → religa ao próximo corpo
            continue
        txt = s["text"]
        if tp == "nome":
            fecha()
            cur = {"nome": [txt], "pg": s["pg"], "desc": [], "benef": []}
            dropcap = ""
            continue
        # corpo
        if dropcap:
            txt = dropcap + txt.lstrip(); dropcap = ""
        if cur is None:
            intro.append(txt)                  # texto de abertura (antes do 1º papel)
        elif s["bold"]:
            cur["benef"].append(txt)
        else:
            cur["desc"].append(txt)
    fecha()

    banco = {
        "fonte": FONTE, "livro": "Heróis de Arton", "secao": "Papéis no Grupo",
        "pagina": PG_INI, "total": len(papeis),
        "introducao": dehyph(juntar(intro)).strip(),
        "papeis": papeis,
    }
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(papeis)} papéis -> {OUT.name}\n")
    print(f"  intro: {len(banco['introducao'])} chars\n")
    for p in papeis:
        print(f"  - {p['nome']:<16} pg{p['pagina']:>3} | desc {len(p['descricao']):>4}c "
              f"| benef: {p['beneficio'][:60]}")


if __name__ == "__main__":
    main()
