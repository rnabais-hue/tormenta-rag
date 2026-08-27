# -*- coding: utf-8 -*-
r"""Extração das ORIGENS REGIONAIS — *Atlas de Arton* (Apêndice, págs 472–483).

1º recorte do 3º livro de expansão (`fonte="atlas-arton"`). Origens ligadas a um reino/
região de Arton (escolhidas no lugar da origem comum). Cada uma:
  • nome  — Tormenta20 ~16pt (pode ocupar 2 linhas; continuação minúscula → junta);
  • região — tag Tormenta20 ~11pt logo após o nome (ex.: "Sambúrdia", "Ahlen");
  • Itens. / Benefício. — rótulos negrito IowanOldStyle + texto.
Schema compatível com as origens do núcleo (`tipo="origem"`) + campo `regiao`. As perícias
concedidas ("treinado em X") são canonizadas contra as 29 perícias reais.

Layout = Heróis/núcleo (IowanOldStyle corpo, Tormenta20 nomes, SourceSansPro caixas). Duas
colunas → ordenação por bloco; caixas/tabela-resumo fora do fluxo via get_drawings().
A "Tabela: Origens Regionais" (p475) é redundante → descartada. Saída: dados/origens_regionais_atlas.json.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PDF = Path(__file__).parent / "livro" / "Atlas-de-Arton-v1.0-17-11-2023.pdf"
OUT = Path(__file__).parent / "dados" / "origens_regionais_atlas.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "atlas-arton"
PG_INI, PG_FIM = 472, 483
STOP = re.compile(r"^(Origens Regionais|Apêndice|Tabela)", re.I)


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


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
    return re.sub(r"[^a-z]", "", slug(s))


def _pericias_canon():
    p = Path(__file__).parent / "dados" / "pericias.json"
    if not p.exists():
        return {}
    return {_norm(x["nome"]): x["nome"] for x in json.loads(p.read_text(encoding="utf-8"))}


PER = _pericias_canon()


def parse_pericias(txt):
    out = []
    m = re.search(r"treinad[oa]\s+em\s+(.{0,160})", dehyph(txt), re.I)
    if m:
        for tok in re.split(r"\s*(?:[,;.]|\be\b)\s*", m.group(1)):
            base = re.sub(r"\s*\([^)]*\)", "", dehyph(tok)).strip()
            if _norm(base) in PER and PER[_norm(base)] not in out:
                out.append(PER[_norm(base)])
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
                    if not s["text"].strip():
                        continue
                    if "SourceSans" in s["font"] or "Spirals" in s["font"]:
                        continue                       # caixas/pull-quotes
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
    origens = []
    cur = None
    campo = None
    dropcap = ""
    intro = []
    ultima_nome = False

    def fecha():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ").strip()
        if not nome or STOP.match(nome):
            cur = None; return
        itens = dehyph(juntar(cur["itens"])).strip()
        benef = dehyph(juntar(cur["beneficio"])).strip()
        origens.append({
            "id": f"origem-regional:atlas:{slug(nome)}", "tipo": "origem", "subtipo": "regional",
            "nome": nome, "regiao": dehyph(juntar(cur["regiao"])).strip() or None,
            "fonte": FONTE, "versao": "1.0", "pagina": cur["pg"] + 1,
            "itens": itens, "beneficio": benef, "pericias": parse_pericias(benef),
        })
        cur = None

    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 24:                   # splash "Origens Regionais"/"Apêndice" ou drop-cap
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["t20"] and 13 <= z < 20:              # nome de origem (16pt; pode partir)
            _sem_conteudo = cur is not None and not (cur["regiao"] or cur["itens"] or cur["beneficio"])
            if cur is not None and ultima_nome and (t[:1].islower() or _sem_conteudo):
                cur["nome"].append(t)              # continuação do nome (minúscula OU sem conteúdo ainda)
                continue
            fecha()
            cur = {"nome": [t], "regiao": [], "itens": [], "beneficio": [], "pg": s["pg"]}
            campo = None; ultima_nome = True
            continue
        ultima_nome = False
        if s["t20"] and 10 <= z < 13:              # tag de REGIÃO
            if cur is not None:
                cur["regiao"].append(t)
            continue
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        low = dehyph(t).lower()
        if s["bold"] and cur is not None:
            if low.startswith("iten"):
                campo = "itens"; continue
            if low.startswith("benef"):
                campo = "beneficio"; continue
        if cur is None:
            intro.append(t)
        elif campo in ("itens", "beneficio"):
            cur[campo].append(t)
    fecha()

    banco = {"fonte": FONTE, "livro": "Atlas de Arton", "secao": "Origens Regionais (Apêndice)",
             "pagina": PG_INI, "total": len(origens),
             "introducao": dehyph(juntar(intro)).strip(), "origens": origens}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    from collections import Counter
    regs = Counter(o["regiao"] for o in origens)
    print(f"{len(origens)} origens regionais -> {OUT.name}  ({len(regs)} regiões)\n")
    for o in origens:
        print(f"  {o['nome']:<28} [{str(o['regiao'])[:16]:<16}] pg{o['pagina']} | "
              f"itens {len(o['itens']):>3}c benef {len(o['beneficio']):>3}c | pericias {o['pericias']}")


if __name__ == "__main__":
    main()
