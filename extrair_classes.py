# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das classes de Tormenta20 (núcleo).

Estrutura de uma classe (guiada pela tipografia, limites pelo TOC):
  - Página 1: nome (Tormenta20 ~27) + flavor (resumo).
  - Página 2: uma TABELA de progressão (omitida em v1), o marcador
    "Características de Classe" (Tormenta20 ~21) -> stat block (rótulos em
    negrito PV/PM/Perícias/Proficiências -> valor roman), e o marcador
    "Habilidades de Classe" (~21) -> habilidades (nome negrito -> efeito roman,
    incluindo a lista de "• Poderes" selecionáveis dentro do efeito).
  - Páginas seguintes: continuação das habilidades.

Ordenação por BLOCO/frame (como nas raças) para não intercalar colunas.
Saída: classes.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
OUT = Path(__file__).parent / "dados" / "classes.json"
OUT.parent.mkdir(exist_ok=True)
BOLD, ITAL = 2**4, 2**1


def dehyph(s):
    s = re.sub("[­�]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def limpar_resumo(txt):
    txt = re.sub(r'^[a-zà-ÿ]{0,4}["”\')]+[,.]?\s+', "", txt)
    return txt.strip()[:700]


def limites_classes(doc):
    """(nome, pág_ini, pág_fim) de cada classe, a partir do TOC (nível 4 entre
    Arcanista pág 42 e Origens pág 91)."""
    toc = [(t.strip(), p) for lvl, t, p in doc.get_toc() if lvl == 4 and 42 <= p < 91]
    lim = []
    for i, (nome, pg) in enumerate(toc):
        fim = toc[i + 1][1] if i + 1 < len(toc) else 91
        lim.append((nome, pg, fim))
    return lim


def coletar_spans(doc, pg_ini, pg_fim):
    """Spans úteis das páginas [pg_ini, pg_fim) (0-based), ordenados por bloco."""
    out = []
    for pg in range(pg_ini, pg_fim):
        page = doc[pg]; W, H = page.rect.width, page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0: continue
            # QUADROS de opção (familiares, totens, papéis de companheiro,
            # melhorias de arma) usam a fonte IowanOldStyle-Black — são OPÇÕES
            # de um poder, não poderes. Pula o bloco inteiro (senão viram
            # "poderes" falsos ao explodir "Poder de X").
            if any("Black" in s["font"] for l in b["lines"] for s in l["spans"]):
                continue
            bx0, by0 = b["bbox"][0], b["bbox"][1]
            bcol = 0 if bx0 < W * 0.40 else 1
            for li, l in enumerate(b["lines"]):
                for si, s in enumerate(l["spans"]):
                    if not s["text"].strip(): continue
                    if s["size"] <= 8.2: continue
                    if "SourceSans" in s["font"] or "Spirals" in s["font"]: continue
                    y = s["bbox"][1]
                    if y < H * 0.06 or y > H * 0.94: continue
                    out.append({
                        "key": (pg, bcol, round(by0, 1), li, si),
                        "pg": pg, "size": s["size"], "font": s["font"],
                        "bold": bool(s["flags"] & BOLD), "ital": bool(s["flags"] & ITAL),
                        "text": s["text"],
                    })
    out.sort(key=lambda r: r["key"])
    return out


def eh_titulo(s):
    return "Tormenta20" in s["font"] and s["size"] >= 15


# cabeçalho da tabela de progressão e referências cruzadas (sempre em negrito):
_LIXO = re.compile(r"^(Tabela\s+\d|Nível\b|Habilidades de Classe$|Capítulo\s+\d)", re.I)


def eh_lixo(s):
    return s["bold"] and bool(_LIXO.match(dehyph(s["text"])))


def idx_marcador(spans, chave):
    for i, s in enumerate(spans):
        if eh_titulo(s) and chave.lower() in dehyph(s["text"]).lower():
            return i
    return None


def parear_negrito_roman(spans):
    """Alterna nome(negrito) -> efeito(roman) até o próximo negrito. Ignora
    spans de título de seção. Devolve [{nome, efeito}]."""
    itens, cur = [], None
    for s in spans:
        if eh_titulo(s) or eh_lixo(s):
            continue
        if s["bold"]:
            if cur is None or cur["_ef"].strip():
                cur = {"nome": "", "_ef": ""}; itens.append(cur)
            cur["nome"] += s["text"]
        else:
            if cur is None:
                cur = {"nome": "", "_ef": ""}; itens.append(cur)
            cur["_ef"] += s["text"]
    saida = []
    for it in itens:
        nm = dehyph(it["nome"]).rstrip(". ")
        ef = dehyph(it["_ef"])
        if nm and ef and not _LIXO.match(nm):     # pós-filtro (pega lixo multi-span, ex.: "Capítulo 4")
            saida.append({"nome": nm, "efeito": ef})
    return saida


def parse_classe(nome, pg_ini, spans):
    carac_i = idx_marcador(spans, "Caracter")
    hab_i = idx_marcador(spans, "Habilidades")

    # resumo: corpo roman (não itálico) da 1ª página, antes de qualquer marcador
    roman1 = [s["text"] for s in spans
              if s["pg"] == pg_ini and not s["ital"] and not s["bold"] and not eh_titulo(s)]
    resumo = limpar_resumo(dehyph(" ".join(roman1)))

    caracteristicas = {}
    if carac_i is not None and hab_i is not None and carac_i < hab_i:
        for it in parear_negrito_roman(spans[carac_i + 1:hab_i]):
            caracteristicas[it["nome"]] = it["efeito"]

    habilidades = parear_negrito_roman(spans[hab_i + 1:]) if hab_i is not None else []

    slug = re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")
    return {
        "id": f"classe:{slug}", "tipo": "classe", "nome": nome,
        "fonte": "nucleo", "versao": "jogo-do-ano-2024", "pagina": pg_ini + 1,
        "resumo": resumo,
        "caracteristicas": caracteristicas,
        "habilidades": habilidades,
    }


def main():
    doc = pymupdf.open(PDF)
    classes = []
    for nome, pg, fim in limites_classes(doc):
        spans = coletar_spans(doc, pg - 1, fim - 1)      # TOC é 1-based; doc 0-based
        classes.append(parse_classe(nome, pg - 1, spans))
    OUT.write_text(json.dumps(classes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(classes)} classes -> {OUT.name}\n")
    for c in classes:
        cc = list(c["caracteristicas"].keys())
        print(f"- {c['nome']:<11} pág {c['pagina']:>3} | {len(c['habilidades'])} habs | "
              f"caract: {', '.join(cc) if cc else '(nenhuma!)'}")


if __name__ == "__main__":
    main()
