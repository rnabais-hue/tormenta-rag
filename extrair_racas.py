# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das raças de Tormenta20 (núcleo).

Estratégia (guiada pela tipografia, não pelo TOC quebrado):
  - Região de raças = doc[24]..doc[36] (capítulo).
  - NOME de raça = span na fonte Tormenta20, tamanho >= 20, que não seja um
    marcador de seção (stoplist). Layout A: nome em ~27 (1 raça/página);
    Layout B "Raças Extras": nome em ~21 (várias/página, cruza páginas).
  - Ordena todos os spans em ordem de leitura (página, coluna, y, x) e fatia
    o conteúdo de cada raça entre âncoras de nome consecutivas.
  - Dentro da raça: o LORE não tem negrito -> o 1º span em negrito inicia o
    bloco mecânico. A 1ª "frase" em negrito, se casar 'Atributo ±N', são os
    MODIFICADORES; o resto alterna nome(negrito) -> efeito(roman).

Saída: JSON (lista de raças). NÃO toca no índice FAISS.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
OUT = Path(__file__).parent / "dados" / "racas.json"
OUT.parent.mkdir(exist_ok=True)
PAG_INI, PAG_FIM = 24, 36          # 0-based, inclusivo (capítulo de raças)

BOLD, ITAL = 2**4, 2**1
ATR = r"For[çc]a|Destreza|Constitui[çc][ãa]o|Intelig[êe]ncia|Sabedoria|Carisma"
STOP = re.compile(
    r"^(Habilidades|de Raça|das Raças|Características|Escolhendo|Raças Extras|"
    r"Raças|Classes|das Classes|SUBINDO|Nível de|Personagem)\b", re.I)

def dehyph(s):
    s = re.sub("[­�]\\s*", "", s)    # soft-hyphen (U+00AD) e seu mojibake (U+FFFD): junta a palavra
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)      # hífen de quebra com espaço ("aventurando- se" -> "aventurando-se")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def coletar_spans(doc):
    """Todos os spans úteis, ordenados por BLOCO (frame) e não por span solto.
    Crucial nas páginas compactas: dois frames de raças diferentes podem se
    sobrepor em x e intercalar linhas; agrupar por bloco os separa. Cada bloco
    é atribuído a uma coluna pelo seu x0 e ordenado por (página, coluna, y0)."""
    out = []
    for pg in range(PAG_INI, PAG_FIM + 1):
        page = doc[pg]; W, H = page.rect.width, page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0: continue
            bx0, by0 = b["bbox"][0], b["bbox"][1]
            bcol = 0 if bx0 < W*0.40 else 1   # calha larga: col.esq ~x51-87, col.dir ~x289+
            for li, l in enumerate(b["lines"]):
                for si, s in enumerate(l["spans"]):
                    if not s["text"].strip(): continue
                    if s["size"] <= 8.2: continue
                    if "SourceSans" in s["font"] or "Spirals" in s["font"]: continue
                    y = s["bbox"][1]
                    if y < H*0.06 or y > H*0.94: continue     # cabeçalho/rodapé
                    out.append({
                        "key": (pg, bcol, round(by0, 1), li, si),
                        "pg": pg, "size": s["size"], "font": s["font"],
                        "bold": bool(s["flags"] & BOLD),
                        "ital": bool(s["flags"] & ITAL),
                        "text": s["text"],
                    })
    out.sort(key=lambda r: r["key"])
    return out

def eh_nome(s):
    return ("Tormenta20" in s["font"] and s["size"] >= 20
            and not STOP.match(dehyph(s["text"])))

def eh_estrutural(s):
    """Span de título/marcador de seção (ex.: 'Habilidades de Raça', 'Raças
    Extras') — deve ser removido do corpo para não vazar em resumo/efeitos."""
    return (("Tormenta20" in s["font"] and s["size"] >= 18)
            or STOP.match(dehyph(s["text"])))

def limpar_resumo(txt):
    # apara fragmento de palavra quebrada que sobra no início (ex.: 'ogs") são...')
    txt = re.sub(r'^[a-zà-ÿ]{0,4}["”\')]+[,.]?\s+', "", txt)
    return txt.strip()[:700]


def corrigir_artefatos(rec):
    """Correções PONTUAIS de artefatos do PDF que escapam aos filtros tipográficos.
    Restritas por nome de raça (auditáveis; não afetam as demais). Não dá para
    generalizar por itálico: nomes de magia nas habilidades também são itálicos."""
    if rec["nome"].startswith("Lefou") and rec["resumo"].startswith("Sir "):
        # legenda de arte "— Sir Porti…": só "Sir" (roman) vaza no início do resumo
        rec["resumo"] = rec["resumo"][len("Sir "):]
    if rec["nome"].startswith("Medusa"):
        for h in rec["habilidades"]:
            # a palavra-chave de jogo "Veneno" (itálica) fecha "Natureza Venenosa"
            h["efeito"] = re.sub(r"\s*Veneno\.\s*$", "", h["efeito"]).rstrip()
    return rec

