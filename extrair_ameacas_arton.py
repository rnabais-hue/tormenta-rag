# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do BESTIÁRIO de *Ameaças de Arton* (v1.0) — só as CRIATURAS.

Livro de expansão (fonte="ameacas-arton"). O Cap. 1 (págs 12–373) é o bestiário,
em ~30 grupos temáticos. Escopo desta família: SÓ as fichas de criatura (as raças
variantes, espalhadas em caixas soltas, ficam de fora por decisão de projeto).

Desafio de layout (diferente do núcleo): 2 colunas, várias variantes por página,
texto-sombra decorativo, nomes quebrados/concatenados, blocos fora de ordem e
marca-d'água. Estratégia:
  1) Montar o texto de cada grupo SÓ com os spans que compõem o stat block —
     `Tormenta20-Regular` (nome/ND) + `SourceSansPro-*` (ficha) — descartando
     `IowanOldStyle*` (lore/caixas), `Helvetica` (marca-d'água) e SourceSansPro
     tamanho <=8 (sombra decorativa).
  2) Segmentar em criaturas pela ÂNCORA do stat block: `<Tipo> (<sub>)? <Tamanho>`,
     capturando o NOME imediatamente antes e o ND próximo.
  3) Extrair os campos por regex (mesmo formato do núcleo).

Uso:
    python extrair_ameacas_arton.py            # grupos-piloto (validar)
    python extrair_ameacas_arton.py --todos    # todos os grupos de criatura

Lê o PDF; escreve dados/ameacas_arton.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path

import pymupdf

import fontes  # registro de procedência

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Ameacas-de-Arton-v1.0-17-11-2023.pdf"
OUT = BASE / "dados" / "ameacas_arton.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "ameacas-arton"

# Grupos temáticos do Cap. 1 (nome -> (pag_inicial, pag_final)). Derivado do TOC.
# `cria=True` = grupo de criaturas; os demais (regras/perigos) ficam fora do escopo.
GRUPOS = [
    ("Brutos & Indomáveis", 32, 43, True),
    ("Capangas & Bandoleiros", 44, 53, True),
    ("Culto de Aharadak", 54, 65, True),
    ("Dragões", 66, 79, True),
    ("Duyshidakk", 80, 89, True),
    ("Elementais", 90, 103, True),
    ("Ermos", 104, 115, True),
    ("Gnolls", 116, 125, True),
    ("Golens", 126, 137, True),
    ("Igreja de Arsenal", 138, 145, True),
    ("Igreja de Kallyadranoch", 146, 155, True),
    ("Império de Jade", 156, 169, True),
    ("Império de Tauron", 170, 179, True),
    ("Kobolds", 180, 191, True),
    ("Mascotes & Familiares", 192, 199, True),
    ("Masmorras", 200, 211, True),
    ("Montarias", 212, 229, True),
    ("Mortos-Vivos", 230, 243, True),
    ("Mundo Perdido", 244, 253, True),
    ("Piratas & Pistoleiros", 254, 265, True),
    ("Povos-Trovão", 266, 275, True),
    ("Puristas", 276, 285, True),
    ("Reino dos Mortos", 286, 297, True),
    ("Reinos de Moreania", 298, 307, True),
    ("Sanguinárias", 308, 315, True),
    ("Sob as Ondas", 316, 327, True),
    ("Sszzaazitas", 328, 339, True),
    ("Trolls Nobres", 340, 349, True),
    ("Uivantes", 350, 359, True),
]
GRUPOS_PILOTO = {"Dragões", "Mortos-Vivos"}

TIPOS = r"Monstro|Humanoide|Animal|Construto|Espírito|Morto-?[Vv]ivo|Aberração|Planta|Elemental|Fada|Verme|Dragão"
TAMS = r"Minúsculo|Pequeno|Médio|Grande|Enorme|Colossal"


