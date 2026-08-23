# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das ORIGENS de Tormenta20 (núcleo), guiada pela
TIPOGRAFIA. Seção "Origens", págs 91–101.

Tipografia = schema:
  - Nome da origem: Tormenta20-Regular ~21 (Acólito, Amnésico…). O cabeçalho da
    seção "Origens" é ~26 (ignorado); "Sua Própria Origem" é regra, não origem.
  - Lore: IowanOldStyle-Roman ~9.5 antes do rótulo "Itens.".
  - Rótulos em negrito: "Itens." → linha de itens; "Benefícios." → perícias e
    poderes concedidos, no formato "A, B (perícias); C, D (poderes).".
  - Poder Único: Tormenta20-Regular ~16 (nome do poder exclusivo) + efeito roman.

Os Benefícios são parseados em listas `pericias`/`poderes` (habilita filtro
híbrido: "origens que dão a perícia Cura"). Ordena por bloco/coluna.

Lê o PDF; escreve dados/origens.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
OUT = Path(__file__).parent / "dados" / "origens.json"
OUT.parent.mkdir(exist_ok=True)
BOLD = 2**4

PG_INI, PG_FIM = 91, 101            # 1-based, inclusive (Deuses = 102)
STOP_NOME = re.compile(r"^(Origens|Sua Própria Origem)$", re.I)


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def coletar_spans(doc):
    out = []
    for pg in range(PG_INI - 1, PG_FIM):        # 0-based
        page = doc[pg]; W, H = page.rect.width, page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            bx0, by0 = b["bbox"][0], b["bbox"][1]
            bcol = 0 if bx0 < W * 0.40 else 1
            for li, l in enumerate(b["lines"]):
                for si, s in enumerate(l["spans"]):
                    if not s["text"].strip():
                        continue
                    if s["size"] <= 8.4:            # legendas de arte (~8.0)
                        continue
                    y = s["bbox"][1]
                    if y < H * 0.06 or y > H * 0.94:
                        continue
                    out.append({
                        "key": (pg, bcol, round(by0, 1), li, si),
                        "pg": pg, "size": s["size"], "font": s["font"],
                        "bold": bool(s["flags"] & BOLD), "text": s["text"],
                    })
    out.sort(key=lambda r: r["key"])
    return out


def tipo_span(s):
    t20 = "Tormenta20" in s["font"]
    z = s["size"]
    if t20 and z >= 24:
        return "secao"          # "Origens" — ignora
    if t20 and 19 <= z < 24:
        return "nome"           # nome da origem
    if t20 and 13 <= z < 18:
        return "poder"          # nome do Poder Único
    if "IowanOldStyle" in s["font"]:
        return "corpo"
    return "ign"


# perícias canônicas (as 29 do jogo) para normalizar a lista das origens:
# fecha "Ofício (alquimista)" → "Ofício" e "Enga-nação" → "Enganação".
def _norm(s):
    s = dehyph(s).lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s)


def _carregar_pericias_canon():
    p = Path(__file__).parent / "dados" / "pericias.json"
    if not p.exists():
        return {}
    return {_norm(x["nome"]): x["nome"] for x in json.loads(p.read_text(encoding="utf-8"))}


_PER_CANON = _carregar_pericias_canon()


def canon_pericia(tok):
    base = re.sub(r"\s*\([^)]*\)", "", dehyph(tok)).strip()   # tira especialização
    return _PER_CANON.get(_norm(base), base)


def parse_beneficios(txt):
    """'A, B (perícias); C, D (poderes).' -> (pericias[], poderes[])."""
    txt = dehyph(txt)
    def lista(m):
        return [x.strip(" .") for x in re.split(r"[,;]", m) if x.strip(" .")]
    per = re.search(r"(.+?)\s*\(perícias\)", txt)
    pod = re.search(r"\(perícias\)\s*;?\s*(.+?)\s*\(poderes\)", txt)
    pericias = [canon_pericia(x) for x in lista(per.group(1))] if per else []
    poderes = lista(pod.group(1)) if pod else []
    return pericias, poderes


def main():
    doc = pymupdf.open(PDF)
    spans = coletar_spans(doc)

    origens = []
    cur = None
    campo = None                 # 'lore' | 'itens' | 'beneficios' | 'poder'

    def fecha():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(cur["nome"]).rstrip(". ")
        if STOP_NOME.match(nome):
            cur = None; return
        pericias, poderes = parse_beneficios(cur["beneficios"])
        pu_nome = dehyph(cur["poder_nome"]).rstrip(". ")
        rec = {
            "id": f"origem:{slug(nome)}", "tipo": "origem", "nome": nome,
            "fonte": "nucleo", "versao": "jogo-do-ano-2024", "pagina": cur["pg"] + 1,
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
        if tp == "secao" or tp == "ign":
            continue
        txt = s["text"]
        low = dehyph(txt).lower()
        if tp == "nome":
            # nome pode ocupar 2 linhas (ex.: "Assistente de Laboratório") → só
            # abre nova origem se a atual já tem corpo; senão continua o nome.
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
        # rótulos "Itens." / "Benefícios." podem estar partidos em 2 spans negrito
        # (ex.: "Benefí"+"cios."): pula TODO span negrito (só troca de campo no 1º).
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

    OUT.write_text(json.dumps(origens, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(origens)} origens -> {OUT.name}\n")
    for o in origens:
        pu = o.get("poder_unico", {}).get("nome", "—")
        print(f"  - {o['nome']:<22} pg{o['pagina']:>3} | "
              f"{len(o['pericias'])} perícias, {len(o['poderes'])} poderes | PU: {pu}")


if __name__ == "__main__":
    main()