def parse_raca(nome, pagina, spans):
    """spans = conteúdo da raça em ordem de leitura (sem o span do nome)."""
    spans = [s for s in spans if not eh_estrutural(s)]   # tira marcadores/títulos vazados
    # 1º negrito inicia a mecânica; antes disso é lore (resumo = roman não-itálico)
    b0 = next((i for i, s in enumerate(spans) if s["bold"]), None)
    resumo = ""
    if b0 is not None:
        roman = [s["text"] for s in spans[:b0] if not s["ital"] and not s["bold"]]
        resumo = limpar_resumo(dehyph(" ".join(roman)))
    mech = spans[b0:] if b0 is not None else []

    # modificadores = 1ª sequência em negrito, até fechar a frase (ponto)
    modificadores, j = {}, 0
    mtxt = ""
    while j < len(mech) and mech[j]["bold"]:
        mtxt += mech[j]["text"]; j += 1
        if "." in mech[j-1]["text"]:
            break
    def _mods(txt):
        d = {}
        for atr, sig, val in re.findall(rf"({ATR})\s*([+\-–])\s*(\d)", dehyph(txt)):
            d[dehyph(atr)] = int(("-" if sig in "-–" else "+") + val)
        return d
    variantes = {}
    mtxt_c = dehyph(mtxt)
    flex_m = re.search(r"em\s+(?:dois|tr[êe]s|quatro)\s+atributos\s+diferentes"
                       r"(?:\s*\(exceto[^)]*\))?", mtxt_c, re.I)
    has_fixed = re.search(rf"({ATR})\s*[+\-–]\s*\d", mtxt_c)
    is_subraca = "(" in mtxt_c and ";" in mtxt_c and re.search(ATR, mtxt_c)
    if is_subraca:                               # "... (Aggelus); ... (Sulfure)"
        for parte in mtxt_c.split(";"):
            m = re.search(r"\(([^)]+)\)", parte)
            if m:
                variantes[m.group(1).strip()] = _mods(parte)
    elif flex_m or has_fixed:
        if flex_m:
            modificadores["_flexivel"] = "+1 " + dehyph(flex_m.group(0))
        modificadores.update(_mods(mtxt_c))
    else:
        j = 0   # não eram modificadores: 1ª habilidade começa no 1º negrito

    # habilidades: nome(negrito) -> efeito(demais) até o próximo negrito
    habs, cur = [], None
    for s in mech[j:]:
        if s["bold"]:
            if cur is None or cur["_ef"].strip():
                cur = {"nome": "", "_ef": ""}; habs.append(cur)
            elif cur["_ef"] == "":   # negrito seguido de negrito = nome multi-span
                pass
            cur["nome"] += s["text"]
        else:
            if cur is None:
                cur = {"nome": "", "_ef": ""}; habs.append(cur)
            cur["_ef"] += s["text"]
    habilidades = []
    for h in habs:
        nm = dehyph(h["nome"]).rstrip(". ")
        ef = dehyph(h["_ef"])
        if nm and ef:
            habilidades.append({"nome": nm, "efeito": ef})

    slug = re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")
    rec = {
        "id": f"raca:{slug}", "tipo": "raca", "nome": nome,
        "fonte": "nucleo", "versao": "jogo-do-ano-2024", "pagina": pagina,
        "modificadores": modificadores, "resumo": resumo,
        "habilidades": habilidades,
    }
    if variantes:
        rec["modificadores_variantes"] = variantes
    return corrigir_artefatos(rec)

def main():
    doc = pymupdf.open(PDF)
    spans = coletar_spans(doc)
    # índices das âncoras de nome
    anchors = [(i, s) for i, s in enumerate(spans) if eh_nome(s)]
    racas = []
    for a, (idx, s) in enumerate(anchors):
        fim = anchors[a+1][0] if a+1 < len(anchors) else len(spans)
        conteudo = spans[idx+1:fim]
        nome = dehyph(s["text"])
        pagina = s["pg"] + 1
        racas.append(parse_raca(nome, pagina, conteudo))
    OUT.write_text(json.dumps(racas, ensure_ascii=False, indent=2), encoding="utf-8")
    # resumo no console
    print(f"{len(racas)} raças extraídas -> {OUT.name}\n")
    for r in racas:
        if r.get("modificadores_variantes"):
            mods = " | ".join(f"{lbl}: " + ", ".join(f"{k} {v:+d}" for k, v in d.items())
                              for lbl, d in r["modificadores_variantes"].items())
        else:
            partes = []
            if r["modificadores"].get("_flexivel"):
                partes.append(r["modificadores"]["_flexivel"])
            partes += [f"{k} {v:+d}" for k, v in r["modificadores"].items() if k != "_flexivel"]
            mods = ", ".join(partes) or "(sem mods)"
        print(f"- {r['nome']:<14} pág {r['pagina']:>3} | {len(r['habilidades'])} habs | {mods}")

if __name__ == "__main__":
    main()
