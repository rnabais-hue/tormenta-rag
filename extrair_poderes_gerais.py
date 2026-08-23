# -*- coding: utf-8 -*-
r"""Stage A dos PODERES (categorias GERAIS): extrai os poderes do capítulo
"Perícias & Poderes" (págs 130-143) — que NÃO vêm de classes.json e sim de uma
seção própria do livro, guiada pela TIPOGRAFIA.

Tipografia observada (uniforme nas 5 categorias):
  - Cabeçalho de categoria: Tormenta20-Regular ~27 ("Poderes / de Combate",
    "de Destino", "de Magia", "Concedidos", "da Tormenta"). Vem em 2 spans.
  - Nome do poder: Tormenta20-Regular ~16 (pode ocupar 2 linhas → junta-se).
  - Efeito: IowanOldStyle-Roman ~9.5 (o "Pré-requisito:" é IowanOldStyle-Italic
    seguido do valor roman — fica embutido no efeito e é separado depois).
  - CONCEDIDOS têm, entre o nome e o efeito, um span Tormenta20 ~11 com o(s)
    DEUS(es) concedente(s) — ex.: "Ataque Piedoso" → "Lena, Thyatis". Capturado
    em `deuses` (insumo de elegibilidade por devoção, Stage C).

A intro ("Poderes gerais", "Escolhendo", "Grupos de Poderes") fica ANTES do 1º
cabeçalho ~27 e é ignorada. Ordena por bloco/coluna (como raças/classes) para não
intercalar colunas.

Lê o PDF; escreve dados/poderes_gerais.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
OUT = Path(__file__).parent / "dados" / "poderes_gerais.json"
OUT.parent.mkdir(exist_ok=True)

PG_INI, PG_FIM = 130, 143            # 1-based, inclusive (Cap 3 começa em 144)
CAT = {                              # keyword no cabeçalho ~27 -> categoria
    "combate": "combate", "destino": "destino", "magia": "magia",
    "concedidos": "concedido", "tormenta": "tormenta",
}
# Panteão de Arton (20 deuses) — canonicaliza a caixa dos deuses concedentes,
# que no PDF varia ("Lin-Wu" vs "Lin-wu"). Chave = casefold.
PANTEAO = ["Aharadak", "Allihanna", "Arsenal", "Azgher", "Hyninn", "Kallyadranoch",
           "Khalmyr", "Lena", "Lin-Wu", "Marah", "Megalokk", "Nimb", "Oceano",
           "Sszzaas", "Tanna-Toh", "Tenebra", "Thwor", "Thyatis", "Valkaria", "Wynna"]
_PANTEAO = {d.casefold(): d for d in PANTEAO}


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


def extrair_pre(efeito):
    """Separa 'Pré-requisito(s): X' (texto) do efeito. Devolve (efeito, pre|None)."""
    m = re.search(r"Pré-requisitos?:\s*([^.]+)", efeito)
    if not m:
        return efeito.strip(), None
    pre = m.group(1).strip()
    efeito = re.sub(r"\s*Pré-requisitos?:\s*[^.]+\.?", "", efeito).strip()
    return efeito, pre


def coletar_spans(doc):
    """Spans úteis das págs [PG_INI, PG_FIM], ordenados por bloco/coluna."""
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
                        "text": s["text"],
                    })
    out.sort(key=lambda r: r["key"])
    return out


def tipo_span(s):
    f, z = s["font"], s["size"]
    t20 = "Tormenta20" in f
    if t20 and z >= 24:
        return "cat"
    if t20 and 13 <= z < 20:
        return "nome"
    if t20 and 10 <= z < 13:
        return "deus"
    if "IowanOldStyle" in f and z >= 8.5:
        return "efeito"
    return "ign"          # SourceSans, Spirals, sz21 intro (Tormenta20 20-24), etc.


def main():
    doc = pymupdf.open(PDF)
    spans = coletar_spans(doc)

    poderes = []
    categoria = None            # None enquanto na intro (antes do 1º cabeçalho ~27)
    cur = None                  # poder em construção
    cat_buf = []                # junta os 2 spans do cabeçalho ~27

    def fecha_cat():
        nonlocal categoria, cat_buf
        if cat_buf:
            txt = dehyph(" ".join(cat_buf)).lower()
            for kw, c in CAT.items():
                if kw in txt:
                    categoria = c
                    break
            cat_buf = []

    for s in spans:
        tp = tipo_span(s)
        if tp == "cat":
            if cur:
                poderes.append(cur); cur = None
            cat_buf.append(s["text"])
            continue
        fecha_cat()             # qualquer span não-cat fecha o cabeçalho pendente
        if categoria is None or tp == "ign":
            continue
        if tp == "nome":
            if cur and cur["_nm_fechado"] and (cur["_ef"] or cur["_deus"]):
                poderes.append(cur); cur = None
            if cur is None:
                cur = {"categoria": categoria, "pg": s["pg"] + 1,
                       "_nome": "", "_deus": "", "_ef": "", "_nm_fechado": False}
            cur["_nome"] += s["text"]
        elif tp == "deus" and cur is not None:
            cur["_nm_fechado"] = True
            cur["_deus"] += s["text"]
        elif tp == "efeito" and cur is not None:
            cur["_nm_fechado"] = True
            cur["_ef"] += s["text"]
    if cur:
        poderes.append(cur)

    # normaliza + monta registros
    saida = []
    for p in poderes:
        nome = dehyph(p["_nome"]).rstrip(". ")
        ef, pre = extrair_pre(dehyph(p["_ef"]))
        if not nome or not ef:
            continue
        reg = {
            "id": f"poder:{p['categoria']}:{slug(nome)}",
            "tipo": "poder", "categoria": p["categoria"],
            "nome": nome, "efeito": ef, "pre_requisito": pre,
            "fonte": "nucleo", "versao": "jogo-do-ano-2024", "pagina": p["pg"],
        }
        if p["categoria"] == "concedido":
            deuses = [_PANTEAO.get(d.strip().casefold(), d.strip())
                      for d in re.split(r"[,/]", dehyph(p["_deus"])) if d.strip()]
            reg["deuses"] = deuses
        saida.append(reg)

    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    por = Counter(p["categoria"] for p in saida)
    com_pre = sum(1 for p in saida if p["pre_requisito"])
    print(f"{len(saida)} poderes gerais -> {OUT.name}")
    for c in ["combate", "destino", "magia", "concedido", "tormenta"]:
        print(f"  - {c:<10} {por.get(c,0):>3}")
    print(f"  ({com_pre} com pré-requisito)")
    sem_deus = [p['nome'] for p in saida if p['categoria']=='concedido' and not p.get('deuses')]
    if sem_deus:
        print(f"  ! concedidos SEM deus ({len(sem_deus)}): {sem_deus[:8]}")


if __name__ == "__main__":
    main()
