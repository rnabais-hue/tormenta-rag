# -*- coding: utf-8 -*-
r"""Extração dos NOVOS ITENS MÁGICOS — *Heróis de Arton* (Cap. 3, págs 258–275).

Seção grande e uniforme: vários blocos de **itens mágicos** (rótulo negrito IowanOldStyle
terminando em "." + descrição/efeito, como as construções de Domínio) agrupados por
categoria, mais dois blocos PROCEDURAIS (Itens Inteligentes, Itens Amaldiçoados).

Categorias (derivadas do cabeçalho 21pt): Encantos para Armas / Armas Específicas / Encantos
para Armaduras & Escudos / Armaduras Específicas / Escudos Específicos / Encantos para
Esotéricos / Esotéricos Específicos / Encantos para Acessórios / Acessórios Específicos /
Maldições (de Armas, de Armaduras/Escudos/Acessórios). Cada item: `tipo="item_magico"`,
`subtipo=<categoria>`. Procedurais: `tipo="regra_opcional"`, `subtipo="itens_magicos"`.

Máquina header-driven (reusa Domínios/regras_soltas): 27pt agrupador redundante (Armas/
Armaduras/Esotéricos/Acessórios) é absorvido; a categoria vem por PALAVRA-CHAVE no cabeçalho.
`fonte="herois-arton"`. Saída: dados/itens_magicos_herois.json.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "itens_magicos_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 258, 275
RE_ITEM = re.compile(r"^[A-ZÀ-Ú][\wÀ-ÿ][\wÀ-ÿ ()\-']{0,34}\.$")


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


def _norm(s):
    return slug(s).replace("-", " ")


def categoria_de(nn):
    """Deriva (categoria, rótulo, modo) do texto normalizado do cabeçalho. modo:
    'item' (lista de itens), 'proc' (bloco procedural) ou None (agrupador redundante)."""
    grupo = ("armaduras" if "armadura" in nn else "escudos" if "escudo" in nn else
             "esotericos" if "esoteric" in nn else "acessorios" if "acessori" in nn else
             "armas" if "arma" in nn else "")
    # PROCEDURAIS primeiro (cuidado: "amaldiçoados"/"removendo maldições" contêm "maldic")
    if "amaldicoados" in nn or "removendo maldic" in nn:
        return ("itens_amaldicoados", "Itens Amaldiçoados", "proc")
    if "itens inteligentes" in nn or "criando um item" in nn or nn == "ego" or "item magico inteligente" in nn:
        return ("itens_inteligentes", "Itens Inteligentes", "proc")
    # LISTAS de itens
    if "maldic" in nn:
        return (f"maldicao_{grupo or 'geral'}", f"Maldições ({grupo or 'geral'})", "item")
    if "encanto" in nn:
        return (f"encanto_{grupo}", f"Encantos para {grupo}", "item")
    if "especific" in nn:
        return (f"{grupo}_especifico", f"{grupo} específicos", "item")
    return (None, None, None)   # agrupador redundante (Armas/Armaduras/... sozinho)


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
                    if not s["text"].strip() or "Spirals" in s["font"]:
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


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)
    itens, modulos = [], []
    hdr, hdr_sz = [], 0.0
    modo = None          # 'item' | 'proc' | None
    categoria = rotulo = None
    cur_item = cur_mod = None
    dropcap = ""

    def fecha_item():
        nonlocal cur_item
        if cur_item:
            nome = dehyph(cur_item["nome"]).rstrip(". ")
            desc = dehyph(juntar(cur_item["desc"])).strip()
            if nome and desc:
                itens.append({"id": f"item-magico:herois:{cur_item['cat']}:{slug(nome)}",
                              "tipo": "item_magico", "subtipo": cur_item["cat"], "categoria": cur_item["rot"],
                              "nome": nome, "fonte": FONTE, "versao": "1.1", "pagina": cur_item["pg"] + 1,
                              "descricao": desc})
        cur_item = None

    def fecha_mod():
        nonlocal cur_mod
        if cur_mod and cur_mod["corpo"]:
            nome = cur_mod["nome"]
            modulos.append({"id": f"item-magico-regra:herois:{slug(nome)}", "tipo": "regra_opcional",
                            "subtipo": "itens_magicos", "regra": cur_mod["rot"], "nome": nome,
                            "fonte": FONTE, "versao": "1.1", "pagina": cur_mod["pg"] + 1,
                            "efeito": dehyph(juntar(cur_mod["corpo"])).strip()})
        cur_mod = None

    def flush_hdr(pg):
        nonlocal modo, categoria, rotulo, cur_mod
        if not hdr:
            return
        nome = dehyph(juntar(hdr)).strip(); sz = hdr_sz
        hdr.clear()
        cat, rot, m = categoria_de(_norm(nome))
        if m == "item":
            fecha_item(); fecha_mod()
            modo, categoria, rotulo = "item", cat, rot
            return
        if m == "proc":
            fecha_item(); fecha_mod()
            modo, categoria, rotulo = "proc", cat, rot
            cur_mod = {"nome": nome, "corpo": [], "pg": pg, "rot": rot}
            return
        # agrupador redundante (Armas/Armaduras/...): se 27pt e não casou, ignora;
        # se for subtítulo de um bloco proc, dobra
        if modo == "proc" and cur_mod is not None and sz < 24:
            cur_mod["corpo"].append(f" {nome}:")

    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 40:
            tt = t.strip()
            if len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["t20"] and 15 <= z < 40:
            hdr.append(t); hdr_sz = max(hdr_sz, z)
            continue
        if hdr:
            flush_hdr(s["pg"]); hdr_sz = 0.0
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if re.match(r"(?i)^tabela\s+\d", dehyph(t)):
            continue                              # legenda de tabela vazada → descarta
        if modo == "item":
            if s["bold"] and RE_ITEM.match(dehyph(t).strip()):
                fecha_item()
                cur_item = {"nome": t, "desc": [], "pg": s["pg"], "cat": categoria, "rot": rotulo}
            elif cur_item is not None:
                cur_item["desc"].append(t)
        elif modo == "proc" and cur_mod is not None:
            cur_mod["corpo"].append(t)
    flush_hdr(PG_FIM); fecha_item(); fecha_mod()

    # contagem por categoria
    from collections import Counter
    porcat = Counter(i["subtipo"] for i in itens)
    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "secao": "Novos Itens Mágicos",
             "pagina": PG_INI, "total_itens": len(itens), "total_modulos": len(modulos),
             "por_categoria": dict(porcat), "itens": itens, "modulos": modulos}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(itens)} itens mágicos + {len(modulos)} módulos -> {OUT.name}\n")
    for cat, n in porcat.items():
        print(f"  {cat:<24} {n}")
    print("\n  módulos:", ", ".join(m["nome"] for m in modulos))


if __name__ == "__main__":
    main()
