# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das COMPLICAÇÕES — *Heróis de Arton* (Cap. 4, págs 284–289).

Regra opcional (fonte="herois-arton"). Complicação = restrição/penalidade que o
personagem pode escolher na criação (uma só) em troca de um poder geral extra.
Duas categorias: **Gerais** e **de Classe**. Entidade nova: `tipo="complicacao"`.

Layout (duas colunas → ordenação por bloco). Âncoras tipográficas:
  • nome da complicação = Tormenta20 ~16pt;
  • categoria = cabeçalho Tormenta20 ~21pt ("Complicações Gerais"/"de Classe");
  • no formato compacto (p289) a CLASSE vem taggeada em Tormenta20 ~11pt após o nome;
  • efeito = corpo IowanOldStyle;
  • título de seção 27/66pt e drop-cap 78pt (Tormenta20 ≥24) descartados/religados;
  • pull-quotes e a Tabela 4-1 em SourceSans → descartados; MAS um cabeçalho
    SourceSans ≥12.5pt ("Regra Opcional: Superação") inicia uma CAIXA (sidebar).

O texto anterior à 1ª categoria (intro + "Tipos de complicações") vira `introducao`.
Saída: dados/complicacoes_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "complicacoes_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
BOLD = 2**4
PG_INI, PG_FIM = 284, 289

CAT = {"complicacoesgerais": "geral", "complicacoesdeclasse": "classe"}


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


def _classes_canon():
    p = Path(__file__).parent / "dados" / "classes.json"
    nomes = []
    if p.exists():
        nomes = [c["nome"] for c in json.loads(p.read_text(encoding="utf-8"))]
    nomes.append("Treinador")     # classe nova de Heróis (Cap. 1)
    return nomes


CLASSES = _classes_canon()
CLASSES_NORM = {_norm(n): n for n in CLASSES}


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
                    if not s["text"].strip():
                        continue
                    if "Spirals" in s["font"]:
                        continue
                    y = s["bbox"][1]
                    if (y < H * 0.06 or y > H * 0.94) and s["size"] < 24:
                        continue
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "size": s["size"], "font": s["font"],
                                "ss": "SourceSans" in s["font"],
                                "t20": "Tormenta20" in s["font"],
                                "ios": "IowanOldStyle" in s["font"],
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def deriva_classe(nome, efeito):
    """Fallback: acha a classe citada no nome/efeito (nomes canônicos)."""
    hay = " " + dehyph(nome + " " + efeito) + " "
    for norm, real in CLASSES_NORM.items():
        if re.search(r"(?<![a-zà-ÿ])" + re.escape(real), hay, re.I):
            return real
    return None


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    comps = []
    intro = []
    sidebars = []
    cur = None            # complicação atual
    sb = None             # sidebar/caixa atual
    dropcap = ""
    categoria = None
    hdr21 = []            # buffer de spans 21pt (o título "de Classe" vem partido)

    def fecha_comp():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ")
        efeito = dehyph(juntar(cur["efeito"])).strip()
        if not nome:
            cur = None; return
        voto = "†" in efeito          # † = complicação de código/voto (viola → perde PM)
        efeito = re.sub(r"\s*†\s*", " ", efeito).strip()
        classe = cur["classe"] or (deriva_classe(nome, efeito) if cur["cat"] == "classe" else None)
        rec = {
            "id": f"complicacao:herois:{slug(nome)}", "tipo": "complicacao", "nome": nome,
            "categoria": cur["cat"], "classe": classe, "voto": voto,
            "fonte": FONTE, "versao": "1.1", "pagina": cur["pg"] + 1,
            "efeito": efeito,
        }
        comps.append(rec); cur = None

    def fecha_sb():
        nonlocal sb
        if sb and sb["texto"]:
            sidebars.append({"titulo": dehyph(sb["titulo"]).strip(),
                             "texto": dehyph(juntar(sb["texto"])).strip(),
                             "pagina": sb["pg"] + 1})
        sb = None

    def flush_hdr():
        nonlocal categoria
        if not hdr21:
            return
        k = _norm(" ".join(hdr21))
        if "declasse" in k:
            fecha_comp(); categoria = "classe"
        elif "gerais" in k:
            fecha_comp(); categoria = "geral"
        elif categoria is None:
            intro.append(" ".join(hdr21))          # subtítulo do overview (ex.: "Tipos de complicações")
        hdr21.clear()

    for s in spans:
        t = s["text"]; z = s["size"]
        # cabeçalho de categoria vem em Tormenta20 ~21pt e pode estar PARTIDO em
        # 2 spans ("Complicações" + "de Classe") → acumula e resolve no flush.
        if s["t20"] and 19 <= z < 24:
            hdr21.append(t)
            continue
        flush_hdr()
        # 1) SourceSans: cabeçalho de caixa (≥12.5) inicia sidebar; resto descarta
        if s["ss"]:
            if z >= 12.5 and re.search(r"[A-Za-zÀ-ÿ]", t):
                fecha_comp(); fecha_sb()
                sb = {"titulo": t, "texto": [], "pg": s["pg"]}
            continue
        # 2) Tormenta20 grande (≥24): título de seção ou drop-cap
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            continue
        # 4) Tormenta20 ~16: nome de complicação (só após 1ª categoria)
        if s["t20"] and 13 <= z < 19:
            fecha_sb()
            if categoria is None:
                intro.append(t)                    # subtítulo dos "Tipos" (ex.: comportamentais)
            else:
                fecha_comp()
                cur = {"nome": [t], "efeito": [], "classe": None,
                       "cat": categoria, "pg": s["pg"]}
            continue
        # 5) Tormenta20 ~11: tag de CLASSE (formato compacto)
        if s["t20"] and 10 <= z < 13:
            if cur is not None:
                c = _norm(t)
                cur["classe"] = CLASSES_NORM.get(c, dehyph(t).strip())
            continue
        # 6) corpo IowanOldStyle
        if s["ios"]:
            if dropcap:
                t = dropcap + t.lstrip(); dropcap = ""
            if sb is not None:
                sb["texto"].append(t)
            elif cur is not None:
                cur["efeito"].append(t)
            elif categoria is None:
                intro.append(t)
    flush_hdr(); fecha_comp(); fecha_sb()

    banco = {
        "fonte": FONTE, "livro": "Heróis de Arton", "secao": "Complicações",
        "pagina": PG_INI, "total": len(comps),
        "n_gerais": sum(1 for c in comps if c["categoria"] == "geral"),
        "n_classe": sum(1 for c in comps if c["categoria"] == "classe"),
        "introducao": dehyph(juntar(intro)).strip(),
        "complicacoes": comps,
        "regras_extra": sidebars,
    }
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(comps)} complicações ({banco['n_gerais']} gerais + {banco['n_classe']} de classe) "
          f"-> {OUT.name}")
    print(f"  intro {len(banco['introducao'])}c · {len(sidebars)} caixa(s): "
          f"{[s['titulo'] for s in sidebars]}\n")
    for c in comps:
        cl = f" [{c['classe']}]" if c["classe"] else ""
        print(f"  {c['categoria'][:3]} {c['nome']:<24}{cl:<14} pg{c['pagina']} | {len(c['efeito'])}c")


if __name__ == "__main__":
    main()
