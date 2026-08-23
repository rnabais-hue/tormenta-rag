# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das 29 PERÍCIAS de Tormenta20 (núcleo), guiada pela
TIPOGRAFIA (não pelo TOC). Seção "Descrição das Perícias", págs 121–129.

Tipografia = schema:
  - Nome da perícia: Tormenta20-Regular ~21 (pode ocupar 2 linhas → junta).
  - Stat block: Tormenta20-Regular ~16, tokens separados por "•":
      atributo-chave (For|Des|Con|Int|Sab|Car) + flags "Treinada" (só treinada)
      e "Armadura" (penalidade de armadura). Ex.: "Des • Treinada • Armadura".
  - Descrição: IowanOldStyle-Roman ~9.5. O 1º trecho roman (antes do 1º negrito)
    é o RESUMO; cada USO é um nome em negrito ("Amortecer Queda (CD 15, Apenas
    Treinado).", "Escapar.") seguido do efeito em roman.

Uma perícia só é emitida se tiver atributo no stat block (guarda contra sz21 que
não seja nome de perícia). Ordena por bloco/coluna (como raças/classes/poderes).

Lê o PDF; escreve dados/pericias.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
OUT = Path(__file__).parent / "dados" / "pericias.json"
OUT.parent.mkdir(exist_ok=True)
BOLD = 2**4

PG_INI, PG_FIM = 121, 129            # 1-based, inclusive (Poderes Gerais = 130)
ATTR = {"For": "Força", "Des": "Destreza", "Con": "Constituição",
        "Int": "Inteligência", "Sab": "Sabedoria", "Car": "Carisma"}


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
        return "titulo"          # "Descrição das Perícias" — ignora
    if t20 and 19 <= z < 24:
        return "nome"
    if t20 and 14 <= z < 18:
        return "stat"
    if "IowanOldStyle" in s["font"] and z >= 8.5:
        return "desc"
    return "ign"


def parse_stat(tokens):
    """Extrai (atributo, so_treinada, penalidade_armadura) dos tokens sz16."""
    txt = " ".join(tokens)
    m = re.search(r"\b(For|Des|Con|Int|Sab|Car)\b", txt)
    atributo = ATTR[m.group(1)] if m else None
    return atributo, bool(re.search(r"Treinad", txt)), bool(re.search(r"Armadura", txt))


def parse_uso(nome_bold, efeito):
    """Nome do uso pode trazer '(CD 15, Apenas Treinado)'. Separa cd/flag."""
    nome = dehyph(nome_bold)
    cd = None; apenas = False
    m = re.search(r"\(([^)]*)\)", nome)
    if m:
        interno = m.group(1)
        cd_m = re.search(r"CD\s*(\d+)", interno)
        if cd_m:
            cd = int(cd_m.group(1))
        apenas = bool(re.search(r"Apenas\s+Treinado", interno, re.I))
        nome = re.sub(r"\s*\([^)]*\)", "", nome)
    nome = nome.rstrip(". ").strip()
    uso = {"nome": nome, "efeito": dehyph(efeito).strip()}
    if cd is not None:
        uso["cd"] = cd
    if apenas:
        uso["apenas_treinado"] = True
    return uso


# cross-refs e legendas de tabela vazam como "usos" em negrito — descarta.
_LIXO_USO = re.compile(r"^(Capítulo\s+\d|Tabela\s+\d|Introduç)", re.I)


def separar_desc(desc_spans):
    """Do fluxo de descrição: resumo (roman inicial) + usos (negrito→roman)."""
    resumo_parts = []
    usos = []
    cur = None                  # uso em construção
    for s in desc_spans:
        if s["bold"]:
            if cur is None or cur["_ef"].strip():
                cur = {"nome": "", "_ef": ""}; usos.append(cur)
            cur["nome"] += s["text"]
        else:
            if cur is None:
                resumo_parts.append(s["text"])
            else:
                cur["_ef"] += s["text"]
    resumo = dehyph("".join(resumo_parts))
    usos_out = []
    for u in usos:
        nome = dehyph(u["nome"]).strip(". ")
        efeito = dehyph(u["_ef"]).strip()
        if nome and efeito and not _LIXO_USO.match(nome):   # pula cross-ref/legenda
            usos_out.append(parse_uso(u["nome"], u["_ef"]))
    return resumo, usos_out


def main():
    doc = pymupdf.open(PDF)
    spans = coletar_spans(doc)

    pericias = []
    cur = None                  # {nome, pg, stat_tokens[], desc_spans[]}

    def fecha():
        nonlocal cur
        if not cur:
            return
        atributo, so_tr, pen = parse_stat(cur["stat_tokens"])
        if not atributo:                      # sz21 que não é perícia → descarta
            cur = None; return
        nome = dehyph(cur["nome"]).rstrip(". ")
        resumo, usos = separar_desc(cur["desc_spans"])
        pericias.append({
            "id": f"pericia:{slug(nome)}", "tipo": "pericia", "nome": nome,
            "fonte": "nucleo", "versao": "jogo-do-ano-2024", "pagina": cur["pg"] + 1,
            "atributo": atributo, "so_treinada": so_tr, "penalidade_armadura": pen,
            "resumo": resumo, "usos": usos,
        })
        cur = None

    for s in spans:
        tp = tipo_span(s)
        if tp == "titulo" or tp == "ign":
            continue
        if tp == "nome":
            # novo nome só inicia perícia se o atual já tem descrição/stat
            if cur and (cur["stat_tokens"] or cur["desc_spans"]):
                fecha()
            if cur is None:
                cur = {"nome": "", "pg": s["pg"], "stat_tokens": [], "desc_spans": []}
            cur["nome"] += s["text"]
        elif tp == "stat" and cur is not None:
            cur["stat_tokens"].append(s["text"])
        elif tp == "desc" and cur is not None:
            cur["desc_spans"].append(s)
    fecha()

    OUT.write_text(json.dumps(pericias, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(pericias)} perícias -> {OUT.name}\n")
    for p in pericias:
        flags = []
        if p["so_treinada"]: flags.append("só-treinada")
        if p["penalidade_armadura"]: flags.append("armadura")
        print(f"  - {p['nome']:<14} {p['atributo']:<13} {len(p['usos'])} usos "
              f"{'· ' + ', '.join(flags) if flags else ''}")


if __name__ == "__main__":
    main()
