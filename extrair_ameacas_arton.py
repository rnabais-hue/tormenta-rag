# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do BESTIÁRIO de *Ameaças de Arton* (v1.0) — só as CRIATURAS.

Livro de expansão (fonte="ameacas-arton"). O Cap. 1 (págs 12–373) é o bestiário,
em ~29 grupos temáticos. Escopo: SÓ as fichas de criatura.

Arquitetura:
  1) Linearização do fluxo de leitura (coluna 1 -> coluna 2 -> próxima página).
  2) Segmentação contínua por âncoras compostas (Nome + ND + Tipo/Tamanho).
  3) Suporte integral a traços unicode (en-dash, em-dash, minus).
  4) Extração de habilidades especiais (spans Bold/Italic) e ataques.

Uso:
    python extrair_ameacas_arton.py            # grupos-piloto (validar)
    python extrair_ameacas_arton.py --todos    # todos os grupos de criatura
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

# Grupos temáticos do Cap. 1 (págs 32–359)
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
DASHES = r"‐\-―−\u2010\u2011\u2012\u2013\u2014\u2015\u2212"
ATTR_VAL = rf"([+{DASHES}]?\d+|[{DASHES}]+)"


def slug(s):
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.lower().replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def dehyph(s):
    if not s:
        return ""
    s = re.sub(rf"(\w+)[{DASHES}\xad\u00ad]\s+(\w+)", r"\1\2", s)
    s = re.sub(r"[\xad\u00ad]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def limpar_nome(nome):
    nome = nome.strip(" \t.,;:)(")
    for corte in [r".*Tesouro[^.]*\.", r".*para extrair\)\.?", r".*\(Continua[^)]*\)",
                  r".*Car\s*[+\-–]?\d+", r"^\d+\s+"]:
        nome = re.sub(corte, "", nome).strip()
    nome = re.sub(r"\s*ND\s*[\d/S+]+\s*$", "", nome, flags=re.I).strip()
    nome = re.sub(r"^\d+\s+", "", nome).strip()
    ws = nome.split()
    if not ws:
        return ""
    dedup = [ws[0]]
    for w in ws[1:]:
        if w.lower() != dedup[-1].lower():
            dedup.append(w)
    nome = " ".join(dedup)
    n = len(dedup)
    if n >= 2 and n % 2 == 0 and dedup[:n//2] == dedup[n//2:]:
        nome = " ".join(dedup[:n//2])
    return nome


def has_separated_labels(c1, c2):
    """Verifica se os rótulos de stat block em C1 estão sem valores em C1 e os valores estão em C2 na mesma linha."""
    rotulos_sem_valor_em_c1 = 0
    for i, s1 in enumerate(c1):
        t1 = s1["t"].strip()
        if t1 in ["Iniciativa", "Defesa", "Pontos de Vida"]:
            tem_valor_em_c1 = False
            for prox in c1[i+1:i+4]:
                if abs(prox["y0"] - s1["y0"]) <= 4 and re.search(r"\d+", prox["t"]):
                    tem_valor_em_c1 = True
                    break
            if not tem_valor_em_c1:
                for s2 in c2:
                    if abs(s2["y0"] - s1["y0"]) <= 6 and re.search(r"\d+", s2["t"]):
                        rotulos_sem_valor_em_c1 += 1
                        break
    return rotulos_sem_valor_em_c1 >= 2


def get_group_stream(doc, p0, p1):
    """Lineariza todos os spans do grupo na ordem de leitura contínua com detecção de tabela larga."""
    stream = []
    for pno in range(p0, p1 + 1):
        page = doc[pno - 1]
        blocks = page.get_text("dict")["blocks"]
        c1, c2 = [], []
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    fn, sz, tx = s["font"], s["size"], s["text"]
                    if not tx.strip():
                        continue
                    if fn.startswith("Helvetica") or fn.startswith("IowanOldStyle"):
                        continue
                    if fn.startswith("Tormenta20") and sz <= 12.5:
                        continue
                    if fn.startswith("SourceSansPro") and (sz <= 8.5 or sz >= 9.8):
                        continue
                    x0, y0, x1, y1 = s["bbox"]
                    kind = "nome" if fn.startswith("Tormenta20") else "ficha"
                    item = {"t": tx, "sz": sz, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                            "kind": kind, "font": fn, "pno": pno}
                    if x0 < 300:
                        c1.append(item)
                    else:
                        c2.append(item)
        c1.sort(key=lambda s: (round(s["y0"] / 3.0), s["x0"]))
        c2.sort(key=lambda s: (round(s["y0"] / 3.0), s["x0"]))

        if has_separated_labels(c1, c2):
            # Tabela Larga: intercalar C1 e C2 por Y horizontal
            all_spans = sorted(c1 + c2, key=lambda s: (round(s["y0"] / 3.0), s["x0"]))
            stream.extend(all_spans)
        else:
            stream.extend(c1)
            stream.extend(c2)
    return stream


def extrair_habilidades(spans):
    """Extrai habilidades especiais a partir de spans negritados e itálicos."""
    habs = []
    ignorar = {
        "iniciativa", "percepção", "percepcao", "defesa", "fort", "fortitude",
        "ref", "reflexos", "von", "vontade", "pontos de vida", "pv", "pontos de mana",
        "pm", "deslocamento", "corpo a corpo", "à distância", "a distancia",
        "atributos", "perícias", "pericias", "equipamento", "tesouro", "for", "des",
        "con", "int", "sab", "car", "nd"
    }
    curr_nome = ""
    curr_desc = []

    for s in spans:
        fn, tx = s["font"], s["t"].strip()
        if not tx:
            continue
        is_bold_title = False
        if "Bold" in fn and s["sz"] >= 8.8:
            tx_clean = re.sub(r"[:\.\t]+$", "", tx).strip()
            tx_lower = tx_clean.lower()
            if not any(tx_lower.startswith(ign) for ign in ignorar) and not re.match(r"^For\s+[+\-–\d]", tx, re.I):
                if len(tx_clean) >= 3 and not tx_clean.isdigit():
                    is_bold_title = True
        elif "It" in fn and any(k in tx for k in ["(Padrão", "(Movimento", "(Completa", "(Reação", "(Livre"]):
            is_bold_title = True
            tx_clean = tx

        if is_bold_title:
            if curr_nome and curr_desc:
                desc_txt = dehyph(" ".join(curr_desc))
                if len(desc_txt) > 3:
                    habs.append({"nome": curr_nome, "descricao": desc_txt})
            curr_nome = tx_clean
            curr_desc = []
        elif curr_nome:
            if re.search(r"\bFor\s*[+\-–\d]", tx, re.I) or any(tx.lower().startswith(ign) for ign in ["perícias", "equipamento", "tesouro"]):
                if curr_nome and curr_desc:
                    desc_txt = dehyph(" ".join(curr_desc))
                    if len(desc_txt) > 3:
                        habs.append({"nome": curr_nome, "descricao": desc_txt})
                curr_nome = ""
                curr_desc = []
            else:
                curr_desc.append(tx)

    if curr_nome and curr_desc:
        desc_txt = dehyph(" ".join(curr_desc))
        if len(desc_txt) > 3:
            habs.append({"nome": curr_nome, "descricao": desc_txt})
    return habs


def campos_do_bloco(texto, spans):
    """Extrai os campos estruturados de uma criatura."""
    def g(pat, grp=1, d=""):
        m = re.search(pat, texto, re.I)
        return m.group(grp).strip() if m else d

    tipo = g(rf"({TIPOS})\s*(?:\([^)]+\))?\s*(?:{TAMS})", 1, "Monstro").capitalize()
    m_sub = re.search(rf"(?:{TIPOS})\s*\(([^)]+)\)\s*(?:{TAMS})", texto, re.I)
    subtipo = m_sub.group(1).strip() if m_sub else ""
    tamanho = g(rf"(?:{TIPOS})\s*(?:\([^)]+\))?\s*({TAMS})", 1, "Médio").capitalize()
    papel = g(rf"(?:{TAMS})\s*\((Solo|Lacaio|Bando)\)", 1, "Normal").capitalize()

    ini = g(r"Iniciativa\s*([+\-]?\d+)", 1, "+0")
    m_per = re.search(r"Percepção\s*([+\-]?\d+)(?:,\s*([^\n]+?))?(?=Defesa|Fort)", texto, re.I)
    perc = m_per.group(1) if m_per else "+0"
    sentidos = (m_per.group(2).strip().rstrip(",") if (m_per and m_per.group(2)) else "")

    D = r"‐\-―−\u2010\u2011\u2012\u2013\u2014\u2015\u2212"
    m_def_b = re.search(rf"Defesa\s+Fort\s+Ref\s+Von\s*(\d+),\s*([+{D}]?\d+),\s*([+{D}]?\d+),\s*([+{D}]?\d+)(?:,\s*([^\n]+?))?(?=Pontos de Vida|PV)", texto, re.I)
    if m_def_b:
        defesa = m_def_b.group(1)
        fort = m_def_b.group(2)
        refl = m_def_b.group(3)
        vont = m_def_b.group(4)
        resist = m_def_b.group(5).strip().rstrip(",") if m_def_b.group(5) else ""
    else:
        defesa = g(r"Defesa\s*([\d\.]+)", 1, "").replace(".", "")
        m_res = re.search(rf"Fort\.?\s*([+{D}]?\d+),\s*Ref\.?\s*([+{D}]?\d+),\s*Von\.?\s*([+{D}]?\d+)(?:,\s*([^\n]+?))?(?=Pontos de Vida|PV)", texto, re.I)
        fort = m_res.group(1) if m_res else ""
        refl = m_res.group(2) if m_res else ""
        vont = m_res.group(3) if m_res else ""
        resist = m_res.group(4).strip().rstrip(",") if (m_res and m_res.group(4)) else ""

    pv = g(r"Pontos de Vida\s*([\d\.]+)", 1, "").replace(".", "")
    pm = g(r"Pontos de Mana\s*([\d\.]+)", 1, "").replace(".", "")
    desloc = g(r"Deslocamento\s*([^\n]+?)(?=Corpo a Corpo|À Distância|For\s|Ataques|Pontos de Mana|$)", 1, "")
    cac = g(r"Corpo a Corpo\s*([^\n]+?)(?=À Distância|For\s|Perícias|Tesouro|[A-Z][a-z]+ \([A-Za-z]+\)|$)", 1, "")
    dist = g(r"À Distância\s*([^\n]+?)(?=For\s|Perícias|Tesouro|[A-Z][a-z]+ \([A-Za-z]+\)|$)", 1, "")

    pat_atr = rf"For\s*{ATTR_VAL},\s*Des\s*{ATTR_VAL},\s*Con\s*{ATTR_VAL},\s*Int\s*{ATTR_VAL},\s*Sab\s*{ATTR_VAL},\s*Car\s*{ATTR_VAL}"
    m_atr = re.search(pat_atr, texto, re.I)

    def norm_val(v):
        if not v:
            return ""
        v = re.sub(rf"^[{DASHES}]+$", "—", v)
        v = re.sub(rf"^[{DASHES}](\d+)$", r"-\1", v)
        return v

    atributos = ({
        "for": norm_val(m_atr.group(1)),
        "des": norm_val(m_atr.group(2)),
        "con": norm_val(m_atr.group(3)),
        "int": norm_val(m_atr.group(4)),
        "sab": norm_val(m_atr.group(5)),
        "car": norm_val(m_atr.group(6)),
    } if m_atr else {})

    pericias = g(r"Perícias\s*([^\n]+?)(?=Equipamento|Tesouro|$)", 1, "")
    equip = g(r"Equipamento\.?\s*([^\n]+?)(?=Tesouro|$)", 1, "")
    tesouro = g(r"Tesouro\s*([^\n]+?)(?=\.\s*[A-ZÀ-Ý]|$)", 1, "")
    habs = extrair_habilidades(spans)

    return dict(tipo_criatura=tipo, subtipo=subtipo, tamanho=tamanho, papel=papel,
                iniciativa=ini, percepcao=perc, sentidos=sentidos, defesa=defesa,
                fortitude=fort, reflexos=refl, vontade=vont, resistencias=resist,
                pv=pv, pm=pm, deslocamento=desloc, corpo_a_corpo=cac, distancia=dist,
                atributos=atributos, pericias=pericias, equipamento=equip, tesouro=tesouro,
                habilidades=habs)


def segmentar_criaturas(stream, grupo):
    """Segmenta o stream linearizado de spans em criaturas individuais."""
    anchors_idx = []
    i = 0
    while i < len(stream):
        s = stream[i]
        if s["kind"] == "nome" and s["sz"] >= 13.0 and not re.match(r"^ND\b", s["t"].strip(), re.I):
            j = i
            nome_spans = []
            while j < len(stream) and stream[j]["kind"] == "nome" and not re.match(r"^ND\b", stream[j]["t"].strip(), re.I):
                nome_spans.append(stream[j]["t"])
                j += 1
            nome_cand = " ".join(nome_spans).strip()
            proximos_txt = " ".join(x["t"] for x in stream[j:j+12])
            has_tipo = bool(re.search(rf"(?:{TIPOS})\s*(?:\([^)]{{0,40}}\))?\s*(?:{TAMS})", proximos_txt, re.I))
            has_nd = bool(re.search(r"ND\s*[\d/S+]+", proximos_txt, re.I)) or bool(re.search(r"ND\s*[\d/S+]+", nome_cand, re.I))
            if has_tipo or has_nd:
                anchors_idx.append((i, j, nome_cand, stream[i]["pno"]))
                i = j - 1
        i += 1

    criaturas = []
    for idx_entry, (start_i, end_nome_i, raw_nome, pno) in enumerate(anchors_idx):
        next_start = anchors_idx[idx_entry + 1][0] if idx_entry + 1 < len(anchors_idx) else len(stream)
        c_spans = stream[start_i:next_start]
        texto = dehyph(" ".join(s["t"] for s in c_spans))

        m_nd = re.search(r"ND\s*([\d/S+]+)", texto[:200])
        nd = m_nd.group(1) if m_nd else "?"

        nome = limpar_nome(raw_nome)
        if not nome or len(nome) < 3 or re.search(r"Tesouro|extrair|Continua|^\d+$", nome):
            continue

        c_fields = campos_do_bloco(texto, c_spans)
        if not c_fields["defesa"] and not c_fields["pv"]:
            continue

        criaturas.append({
            "id": f"amaarton_{slug(nome)}",
            "tipo": "ameaca",
            "fonte": FONTE,
            "nome": nome,
            "grupo": grupo,
            "nd": nd,
            "pagina": pno,
            **c_fields
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
        stream = get_group_stream(doc, p0, p1)
        cs = segmentar_criaturas(stream, nome)
        print(f"  {nome:28s} págs {p0:3d}-{p1:3d}: {len(cs):2d} criaturas")
        todas.extend(cs)

    banco = {"fonte": FONTE, "livro": fontes.titulo(FONTE),
             "total_criaturas": len(todas), "criaturas": todas}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTotal: {len(todas)} criaturas -> {OUT}")


if __name__ == "__main__":
    main()
