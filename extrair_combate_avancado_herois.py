# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do COMBATE AVANÇADO — *Heróis de Arton* (Cap. 4, págs 298–306).

Regra opcional (fonte="herois-arton"). Um conjunto de ~18 REGRAS OPCIONAIS de combate
(Ações Rápidas, Ataques de Oportunidade, Ataques Mirados, Cobertura Leve, Defesa Épica,
Efeitos Críticos, Falhas Críticas, Lesões, Posicionamento, RD Combinada, …), cada uma um
módulo de regra independente (`tipo="regra_opcional"`, regra="Combate Avançado"), + as
**3 tabelas** grandes: Acertos Críticos, Teste de Morte, Falhas Críticas.

Layout (duas colunas). Cada regra = nome Tormenta20 ~21pt (às vezes PARTIDO em 2 spans →
buffer `hdr21`) + corpo IowanOldStyle. As tabelas são retângulos preenchidos (detecção de
caixas via get_drawings()) → saem do fluxo das regras; extraídas à parte via `find_tables()`
e mapeadas para as 3 seções por faixa de página.

Saída: dados/combate_avancado_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "combate_avancado_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 298, 306
# tabelas grandes → faixa de páginas (1-based) onde vivem
TABELAS = [("Acertos Críticos", 300, 301), ("Teste de Morte", 302, 303), ("Falhas Críticas", 304, 305)]


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
                    boxed = any(_dentro(r, sx, sy) for r in boxes)
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg, "boxed": boxed,
                                "size": s["size"], "font": s["font"],
                                "ss": "SourceSans" in s["font"], "t20": "Tormenta20" in s["font"],
                                "ios": "IowanOldStyle" in s["font"],
                                "bold": bool(s["flags"] & (2**4)) or "Bold" in s["font"],
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


RE_NUM = re.compile(r"^\d+(\+| a \d+)?$")        # "1", "24", "3 a 7", "13+" (faixas d%/d20)
_CABECALHO = {"d%", "efeito", "localizacao", "localização", "1d10", "1d20", "1d100",
              "teste de constituição", "teste de constituicao"}


def extrair_tabelas(doc):
    """Tabelas numeradas (d%/d10 → efeito) em SourceSans: o número fica numa sub-coluna
    estreita, centrado no bloco do efeito (por isso o find_tables desalinha). Reconstrói
    por MIDPOINT entre números consecutivos: cada linha de efeito cai na faixa vertical
    do número mais próximo."""
    tabs = []
    for nome, p0, p1 in TABELAS:
        linhas = []
        for pg in (p0, p1):
            page = doc[pg - 1]
            for t in page.find_tables().tables:
                x0, y0, x1, y1 = t.bbox
                spans = []
                for b in page.get_text("dict")["blocks"]:
                    if b.get("type") != 0:
                        continue
                    for l in b["lines"]:
                        for s in l["spans"]:
                            sx, sy = s["bbox"][0], s["bbox"][1]
                            txt = s["text"].strip()
                            if (x0 - 2 <= sx <= x1 + 2 and y0 - 2 <= sy <= y1 + 2
                                    and txt and "Spirals" not in s["font"]
                                    and dehyph(txt).lower() not in _CABECALHO):
                                spans.append((sy, sx, txt))
                if not spans:
                    continue
                nums = [(y, tx) for (y, x, tx) in spans if RE_NUM.match(tx)]
                if nums:                                   # tabela de chave NUMÉRICA (d%/d10)
                    keys = sorted(nums)
                    effs = [(y, x, tx) for (y, x, tx) in spans if not RE_NUM.match(tx)]
                else:                                      # chave TEXTUAL: separa no maior gap de x
                    xs = sorted(x for _, x, _ in spans)
                    gap_i = max(range(1, len(xs)), key=lambda i: xs[i] - xs[i - 1]) if len(xs) > 1 else 0
                    split = (xs[gap_i] + xs[gap_i - 1]) / 2 if gap_i else xs[0]
                    keys = sorted((y, tx) for (y, x, tx) in spans if x < split)
                    effs = [(y, x, tx) for (y, x, tx) in spans if x >= split]
                if not keys:
                    continue
                effs.sort()
                ys = [y for y, _ in keys]
                for i, (y, chave) in enumerate(keys):
                    lo = -1e9 if i == 0 else (ys[i - 1] + y) / 2
                    hi = 1e9 if i == len(keys) - 1 else (y + ys[i + 1]) / 2
                    ef = dehyph(juntar([tx for (ey, ex, tx) in effs if lo <= ey < hi])).strip()
                    if ef:                                 # descarta fragmentos de cabeçalho (efeito vazio)
                        linhas.append({"faixa": chave, "efeito": ef})
        tabs.append({"nome": nome, "pagina": p0, "total_linhas": len(linhas), "linhas": linhas})
    return tabs


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    regras = []
    intro = []
    cur = None
    hdr21 = []
    dropcap = ""

    def flush_nome():
        nonlocal cur
        if not hdr21:
            return
        nome = dehyph(juntar(hdr21)).strip()
        hdr21.clear()
        if nome and not re.match(r"(?i)^combate\s+avan", nome):   # ignora o título de seção
            if cur:
                fechar()
            cur = {"nome": nome, "corpo": [], "pg": None}

    def fechar():
        nonlocal cur
        if cur and cur["corpo"]:
            nome = cur["nome"]
            regras.append({
                "id": f"combate-avancado:herois:{slug(nome)}", "tipo": "regra_opcional",
                "subtipo": "combate_avancado", "regra": "Combate Avançado", "nome": nome,
                "fonte": FONTE, "versao": "1.1", "pagina": (cur["pg"] or 297) + 1,
                "efeito": dehyph(juntar(cur["corpo"])).strip(),
            })
        cur = None

    for s in spans:
        z = s["size"]; t = s["text"]
        if s["t20"] and 19 <= z < 24 and not s["boxed"]:
            hdr21.append(t)
            continue
        flush_nome()
        if s["boxed"]:
            continue                       # conteúdo de tabela → tratado à parte
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        if s["ss"]:
            continue
        if s["ios"]:
            if dropcap:
                t = dropcap + t.lstrip(); dropcap = ""
            if cur is not None:
                if cur["pg"] is None:
                    cur["pg"] = s["pg"]
                cur["corpo"].append(t)
            else:
                intro.append(t)
    flush_nome(); fechar()

    tabelas = extrair_tabelas(doc)

    banco = {
        "fonte": FONTE, "livro": "Heróis de Arton", "secao": "Combate Avançado",
        "pagina": PG_INI, "total_regras": len(regras), "total_tabelas": len(tabelas),
        "introducao": dehyph(juntar(intro)).strip(),
        "regras": regras, "tabelas": tabelas,
    }
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(regras)} regras + {len(tabelas)} tabelas -> {OUT.name}")
    print(f"  intro {len(banco['introducao'])}c\n")
    for r in regras:
        print(f"  {r['nome']:<28} pg{r['pagina']} | {len(r['efeito']):>4}c")
    print()
    for tb in tabelas:
        print(f"  TABELA {tb['nome']:<20} pg{tb['pagina']} | {tb['total_linhas']} linhas")
        for ln in tb["linhas"][:3]:
            print(f"      {ln['faixa']:>7} → {ln['efeito'][:70]}")


if __name__ == "__main__":
    main()
