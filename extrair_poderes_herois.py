# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA dos NOVOS PODERES de *Heróis de Arton* (Cap. 1).

Duas seções, MESMO layout tipográfico:
  - Novos Poderes de Classe (págs 56–79): header 27pt = NOME DA CLASSE.
  - Novos Poderes Gerais    (págs 80–97): header 27pt = CATEGORIA
    ("Poderes de Combate/Destino/Magia/..."; Concedidos etc.).

Cada PODER: nome em Tormenta20 16pt (âncora); efeito = corpo IowanOldStyle abaixo,
até o próximo poder. Pré-requisito sai do efeito por regex (fica como TEXTO — o
Stage B do grafo, se rodar, estrutura em predicado).

Schema compatível com os poderes do núcleo (categoria: nome-de-classe|combate|
destino|magia|concedido|tormenta|...). Saída: dados/poderes_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "poderes_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
CLASSE_INI, CLASSE_FIM = 56, 79     # 1-based, inclusivo
GERAIS_INI, GERAIS_FIM = 80, 97

CLASSES_T20 = {
    "arcanista", "bárbaro", "barbaro", "bardo", "bucaneiro", "caçador", "cacador",
    "cavaleiro", "clérigo", "clerigo", "druida", "guerreiro", "inventor", "ladino",
    "lutador", "nobre", "paladino",
}


def dehyph(s):
    s = re.sub("[­�]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def norm_categoria(header):
    """'Poderes de Combate' -> 'combate'; nome-de-classe fica como está (minúsculo)."""
    h = dehyph(header).strip()
    m = re.search(r"Poderes?\s+(?:de|da|do)\s+(.+)", h, re.I)
    if m:
        return slug(m.group(1)).replace("-", "_")
    return slug(h).replace("-", "_")


def extrair_pre(efeito):
    m = re.search(r"Pré-requisitos?:\s*([^.]+)", efeito)
    if not m:
        return efeito.strip(), None
    pre = m.group(1).strip()
    efeito = re.sub(r"\s*Pré-requisitos?:\s*[^.]+\.?", "", efeito).strip()
    return efeito, pre


def coletar_spans(doc, p0, p1):
    out = []
    for pg in range(p0, p1 + 1):
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
                    if "SourceSans" in s["font"] or "Spirals" in s["font"]:
                        continue
                    y = s["bbox"][1]
                    # Filtra cabeçalho corrido / nº de página (spans PEQUENOS na margem).
                    # Títulos de seção grandes (Tormenta20 ≥20pt) podem estar no topo — mantém.
                    if (y < H * 0.06 or y > H * 0.94) and s["size"] < 20:
                        continue
                    out.append({"key": (pg, bcol, round(by0, 1), li, si),
                                "pg": pg, "size": s["size"], "font": s["font"], "text": tx})
    out.sort(key=lambda r: r["key"])
    return out


def role(s):
    """Papel tipográfico do span: dropcap / splash / header / nome / body."""
    if "Tormenta20" not in s["font"]:
        return "body"
    t = dehyph(s["text"]).strip()
    sz = s["size"]
    if sz >= 36 and len(t) <= 2 and t.isalpha():
        return "dropcap"                                   # inicial decorativa ("P", "A")
    if re.match(r"novos\s+poderes", t, re.I):
        return "splash"                                    # título do capítulo
    if 14 <= sz < 20:
        return "nome"                                      # nome de poder (16pt)
    if sz >= 20:
        return "header"                                    # classe (27pt) ou categoria (27/58pt)
    return "body"


def eh_nome_poder(s):
    return role(s) == "nome"


def extrair_secao(doc, p0, p1, modo):
    """modo='classe' -> header vira campo classe; modo='geral' -> header vira categoria."""
    spans = coletar_spans(doc, p0, p1)
    poderes = []
    header_atual = None
    i = 0
    while i < len(spans):
        s = spans[i]
        r = role(s)
        if r in ("splash", "dropcap"):
            i += 1
            continue
        if r == "header":
            # header pode quebrar em 2 spans ("Poderes " + "de Combate")
            partes = [s["text"]]
            j = i + 1
            while j < len(spans) and role(spans[j]) == "header" and spans[j]["pg"] == s["pg"]:
                partes.append(spans[j]["text"]); j += 1
            header_atual = dehyph(" ".join(partes))
            i = j
            continue
        if r == "nome":
            # nome pode quebrar em vários spans 16pt consecutivos ("Arma" + "Aprimorada")
            nome_partes = [s["text"]]
            pg_poder = s["pg"]
            j = i + 1
            while j < len(spans) and role(spans[j]) == "nome":
                nome_partes.append(spans[j]["text"]); j += 1
            nome = dehyph(" ".join(nome_partes))
            # corpo: spans até o próximo nome/header/splash
            corpo = []
            while j < len(spans) and role(spans[j]) in ("body", "dropcap"):
                if role(spans[j]) == "body":
                    corpo.append(spans[j]["text"])
                j += 1
            efeito = dehyph(" ".join(corpo))
            efeito, pre = extrair_pre(efeito)
            if len(nome) >= 3 and len(efeito) >= 10:
                rec = {
                    "tipo": "poder", "nome": nome, "efeito": efeito,
                    "pre_requisito": pre, "fonte": FONTE, "versao": "1.1", "pagina": pg_poder,
                }
                if modo == "classe":
                    rec["categoria"] = "classe"
                    rec["classe"] = header_atual or "?"
                    rec["id"] = f"poder:herois:{slug(rec['classe'])}:{slug(nome)}"
                else:
                    cat = norm_categoria(header_atual or "geral")
                    rec["categoria"] = cat
                    rec["id"] = f"poder:herois:{cat}:{slug(nome)}"
                poderes.append(rec)
            i = j
            continue
        i += 1
    return poderes


def main():
    doc = pymupdf.open(str(PDF))
    classe = extrair_secao(doc, CLASSE_INI, CLASSE_FIM, "classe")
    gerais = extrair_secao(doc, GERAIS_INI, GERAIS_FIM, "geral")
    todos = classe + gerais

    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "total": len(todos),
             "total_classe": len(classe), "total_gerais": len(gerais), "poderes": todos}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(todos)} poderes -> {OUT.name} ({len(classe)} de classe, {len(gerais)} gerais)\n")
    from collections import Counter
    print("Poderes de classe por classe:")
    for k, n in Counter(p.get("classe") for p in classe).most_common():
        print(f"   {str(k):18s} {n}")
    print("Poderes gerais por categoria:")
    for k, n in Counter(p.get("categoria") for p in gerais).most_common():
        print(f"   {str(k):18s} {n}")
    com_pre = sum(1 for p in todos if p["pre_requisito"])
    print(f"\ncom pré-requisito: {com_pre}/{len(todos)}")


if __name__ == "__main__":
    main()
