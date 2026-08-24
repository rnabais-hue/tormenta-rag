# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das CLASSES VARIANTES de *Heróis de Arton* (Cap. 1, págs 24–47).

14 variantes (Alquimista, Atleta, Burguês, Duelista, Ermitão, Inovador, Machado de
Pedra, Magimarcialista, Necromante, Santo, Seteiro, Usurpador, Vassalo, Ventanista).
Cada uma é uma classe alternativa com a MESMA estrutura da nova classe Treinador:
nome Tormenta20 27pt -> "Características de Classe" (21pt) -> "Habilidades de Classe" (21pt)
-> Tabela de progressão (IowanOldStyle-Bold "Tabela 1-N", que serve de fim das habilidades).

Schema compatível com classes.json: nome, resumo, caracteristicas{pv,pm,pericias,
proficiencias}, habilidades[{nome,efeito}], variante=True. Saída: dados/variantes_herois.json.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "variantes_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PAG_INI, PAG_FIM = 24, 47
BOLD = 2**4
NOMES = {"Alquimista", "Atleta", "Burguês", "Duelista", "Ermitão", "Inovador",
         "Machado de Pedra", "Magimarcialista", "Necromante", "Santo", "Seteiro",
         "Usurpador", "Vassalo", "Ventanista"}


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def coletar(doc):
    out = []
    for pg in range(PAG_INI, PAG_FIM + 1):
        page = doc[pg - 1]; W, H = page.rect.width, page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            bx0, by0 = b["bbox"][0], b["bbox"][1]
            bcol = 0 if bx0 < W * 0.40 else 1
            for li, l in enumerate(b["lines"]):
                for si, s in enumerate(l["spans"]):
                    tx = s["text"]
                    if not tx.strip() or s["size"] <= 8.2:
                        continue
                    if "SourceSans" in s["font"] or "Spirals" in s["font"] or "LetterGothic" in s["font"]:
                        continue
                    y = s["bbox"][1]
                    if (y < H * 0.06 or y > H * 0.94) and s["size"] < 20:
                        continue
                    dc = "Tormenta20" in s["font"] and s["size"] >= 36 and len(tx.strip()) <= 2
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "size": s["size"], "font": s["font"], "text": tx,
                                "bold": bool(s["flags"] & BOLD) or "Bold" in s["font"],
                                "dropcap": dc})
    out.sort(key=lambda r: r["key"])
    return [s for s in out if not s["dropcap"]]


def eh_nome_variante(spans, i):
    """Âncora = Tormenta20 ~27pt (24-32). Junta spans consecutivos e confere NOMES."""
    s = spans[i]
    if not ("Tormenta20" in s["font"] and 24 <= s["size"] < 34):
        return None
    partes = [s["text"]]; j = i + 1
    while j < len(spans) and "Tormenta20" in spans[j]["font"] and 24 <= spans[j]["size"] < 34 \
            and spans[j]["pg"] == s["pg"]:
        partes.append(spans[j]["text"]); j += 1
    nome = dehyph(" ".join(partes))
    return (nome, j) if nome in NOMES else None


def eh_secao(s):
    return "Tormenta20" in s["font"] and 19 <= s["size"] < 24


def eh_tabela(s):
    return s["bold"] and bool(re.match(r"Tabela\s+\d", dehyph(s["text"])))


def parse_caracteristicas(spans):
    txt = dehyph(" ".join(s["text"] for s in spans if not eh_secao(s)))
    car = {}
    for lab, key in [("Pontos de Vida", "pv"), ("Pontos de Mana", "pm"),
                     ("Perícias", "pericias"), ("Proficiências", "proficiencias")]:
        m = re.search(re.escape(lab) + r"[.:]?\s*(.+?)(?=Pontos de|Perícias|Proficiências|$)", txt)
        if m:
            car[key] = m.group(1).strip().rstrip(".")
    return car


def parse_habilidades(spans):
    # A tabela de progressão fica no MEIO da lista (base de uma coluna), com mais
    # habilidades na coluna seguinte. Em vez de parar, PULA só a coluna da tabela.
    habs, cur = [], None
    skip = None                         # (pg, bcol) da coluna ocupada pela tabela
    for s in spans:
        if eh_secao(s):
            break
        if eh_tabela(s):
            skip = (s["pg"], s["key"][1]); cur = None; continue
        if skip is not None:
            if (s["pg"], s["key"][1]) == skip:
                continue                # ainda na coluna da tabela → pula
            skip = None                 # mudou de coluna/página → retoma
        if s["bold"]:
            if cur is None or cur["_ef"].strip():
                cur = {"nome": "", "_ef": ""}; habs.append(cur)
            cur["nome"] += s["text"]
        else:
            if cur is None:
                cur = {"nome": "", "_ef": ""}; habs.append(cur)
            cur["_ef"] += s["text"]
    out = []
    for h in habs:
        nm = dehyph(h["nome"]).rstrip(". ")
        ef = dehyph(h["_ef"])
        if nm and ef and len(nm) <= 40:
            out.append({"nome": nm, "efeito": ef})
    return out


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar(doc)

    # âncoras de variante
    anchors = []
    i = 0
    while i < len(spans):
        hit = eh_nome_variante(spans, i)
        if hit:
            nome, j = hit
            anchors.append((i, j, nome, spans[i]["pg"]))
            i = j
        else:
            i += 1

    variantes = []
    for a, (i0, j0, nome, pg) in enumerate(anchors):
        fim = anchors[a + 1][0] if a + 1 < len(anchors) else len(spans)
        bloco = spans[j0:fim]
        # localizar seções dentro do bloco
        idx_car = idx_hab = None
        for k, s in enumerate(bloco):
            if eh_secao(s):
                t = dehyph(s["text"]).lower()
                if "caracter" in t and idx_car is None:
                    idx_car = k
                elif "habilidad" in t and idx_hab is None:
                    idx_hab = k
        resumo = dehyph(" ".join(s["text"] for s in bloco[:idx_car] if not eh_secao(s)))[:600] if idx_car else ""
        car = parse_caracteristicas(bloco[idx_car:idx_hab]) if idx_car is not None else {}
        habs = parse_habilidades(bloco[idx_hab + 1:]) if idx_hab is not None else []
        variantes.append({
            "id": f"classe:herois:variante:{slug(nome)}", "tipo": "classe", "subtipo": "variante",
            "nome": nome, "fonte": FONTE, "versao": "1.1", "pagina": pg, "variante": True,
            "resumo": resumo, "caracteristicas": car, "habilidades": habs,
        })

    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "total": len(variantes), "variantes": variantes}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(variantes)} classes variantes -> {OUT.name}\n")
    for v in variantes:
        print(f"  - {v['nome']:<18} pg{v['pagina']:>3} | {len(v['habilidades'])} habs | "
              f"caract: {list(v['caracteristicas'].keys())}")


if __name__ == "__main__":
    main()
