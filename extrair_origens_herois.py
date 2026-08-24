# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das NOVAS ORIGENS de *Heróis de Arton* (Cap. 1, págs 48–55).

Livro de expansão (fonte="herois-arton"). O formato é o MESMO do núcleo
(extrair_origens.py): nome Tormenta20 ~21pt; rótulos negrito "Itens." e "Benefícios."
(perícias/poderes no formato "A, B (perícias); C, D (poderes)."); Poder Único em
Tormenta20 13–18pt. Corpo em IowanOldStyle.

Diferença: negrito por flag OU "Bold" no nome da fonte; STOP inclui o título da seção.
Saída: dados/origens_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "origens_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
BOLD = 2**4
PG_INI, PG_FIM = 48, 55             # 1-based, inclusive
STOP_NOME = re.compile(r"^(Novas?\s+Origens|Sua Própria Origem)$", re.I)


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
        return "secao"          # "Novas origens" (66pt) / drop-cap — ignora
    if t20 and 19 <= z < 24:
        return "nome"
    if t20 and 13 <= z < 18:
        return "poder"
    if "IowanOldStyle" in s["font"]:
        return "corpo"
    return "ign"


def _norm(s):
    s = dehyph(s).lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s)


def _carregar_pericias_canon():
    p = Path(__file__).parent / "dados" / "pericias.json"
    if not p.exists():
        return {}
    return {_norm(x["nome"]): x["nome"] for x in json.loads(p.read_text(encoding="utf-8"))}


_PER_CANON = _carregar_pericias_canon()


def canon_pericia(tok):
    base = re.sub(r"\s*\([^)]*\)", "", dehyph(tok)).strip()
    return _PER_CANON.get(_norm(base), base)


def parse_beneficios(txt):
    """Formato núcleo: 'A, B (perícias); C, D (poderes).' Formato Heróis (prosa):
    'Você é treinado em X, Y e Z. Além disso, ... o poder P ...'."""
    txt = dehyph(txt)
    def lista(m):
        return [x.strip(" .") for x in re.split(r"[,;]|\se\s", m) if x.strip(" .")]
    # 1) formato núcleo (tagged)
    per = re.search(r"(.+?)\s*\(perícias\)", txt)
    if per:
        pod = re.search(r"\(perícias\)\s*;?\s*(.+?)\s*\(poderes\)", txt)
        pericias = [canon_pericia(x) for x in lista(per.group(1))]
        poderes = lista(pod.group(1)) if pod else []
        return pericias, poderes
    # 2) formato Heróis (prosa): "treinado em X, Y e Z". Como a frase pode continuar
    #    ("...e, quando conduz..."), NÃO confio no stop de pontuação — filtro os tokens
    #    para só os que são PERÍCIAS CANÔNICAS reais (as 29 do jogo).
    pericias, poderes = [], []
    m = re.search(r"treinad[oa]\s+em\s+(.{0,160})", txt, re.I)
    if m:
        for tok in re.split(r"\s*(?:[,;.]|\be\b)\s*", m.group(1)):
            base = re.sub(r"\s*\([^)]*\)", "", dehyph(tok)).strip()
            if _norm(base) in _PER_CANON:
                nome_c = _PER_CANON[_norm(base)]
                if nome_c not in pericias:
                    pericias.append(nome_c)
    for pm in re.finditer(r"\bpoder\s+([A-ZÀ-Ú][\wÀ-ÿ][\wÀ-ÿ '-]+?)(?:\s*\(|[,.]|$)", txt):
        nome_p = pm.group(1).strip()
        if nome_p and nome_p not in poderes:
            poderes.append(nome_p)
    return pericias, poderes


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    origens = []
    cur = None
    campo = None

    def fecha():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(cur["nome"]).rstrip(". ")
        if not nome or STOP_NOME.match(nome):
            cur = None; return
        pericias, poderes = parse_beneficios(cur["beneficios"])
        pu_nome = dehyph(cur["poder_nome"]).rstrip(". ")
        rec = {
            "id": f"origem:herois:{slug(nome)}", "tipo": "origem", "nome": nome,
            "fonte": FONTE, "versao": "1.1", "pagina": cur["pg"] + 1,
            "resumo": dehyph(cur["lore"]).strip()[:600],
            "itens": dehyph(cur["itens"]).strip().rstrip("."),
            "beneficios": dehyph(cur["beneficios"]).strip(),
            "pericias": pericias, "poderes": poderes,
        }
        if pu_nome:
            rec["poder_unico"] = {"nome": pu_nome, "efeito": dehyph(cur["poder_ef"]).strip()}
        origens.append(rec)
        cur = None

    for s in spans:
        tp = tipo_span(s)
        if tp in ("secao", "ign"):
            continue
        txt = s["text"]
        low = dehyph(txt).lower()
        if tp == "nome":
            if cur is not None and (cur["lore"] or cur["itens"] or cur["beneficios"]
                                    or cur["poder_nome"]):
                fecha()
            if cur is None:
                cur = {"nome": "", "pg": s["pg"], "lore": "", "itens": "",
                       "beneficios": "", "poder_nome": "", "poder_ef": ""}
            cur["nome"] += " " + txt
            campo = "lore"
            continue
        if cur is None:
            continue
        if tp == "poder":
            cur["poder_nome"] += txt
            campo = "poder"
            continue
        if s["bold"]:
            if low.startswith("itens"):
                campo = "itens"
            elif low.startswith("benef"):
                campo = "beneficios"
            continue
        if campo == "lore":
            cur["lore"] += txt
        elif campo == "itens":
            cur["itens"] += txt
        elif campo == "beneficios":
            cur["beneficios"] += txt
        elif campo == "poder":
            cur["poder_ef"] += txt
    fecha()

    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "total": len(origens), "origens": origens}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(origens)} origens -> {OUT.name}\n")
    for o in origens:
        pu = o.get("poder_unico", {}).get("nome", "—")
        print(f"  - {o['nome']:<24} pg{o['pagina']:>3} | {len(o['pericias'])} perícias, "
              f"{len(o['poderes'])} poderes | PU: {pu}")


if __name__ == "__main__":
    main()
