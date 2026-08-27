# -*- coding: utf-8 -*-
r"""Extração do ARSENAL MENOR — *Heróis de Arton* (Cap. 3, págs 241–253).

Fecha o Cap. 3 com as seções que faltavam:
  • **Novas Melhorias** de item (241–242) — entidades `tipo="melhoria_item"`.
  • **Capangas** (242–243) — grupos de capangas/mercenários, `tipo="capanga"`.
  • **Veículos** (245) — lista de veículos, `tipo="veiculo"`.
  • **Bases** (246–253): módulos procedurais (Adquirindo/Características/Tipos/Porte/
    Segurança/Manutenção) + **Cômodos** entidades (`tipo="comodo_base"`) + **Mobílias**
    (Tabela 3-8, `tipo="mobilia"`).
Mais os módulos procedurais de Itens Superiores, Capangas Convocados e regras de Veículos.

Reusa a máquina header-driven de `extrair_itens_magicos_herois.py`: 27/21pt = seção;
entidade = rótulo negrito terminando em "." nas seções de LISTA; categoria por palavra-chave.
Mobílias é 2 colunas (Mobília/Benefício) → geometria. `fonte="herois-arton"`.
Saída: dados/arsenal_menor_herois.json.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "arsenal_menor_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 241, 253
RE_ITEM = re.compile(r"^[A-ZÀ-Ú][\wÀ-ÿ][\wÀ-ÿ ()\-']{0,32}\.$")


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


ENT = {"novas melhorias": ("melhoria_item", "Novas Melhorias"),
       "capangas": ("capanga", "Capangas"),
       "lista de veiculos": ("veiculo", "Veículos"),
       "comodos": ("comodo_base", "Cômodos")}


def categoria_de(nn):
    if nn in ENT:
        return (*ENT[nn], "item")
    if nn == "mobilias":
        return ("mobilia", "Mobílias", "tabela")
    return (None, None, "proc")


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


def extrair_mobilias(doc):
    """Tabela 3-8: Mobílias (Mobília | Benefício), 2 colunas, via find_tables + split de x."""
    linhas = []
    for pg in (252, 253):
        page = doc[pg - 1]
        for t in page.find_tables().tables:
            if t.col_count != 2:
                continue
            x0, y0, x1, y1 = t.bbox
            sps = []
            for b in page.get_text("dict")["blocks"]:
                if b.get("type") != 0:
                    continue
                for l in b["lines"]:
                    for s in l["spans"]:
                        sx, sy = s["bbox"][0], s["bbox"][1]
                        if x0 - 2 <= sx <= x1 + 2 and y0 - 2 <= sy <= y1 + 2 and s["text"].strip():
                            sps.append((round(sy, 1), sx, s["text"].strip()))
            if not sps:
                continue
            xs = sorted(x for _, x, _ in sps)
            gap = max(range(1, len(xs)), key=lambda i: xs[i] - xs[i - 1]) if len(xs) > 1 else 0
            split = (xs[gap] + xs[gap - 1]) / 2 if gap else xs[0] + 1
            keys0 = sorted((y, tx) for (y, x, tx) in sps if x < split and _norm(tx) not in ("mobilia", "beneficio"))
            # nomes de mobília em 2 linhas: a continuação começa em MINÚSCULA → funde na anterior
            keys = []
            for y, tx in keys0:
                if keys and tx[:1].islower():
                    keys[-1] = (keys[-1][0], keys[-1][1] + " " + tx)
                else:
                    keys.append((y, tx))
            effs = [(y, x, tx) for (y, x, tx) in sps if x >= split]
            ys = [y for y, _ in keys]
            for i, (y, nome) in enumerate(keys):
                lo = -1e9 if i == 0 else (ys[i - 1] + y) / 2
                hi = 1e9 if i == len(keys) - 1 else (y + ys[i + 1]) / 2
                ben = dehyph(juntar([tx for (ey, ex, tx) in effs if lo <= ey < hi])).strip()
                if nome and ben:
                    linhas.append({"nome": dehyph(nome).rstrip(". "), "beneficio": ben, "pagina": pg})
    return linhas


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)
    entidades, modulos = [], []
    hdr, hdr_sz, hdr_last = [], 0.0, 0.0
    modo = "proc"; categoria = rotulo = None
    cur_ent = cur_mod = None
    dropcap = ""

    def fecha_ent():
        nonlocal cur_ent
        if cur_ent:
            nome = dehyph(cur_ent["nome"]).rstrip(". ")
            desc = dehyph(juntar(cur_ent["desc"])).strip()
            if nome and desc:
                entidades.append({"id": f"{cur_ent['cat']}:herois:{slug(nome)}", "tipo": cur_ent["cat"],
                                  "categoria": cur_ent["rot"], "nome": nome, "fonte": FONTE,
                                  "versao": "1.1", "pagina": cur_ent["pg"] + 1, "descricao": desc})
        cur_ent = None

    def fecha_mod():
        nonlocal cur_mod
        if cur_mod and cur_mod["corpo"]:
            nome = cur_mod["nome"]
            modulos.append({"id": f"arsenal-menor:herois:{slug(nome)}", "tipo": "regra_opcional",
                            "subtipo": "arsenal_menor", "regra": nome, "nome": nome, "fonte": FONTE,
                            "versao": "1.1", "pagina": cur_mod["pg"] + 1,
                            "efeito": dehyph(juntar(cur_mod["corpo"])).strip()})
        cur_mod = None

    def flush_hdr(pg):
        nonlocal modo, categoria, rotulo, cur_mod, hdr_sz, hdr_last
        if not hdr:
            return
        nome = dehyph(juntar(hdr)).strip(); sz = hdr_sz
        hdr.clear(); hdr_sz = 0.0; hdr_last = 0.0
        cat, rot, m = categoria_de(_norm(nome))
        if m == "item":
            fecha_ent(); fecha_mod(); modo, categoria, rotulo = "item", cat, rot
            return
        if m == "tabela":
            fecha_ent(); fecha_mod(); modo = "tabela"
            return
        fecha_ent(); fecha_mod(); modo = "proc"
        cur_mod = {"nome": nome, "corpo": [], "pg": pg}

    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 40:
            tt = t.strip()
            if len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["t20"] and 15 <= z < 40:
            if hdr and abs(z - hdr_last) > 3:     # mudança de nível (ex.: 27→21) → fecha o anterior
                flush_hdr(s["pg"])
            hdr.append(t); hdr_last = z; hdr_sz = max(hdr_sz, z)
            continue
        if hdr:
            flush_hdr(s["pg"])
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if re.match(r"(?i)^tabela\s+\d", dehyph(t)):
            continue
        if modo == "item":
            if s["bold"] and RE_ITEM.match(dehyph(t).strip()):
                fecha_ent()
                cur_ent = {"nome": t, "desc": [], "pg": s["pg"], "cat": categoria, "rot": rotulo}
            elif cur_ent is not None:
                cur_ent["desc"].append(t)
        elif modo == "proc" and cur_mod is not None:
            cur_mod["corpo"].append(t)
    flush_hdr(PG_FIM); fecha_ent(); fecha_mod()

    mobilias = extrair_mobilias(doc)
    from collections import Counter
    porcat = Counter(e["tipo"] for e in entidades)
    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "secao": "Arsenal (seções menores + Bases)",
             "pagina": PG_INI, "total_entidades": len(entidades), "total_modulos": len(modulos),
             "total_mobilias": len(mobilias), "por_tipo": dict(porcat),
             "entidades": entidades, "modulos": modulos, "mobilias": mobilias}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(entidades)} entidades + {len(modulos)} módulos + {len(mobilias)} mobílias -> {OUT.name}\n")
    for cat, n in porcat.items():
        print(f"  {cat:<16} {n}")
    print("\n  módulos:", ", ".join(m["nome"] for m in modulos))
    print("\n  mobílias:", ", ".join(m["nome"] for m in mobilias))


if __name__ == "__main__":
    main()
