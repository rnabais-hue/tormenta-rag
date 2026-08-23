# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do início do Capítulo 1 (Construção de Personagem):
os 6 ATRIBUTOS + o procedimento de criação. Págs 22–23. Guiada pela tipografia.

Saídas:
  - dados/atributos.json    : 6 atributos {nome, abrev, descricao, pericias_governadas}
  - dados/criacao_personagem.json : {passos[9], definindo_atributos{...}, tabela_custo[]}

Tipografia:
  - Atributo: Tormenta20 ~21 no formato "Nome • Abrev" (abrev in For/Des/Con/Int/
    Sab/Car) + descrição roman. `pericias_governadas` = perícias citadas na
    descrição (casadas contra as 29 reais).
  - Passos (pg22): rótulo negrito "N. Título." + descrição roman.
  - Definindo atributos (pg23): "Pontos." / "Rolagens." (negrito) + "Atributos
    Mínimos" + tabela de custo (Atributo | Custo | Rolagem).

NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
DADOS = Path(__file__).parent / "dados"
DADOS.mkdir(exist_ok=True)
OUT_ATR = DADOS / "atributos.json"
OUT_CRI = DADOS / "criacao_personagem.json"
BOLD = 2**4
ABREV = {"For": "Força", "Des": "Destreza", "Con": "Constituição",
         "Int": "Inteligência", "Sab": "Sabedoria", "Car": "Carisma"}


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("é","e"),("í","i"),("ó","o"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _pericias_canon():
    p = DADOS / "pericias.json"
    return [x["nome"] for x in json.loads(p.read_text(encoding="utf-8"))] if p.exists() else []


PERICIAS = _pericias_canon()


def spans_pagina(doc, pgn):
    page = doc[pgn - 1]; W, H = page.rect.width, page.rect.height
    out = []
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
                if y < H * 0.05 or y > H * 0.95:
                    continue
                out.append({"key": (bcol, round(by0, 1), li, si), "x": s["bbox"][0],
                            "y": y, "size": s["size"], "font": s["font"],
                            "bold": bool(s["flags"] & BOLD), "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out, page.rect.width


# --------------------------------------------------------------- atributos (pg23)
def extrair_atributos(spans):
    atrs = []
    cur = None
    for s in spans:
        t = s["text"]
        eh_atr = ("Tormenta20" in s["font"] and 19 <= s["size"] < 24
                  and "•" in t and t.split("•")[-1].strip() in ABREV)
        if eh_atr:
            if cur:
                atrs.append(cur)
            nome, _, abrev = t.partition("•")
            cur = {"nome": nome.strip(), "abrev": abrev.strip(), "_d": ""}
            continue
        # para no "Definindo seus atributos" (sz21 sem •)
        if "Tormenta20" in s["font"] and s["size"] >= 19:
            if cur:
                atrs.append(cur); cur = None
            continue
        if cur is not None and "IowanOldStyle" in s["font"]:
            cur["_d"] += t
    if cur:
        atrs.append(cur)

    saida = []
    for a in atrs:
        desc = dehyph(a["_d"])
        gov = [p for p in PERICIAS if re.search(r"\b" + re.escape(p) + r"\b", desc)]
        saida.append({
            "id": f"atributo:{slug(a['nome'])}", "tipo": "atributo",
            "nome": a["nome"], "abrev": a["abrev"], "pagina": 23,
            "descricao": desc, "pericias_governadas": gov,
        })
    return saida


# ------------------------------------------------------------------- passos (pg22)
def extrair_passos(spans):
    blobs = []
    cur = None
    for s in spans:
        m = re.match(r"^\s*(\d+)\.\s", dehyph(s["text"])) if s["bold"] else None
        if m:
            if cur:
                blobs.append(cur)
            cur = {"n": int(m.group(1)), "_t": s["text"]}
            continue
        if cur is not None:
            cur["_t"] += s["text"]
    if cur:
        blobs.append(cur)
    passos = []
    for b in blobs:
        txt = dehyph(b["_t"])
        txt = re.sub(r"^\d+\.\s*", "", txt)
        titulo, _, desc = txt.partition(".")
        passos.append({"n": b["n"], "titulo": titulo.strip(), "descricao": desc.strip()})
    return passos


# -------------------------------------------------- definindo atributos + tabela (pg23)
def extrair_definindo(spans, W):
    # blob de texto: da âncora "Definindo ... atributos" até a legenda "Tabela"
    txt = ""
    ligado = False
    for s in spans:
        low = dehyph(s["text"]).lower()
        if "Tormenta20" in s["font"] and s["size"] >= 19 and "atributos" in low and "•" not in s["text"]:
            ligado = True
            continue
        if not ligado:
            continue
        if dehyph(s["text"]).startswith("Tabela"):      # começou a tabela → para
            break
        if "Tormenta20" in s["font"] and 14 <= s["size"] < 18:   # "Atributos Mínimos" (sz16)
            txt += "\n" + dehyph(s["text"]) + ": "
            continue
        if "IowanOldStyle" in s["font"] or s["bold"]:
            txt += s["text"]
    definindo = dehyph(txt).replace(" :", ":")

    # tabela de custo (pg23): Atributo | Custo | Rolagem — colunas por posição x
    def coluna(x):
        r = x / W
        return "atributo" if r < 0.62 else ("custo" if r < 0.74 else "rolagem")
    cells = [s for s in spans if s["x"] >= W * 0.52 and 590 <= s["y"] <= 700
             and s["size"] < 12 and dehyph(s["text"]) not in ("Atributo", "Custo", "Rolagem")]
    linhas = {}
    for s in cells:
        linhas.setdefault(round(s["y"] / 6) * 6, {})[coluna(s["x"])] = dehyph(s["text"])
    tabela = [linhas[y] for y in sorted(linhas)
              if "custo" in linhas[y] or "rolagem" in linhas[y]]
    return definindo, tabela


def main():
    doc = pymupdf.open(PDF)
    s23, w23 = spans_pagina(doc, 23)
    s22, _ = spans_pagina(doc, 22)

    atributos = extrair_atributos(s23)
    OUT_ATR.write_text(json.dumps(atributos, ensure_ascii=False, indent=2), encoding="utf-8")

    passos = extrair_passos(s22)
    definindo, tabela = extrair_definindo(s23, w23)
    criacao = {"passos": passos, "definindo_atributos": definindo,
               "tabela_custo": tabela, "paginas": [22, 23]}
    OUT_CRI.write_text(json.dumps(criacao, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(atributos)} atributos -> {OUT_ATR.name}")
    for a in atributos:
        print(f"  - {a['nome']:<13} ({a['abrev']}) governa: {', '.join(a['pericias_governadas']) or '—'}")
    print(f"\n{len(passos)} passos + definindo({len(definindo)} chars) + tabela({len(tabela)} linhas) -> {OUT_CRI.name}")
    for p in passos:
        print(f"  {p['n']}. {p['titulo']}")


if __name__ == "__main__":
    main()