def slug(s):
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.lower().replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def dehyph(s):
    s = re.sub(r"(\w+)[-\xad­]\s+(\w+)", r"\1\2", s)
    s = re.sub(r"[\xad­]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _kept_spans(page):
    """Spans da ficha (Tormenta20 nome/ND/tipo + SourceSansPro 9pt) com coordenadas.
    Descarta marca-d'água, lore/caixas, sombra decorativa e nº de página."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        if "lines" not in b:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                fn, sz, tx = s["font"], s["size"], s["text"]
                if not tx.strip():
                    continue
                if fn.startswith("Helvetica") or fn.startswith("IowanOldStyle"):
                    continue
                if fn.startswith("Tormenta20"):
                    if sz <= 12.5:
                        continue
                    kind = "nome"
                elif fn.startswith("SourceSansPro"):
                    if sz <= 8.5 or sz >= 9.8:
                        continue
                    kind = "ficha"
                else:
                    continue
                x0, y0, x1, y1 = s["bbox"]
                out.append({"t": tx, "sz": sz, "x0": x0, "y0": y0, "x1": x1, "kind": kind})
    return out


def _reconstruir(spans):
    """Texto de um conjunto de spans, reordenado por linha visual (faixa de y) e x."""
    spans = sorted(spans, key=lambda s: (round(s["y0"] / 3.0), s["x0"]))
    return dehyph(" ".join(s["t"] for s in spans))


def _is_nome(s):
    t = s["t"].strip()
    return (s["kind"] == "nome" and s["sz"] >= 13.0
            and re.search(r"[A-Za-zÀ-ÿ]", t) and not re.match(r"ND\b", t))


def texto_statblock_do_grupo(doc, p0, p1):  # mantido para compat (não usado no fluxo novo)
    return [(pno, _reconstruir(_kept_spans(doc[pno - 1]))) for pno in range(p0, p1 + 1)]


def _dedup_palavras(nome):
    """Remove repetição de palavras/frases (texto-sombra e título-destaque+variante):
    'Fantasma Fantasma' -> 'Fantasma'; 'Dragão Adulto Dragão Adulto da tirania' ->
    'Dragão Adulto da tirania'; 'A B A B' -> 'A B'."""
    ws = [w for i, w in enumerate(nome.split()) if i == 0 or w != nome.split()[i - 1]]
    # colapsa n-grama LÍDER repetido: se ws[:n]==ws[n:2n], descarta o primeiro
    mudou = True
    while mudou and len(ws) >= 2:
        mudou = False
        for n in range(len(ws) // 2, 0, -1):
            if ws[:n] == ws[n:2 * n]:
                ws = ws[n:]
                mudou = True
                break
    # colapsa frase inteira duplicada: 'A B A B' -> 'A B'
    n = len(ws)
    if n % 2 == 0 and ws[: n // 2] == ws[n // 2:]:
        ws = ws[: n // 2]
    return " ".join(ws)


def limpar_nome(bruto):
    """Do texto imediatamente antes da âncora de tipo, isola o NOME da criatura:
    as últimas palavras iniciando por maiúscula (com conectores de/do/da/e)."""
    bruto = bruto.strip(" \t.,;:)(")
    # corta caudas conhecidas da criatura anterior (tudo até o último marcador some)
    for corte in [r".*Tesouro[^.]*\.", r".*para extrair\)\.?", r".*\(Continua[^)]*\)",
                  r".*Car\s*[+\-–]?\d+", r"^\d+\s+"]:
        bruto = re.sub(corte, "", bruto).strip()
    m = re.search(
        r"([A-ZÀ-Ý][\wÀ-ÿçãõáéíóúâêôà\-]*(?:\s+(?:de|do|da|das|dos|e|[A-ZÀ-Ý][\wÀ-ÿçãõáéíóúâêôà\-]*))*)\s*$",
        bruto,
    )
    nome = (m.group(1) if m else bruto).strip()
    nome = re.sub(r"\s*ND\s*[\d/]+\s*$", "", nome).strip()   # ND colado
    nome = re.sub(r"^\d+\s+", "", nome).strip()               # nº de página no início
    return _dedup_palavras(nome)


def campos(bloco):
    """Extrai os campos do stat block de um SEGMENTO de texto (uma criatura)."""
    def g(pat, grp=1, d=""):
        m = re.search(pat, bloco, re.I)
        return m.group(grp).strip() if m else d

    tipo = g(rf"({TIPOS})\s*(?:\([^)]+\))?\s*(?:{TAMS})", 1, "Monstro").capitalize()
    m_sub = re.search(rf"(?:{TIPOS})\s*\(([^)]+)\)\s*(?:{TAMS})", bloco, re.I)
    subtipo = m_sub.group(1).strip() if m_sub else ""
    tamanho = g(rf"(?:{TIPOS})\s*(?:\([^)]+\))?\s*({TAMS})", 1, "Médio").capitalize()
    papel = g(rf"(?:{TAMS})\s*\((Solo|Lacaio|Bando)\)", 1, "Normal").capitalize()

    ini = g(r"Iniciativa\s*([+\-]?\d+)", 1, "+0")
    m_per = re.search(r"Percepção\s*([+\-]?\d+)(?:,\s*([^\n]+?))?(?=Defesa|Fort)", bloco, re.I)
    perc = m_per.group(1) if m_per else "+0"
    sentidos = (m_per.group(2).strip().rstrip(",") if (m_per and m_per.group(2)) else "")

    defesa = g(r"Defesa\s*(\d+)", 1, "")
    m_res = re.search(r"Fort\.?\s*([+\-]?\d+),\s*Ref\.?\s*([+\-]?\d+),\s*Von\.?\s*([+\-]?\d+)(?:,\s*([^\n]+?))?(?=Pontos de Vida|PV)", bloco, re.I)
    fort = m_res.group(1) if m_res else ""
    refl = m_res.group(2) if m_res else ""
    vont = m_res.group(3) if m_res else ""
    resist = m_res.group(4).strip().rstrip(",") if (m_res and m_res.group(4)) else ""

    pv = g(r"Pontos de Vida\s*(\d+)", 1, "")
    pm = g(r"Pontos de Mana\s*(\d+)", 1, "")
    desloc = g(r"Deslocamento\s*([^\n]+?)(?=Corpo a Corpo|À Distância|For\s|Ataques|$)", 1, "")
    cac = g(r"Corpo a Corpo\s*([^\n]+?)(?=À Distância|For\s|Perícias|Tesouro|$)", 1, "")
    dist = g(r"À Distância\s*([^\n]+?)(?=For\s|Perícias|Tesouro|$)", 1, "")

    # traços usados no PDF: hyphen, figure/en/em dash, barra, minus (U+2010–2015, 2212)
    D = r"‐-―−\-"
    A = rf"([+{D}]?\d+|[{D}])"   # valor de atributo (número com sinal, ou traço = nenhum)
    m_atr = re.search(
        rf"For\s*{A},\s*Des\s*{A},\s*Con\s*{A},\s*Int\s*{A},\s*Sab\s*{A},\s*Car\s*{A}",
        bloco, re.I)
    atributos = ({"for": m_atr.group(1), "des": m_atr.group(2), "con": m_atr.group(3),
                  "int": m_atr.group(4), "sab": m_atr.group(5), "car": m_atr.group(6)}
                 if m_atr else {})

    pericias = g(r"Perícias\s*([^\n]+?)(?=Equipamento|Tesouro|$)", 1, "")
    equip = g(r"Equipamento\.?\s*([^\n]+?)(?=Tesouro|$)", 1, "")
    tesouro = g(r"Tesouro\s*([^\n]+?)(?=\.\s*[A-ZÀ-Ý]|$)", 1, "")

    return dict(tipo_criatura=tipo, subtipo=subtipo, tamanho=tamanho, papel=papel,
                iniciativa=ini, percepcao=perc, sentidos=sentidos, defesa=defesa,
                fortitude=fort, reflexos=refl, vontade=vont, resistencias=resist,
                pv=pv, pm=pm, deslocamento=desloc, corpo_a_corpo=cac, distancia=dist,
                atributos=atributos, pericias=pericias, equipamento=equip, tesouro=tesouro)


TIPO_ANCORA = re.compile(rf"(?:{TIPOS})\s*(?:\([^)]{{0,40}}\))?\s*(?:{TAMS})", re.I)
BANDA = 205.0  # largura de UMA coluna de stat block (pt); < ~221 (distância entre as
               # duas colunas) para não fundi-las e capturar a linha de atributos centralizada


def _nome_do_anchor(anchor, spans_pagina):
    """Junta os spans-nome na MESMA linha visual do anchor (nome pode vir em 2 spans),
    parando antes de um 'ND'. Ex.: 'Dragão Jovem' + 'da Proteção'."""
    y = anchor["y0"]
    mesma_linha = sorted(
        [s for s in spans_pagina if s["kind"] == "nome" and abs(s["y0"] - y) <= 5
         and s["x0"] >= anchor["x0"] - 2],
        key=lambda s: s["x0"])
    partes = []
    for s in mesma_linha:
        if re.match(r"ND\b", s["t"].strip()):
            break
        partes.append(s["t"])
    return limpar_nome(dehyph(" ".join(partes)))


def extrair_grupo(doc, grupo, p0, p1):
    """Coleta geométrica: cada NOME (Tormenta20 >=13pt) é um anchor; o corpo é o
    conjunto de spans ABAIXO dele, na mesma FAIXA DE COLUNA, até o próximo anchor."""
    criaturas = []
    for pno in range(p0, p1 + 1):
        spans = _kept_spans(doc[pno - 1])
        anchors = sorted([s for s in spans if _is_nome(s)], key=lambda s: (s["x0"], s["y0"]))
        # título-destaque 27pt seguido de variante(s) 16pt: NÃO é criatura própria, mas
        # seu texto é o PREFIXO do nome das variantes ("Dragão Filhote" + "do Bosque").
        reais, titulos = [], []
        for a in anchors:
            if a["sz"] >= 22:
                variante = any(v is not a and v["sz"] < 22 and abs(v["x0"] - a["x0"]) < BANDA
                               and 0 <= v["y0"] - a["y0"] <= 60 for v in anchors)
                if variante:
                    titulos.append({"x0": a["x0"], "y0": a["y0"], "txt": _nome_do_anchor(a, spans)})
                    continue
            reais.append(a)
        for a in reais:
            x0 = a["x0"]
            # próximo anchor na mesma coluna, mais abaixo
            abaixo = [s for s in reais if s is not a and abs(s["x0"] - x0) < BANDA and s["y0"] > a["y0"] + 5]
            y_fim = min((s["y0"] for s in abaixo), default=1e9)
            corpo = [s for s in spans
                     if a["x0"] - 15 <= s["x0"] <= a["x0"] + BANDA
                     and a["y0"] - 1 <= s["y0"] < y_fim]
            texto = _reconstruir(corpo)
            nome = _nome_do_anchor(a, spans)
            # prepende o título-destaque acima (mesma coluna) se o nome for só o sufixo
            tit = [t for t in titulos if abs(t["x0"] - a["x0"]) < BANDA and 0 <= a["y0"] - t["y0"] <= 60]
            if tit:
                pref = sorted(tit, key=lambda t: a["y0"] - t["y0"])[0]["txt"]
                if pref and not nome.startswith(pref):
                    nome = _dedup_palavras(f"{pref} {nome}")
            if not nome or len(nome) < 3:
                continue
            m_nd = re.search(r"ND\s*([\d/]+)", texto[:120])
            nd = m_nd.group(1) if m_nd else "?"
            pagina = pno
            c = campos(texto)
            if not c["defesa"] and not c["pv"]:
                continue
            if re.search(r"Tesouro|extrair|Continua|Nenhum|^\d", nome) or nome[0].islower():
                continue
            criaturas.append({
                "id": f"amaarton_{slug(nome)}",
                "tipo": "ameaca", "fonte": FONTE, "nome": nome, "grupo": grupo,
                "nd": nd, "pagina": pagina, **c,
            })
    return criaturas


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    todos = "--todos" in sys.argv
    doc = pymupdf.open(str(PDF))
    alvo = [g for g in GRUPOS if g[3] and (todos or g[0] in GRUPOS_PILOTO)]
    print(f"Extraindo {'TODOS os grupos' if todos else 'grupos-piloto'} de {PDF.name}")
    print(f"Fonte: {FONTE} ({fontes.titulo(FONTE)})\n")

    todas = []
    for nome, p0, p1, _ in alvo:
        cs = extrair_grupo(doc, nome, p0, p1)
        print(f"  {nome:28s} págs {p0}-{p1}: {len(cs)} criaturas")
        todas.extend(cs)

    banco = {"fonte": FONTE, "livro": fontes.titulo(FONTE),
             "total_criaturas": len(todas), "criaturas": todas}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTotal: {len(todas)} criaturas -> {OUT}")


if __name__ == "__main__":
    main()
