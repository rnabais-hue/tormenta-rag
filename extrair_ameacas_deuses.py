# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do BESTIÁRIO de *Deuses de Arton* (Cap. 4) — só as CRIATURAS.

Livro de expansão (fonte="deuses-arton"). O Cap. 4 "Ameaças Divinas" (págs 254–317) é
o bestiário divino, em 6 grupos temáticos (Abissais, Aspectos dos Deuses, Celestiais,
Fadas, Gênios, Gigantes). Perigos Complexos (318–320) e a Tabela por ND (321) NÃO são
fichas e ficam fora do escopo.

DIFERENÇA-CHAVE vs. Ameaças de Arton (por que NÃO é um porte direto):
Este livro usa o STAT BLOCK COMPACTO com rótulos em VERSALETE — a maiúscula sai a ~9pt
e a continuação a ~6.3pt (SourceSansPro-Bold-SC700). Achatar spans (como em Ameaças)
embaralha a continuação e perde os espaços internos → o motor aqui é BASE-LINHA e
DIRIGIDO POR RÓTULOS:
  1) Reconstrói cada LINHA concatenando spans em ordem-x (versalete cola certo).
  2) Segmenta criaturas por âncora (Nome Tormenta20 16pt + ND + Tipo/Tamanho).
  3) Classifica cada linha pelo rótulo inicial (Iniciativa/Defesa/PV/...); linhas sem
     rótulo são continuação do bloco anterior. Habilidades = título Bold-SC700 no início
     da linha que NÃO é um rótulo de campo conhecido.

Uso:
    python extrair_ameacas_deuses.py            # grupos-piloto (validar)
    python extrair_ameacas_deuses.py --todos    # todos os grupos de criatura
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

import fontes  # registro de procedência

BASE = Path(__file__).parent
PDF = BASE / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = BASE / "dados" / "ameacas_deuses.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"

# Grupos do Cap. 4 "Ameaças Divinas" (páginas PDF = páginas impressas).
GRUPOS = [
    ("Abissais", 254, 265, True),
    ("Aspectos dos Deuses", 266, 275, True),
    ("Celestiais", 276, 287, True),
    ("Fadas", 288, 299, True),
    ("Gênios", 300, 307, True),
    ("Gigantes", 308, 317, True),
]
GRUPOS_PILOTO = {"Abissais"}

TIPOS = r"Monstro|Humanoide|Animal|Construto|Espírito|Morto-?[Vv]ivo|Aberração|Planta|Elemental|Fada|Verme|Dragão|Gigante|Aspecto"
TAMS = r"Minúsculo|Pequeno|Médio|Grande|Enorme|Colossal"
DASHES = r"‐\-―−‐‑‒–—―−"
ATTR_VAL = rf"([+{DASHES}]?\d+|[{DASHES}]+)"
COL_SPLIT = 280.0  # x que separa colunas: a coluna DIREITA começa em x≈289 (nomes)
#                    e o ND da coluna esquerda fica em x≈233 — split em 280 os separa.


def slug(s):
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.lower().replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def dehyph(s):
    if not s:
        return ""
    s = re.sub(rf"(\w+)[{DASHES}\xad­]\s+(\w+)", r"\1\2", s)
    s = re.sub(r"[\xad­]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _norm_tok(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def limpar_nome(nome, grupo=""):
    nome = nome.strip(" \t.,;:)(")
    for corte in [r".*Tesouro[^.]*\.", r".*para extrair\)\.?", r".*\(Continua[^)]*\)",
                  r".*Car\s*[+\-–]?\d+", r"^\d+\s+"]:
        nome = re.sub(corte, "", nome).strip()
    nome = re.sub(r"\s*ND\s*[\d/S+]+\s*$", "", nome, flags=re.I).strip()
    nome = re.sub(r"^\d+\s+", "", nome).strip()
    ws = nome.split()
    if not ws:
        return ""
    # 1) Descarta prefixo = NOME DO GRUPO vazado como cabeçalho de página.
    if grupo:
        gt = [t for t in (_norm_tok(x) for x in grupo.split()) if t]
        nt = [_norm_tok(x) for x in ws]
        gi = 0
        wi = 0
        while gi < len(gt) and wi < len(ws) - 1:
            if nt[wi] == "":
                wi += 1
                continue
            if nt[wi] == gt[gi]:
                gi += 1
                wi += 1
            else:
                break
        if gi == len(gt) and wi >= 1:
            ws = ws[wi:]
    # 2) Dedup consecutivo simples
    dedup = [ws[0]]
    for w in ws[1:]:
        if w.lower() != dedup[-1].lower():
            dedup.append(w)
    ws = dedup
    low = [w.lower() for w in ws]
    # 3) N-grama LIDERANTE repetido (splash + nome idênticos)
    changed = True
    while changed and len(low) >= 2:
        changed = False
        for k in range(len(low) // 2, 0, -1):
            if low[:k] == low[k:2 * k]:
                ws = ws[k:]
                low = low[k:]
                changed = True
                break
    # 4) Sufixo == prefixo sobreposto
    for k in range(len(low) // 2, 1, -1):
        if low[:k] == low[-k:]:
            ws = ws[:-k]
            low = low[:-k]
            break
    # 5) Metades idênticas
    n = len(ws)
    if n >= 2 and n % 2 == 0 and [w.lower() for w in ws[:n // 2]] == [w.lower() for w in ws[n // 2:]]:
        ws = ws[:n // 2]
    nome = " ".join(ws).strip()
    # 6) Inicial maiúscula (o versalete do nome 16pt às vezes vem minúsculo: aucharai→Aucharai)
    if nome and nome[0].islower():
        nome = nome[0].upper() + nome[1:]
    return nome


# --- Rótulos de campo do stat block compacto (âncoras de início de linha) ----------
# Nota: NÃO usar \b no fim — no versalete o valor cola no rótulo ("Defesa26",
# "Pontosde Vida240", "Deslocamento12m") e \b (letra→dígito) não casa.
FIELD_LABELS = [
    ("iniciativa", re.compile(r"^Iniciativa", re.I)),
    ("defesa", re.compile(r"^Defesa", re.I)),
    ("pm", re.compile(r"^Pontos\s*de\s*Mana", re.I)),
    ("pv", re.compile(r"^Pontos\s*de\s*Vida", re.I)),
    ("deslocamento", re.compile(r"^Deslocamento", re.I)),
    ("corpo", re.compile(r"^Corpo\s*a\s*Corpo", re.I)),
    ("distancia", re.compile(r"^[ÀA]\s*Dist[âa]ncia", re.I)),
    ("atributos", re.compile(rf"^For\s*[+{DASHES}]?\d", re.I)),
    ("pericias", re.compile(r"^Per[íi]cias", re.I)),
    ("equipamento", re.compile(r"^Equipamento", re.I)),
    ("tesouro", re.compile(r"^Tesouro", re.I)),
]


def _label_da_linha(txt):
    for nome, pat in FIELD_LABELS:
        if pat.match(txt):
            return nome
    return None


def reconstruir_linhas(doc, p0, p1):
    """Reconstrói as linhas de texto de cada página (col1 depois col2) preservando a
    ordem-x DENTRO da linha — essencial para o versalete colar (maiúscula 9pt +
    continuação 6.3pt). Retorna uma lista achatada de itens-linha em ordem de leitura."""
    itens = []
    for pno in range(p0, p1 + 1):
        page = doc[pno - 1]
        blocks = page.get_text("dict")["blocks"]

        # Splash decorativo: se a página tem NOME em tamanho de ficha (Tormenta20 13–20),
        # os Tormenta20 >=20 são títulos-splash e saem. Página de BOSS (só nome grande):
        # o >=20 é o único nome e fica.
        pagina_tem_nome_ficha = False
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    if (s["font"].startswith("Tormenta20") and 12.5 < s["size"] < 20
                            and s["text"].strip()):
                        pagina_tem_nome_ficha = True

        col1, col2 = [], []
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                spans = [s for s in l["spans"] if s["text"].strip()]
                if not spans:
                    continue
                # Só linhas de FICHA: Tormenta20 (nome/ND) ou SourceSansPro (stat block).
                # Descarta corpo/flavor (IowanOldStyle) e cabeçalhos (Helvetica).
                torm = [s for s in spans if s["font"].startswith("Tormenta20")]
                ssp = [s for s in spans if s["font"].startswith("SourceSansPro")]
                if not torm and not ssp:
                    continue

                max_torm = max((s["size"] for s in torm), default=0)
                # Nome/ND: linha Tormenta20. Splash decorativo descartado.
                is_nome = False
                if max_torm >= 12.5:
                    if max_torm >= 20 and pagina_tem_nome_ficha:
                        continue  # splash decorativo
                    is_nome = True

                txt = "".join(s["text"] for s in spans)
                txt = re.sub(r"[\xad­]", "", txt)
                txt_norm = re.sub(r"\s+", " ", txt).strip()
                if not txt_norm:
                    continue

                # Prefixo Bold-SC700 no início da linha (nome de habilidade / rótulo).
                bold_prefix = ""
                for s in spans:
                    if s["font"].startswith("SourceSansPro") and "Bold" in s["font"]:
                        bold_prefix += s["text"]
                    elif s["text"].strip():
                        break
                bold_prefix = re.sub(r"\s+", " ", bold_prefix).strip()

                x0 = min(s["bbox"][0] for s in spans)
                y0 = l["bbox"][1]
                item = {
                    "t": txt_norm,
                    "sz": max_torm if is_nome else (spans[0]["size"]),
                    "x0": x0,
                    "y0": y0,
                    "pno": pno,
                    "kind": "nome" if is_nome else "stat",
                    "bold_prefix": bold_prefix,
                    "label": None if is_nome else _label_da_linha(txt_norm),
                }
                (col1 if x0 < COL_SPLIT else col2).append(item)

        col1.sort(key=lambda s: s["y0"])
        col2.sort(key=lambda s: s["y0"])
        itens.extend(col1)
        itens.extend(col2)
    return itens


def norm_val(v):
    if not v:
        return ""
    v = v.strip()
    v = re.sub(rf"^[{DASHES}]+$", "—", v)
    v = re.sub(rf"^[{DASHES}](\d+)$", r"-\1", v)
    return v


def _sem_rotulo(txt, label_regex):
    """Remove o rótulo do início do texto do bloco."""
    return re.sub(label_regex, "", txt, count=1, flags=re.I).strip(" :.,")


def campos_e_habilidades(items, tipo_txt):
    """Classifica as linhas de UMA criatura em campos + habilidades.

    `tipo_txt` = texto da linha Tipo/Tamanho (primeira linha após o ND).
    Estratégia: acumula linhas em blocos; um bloco novo começa quando a linha tem um
    rótulo de campo conhecido OU um título Bold-SC700 que não é rótulo (=habilidade).
    Linhas sem rótulo/título são continuação do bloco corrente.
    """
    # --- Tipo / subtipo / tamanho / papel ---
    tipo = "Monstro"
    m = re.search(rf"({TIPOS})", tipo_txt, re.I)
    if m:
        tipo = m.group(1).capitalize()
    m_sub = re.search(rf"(?:{TIPOS})\s*\(([^)]+)\)", tipo_txt, re.I)
    subtipo = m_sub.group(1).strip() if m_sub else ""
    m_tam = re.search(rf"({TAMS})", tipo_txt, re.I)
    tamanho = m_tam.group(1).capitalize() if m_tam else "Médio"
    m_papel = re.search(r"\((Solo|Lacaio|Bando)\)", tipo_txt, re.I)
    papel = m_papel.group(1).capitalize() if m_papel else "Normal"

    # --- Acumular blocos ---
    blocos = []          # [(label, texto)]  label=None p/ habilidade
    habs_raw = []        # [(titulo, texto)]
    cur_kind = None      # "campo" | "hab" | None
    cur_label = None
    cur_titulo = None
    cur_txt = []

    def flush():
        nonlocal cur_kind, cur_label, cur_titulo, cur_txt
        if cur_kind == "campo":
            blocos.append((cur_label, dehyph(" ".join(cur_txt))))
        elif cur_kind == "hab" and cur_titulo:
            desc = dehyph(" ".join(cur_txt))
            habs_raw.append((cur_titulo, desc))
        cur_kind = cur_label = cur_titulo = None
        cur_txt = []

    labels_vistos = set()
    for it in items:
        txt = it["t"]
        label = it["label"]
        bp = it["bold_prefix"]
        # Só abre bloco novo para um rótulo AINDA NÃO VISTO. Uma linha de prosa que só
        # começa com a palavra "Defesa"/"Deslocamento" (continuação de resistências que
        # quebra de linha) NÃO deve reabrir o campo e sobrescrever o valor real — vira
        # continuação do bloco corrente (mantém a 1ª ocorrência, com o número).
        if label and label not in labels_vistos:
            flush()
            cur_kind = "campo"
            cur_label = label
            cur_txt = [txt]
            labels_vistos.add(label)
        elif bp and len(bp) >= 3 and not bp[0].isdigit() and _label_da_linha(bp) is None:
            # Título Bold-SC700 que não é rótulo de campo -> habilidade/ataque especial.
            flush()
            cur_kind = "hab"
            cur_titulo = re.sub(r"[:.\s]+$", "", bp).strip()
            resto = txt[len(bp):].strip() if txt.startswith(bp) else txt
            cur_txt = [resto]
        else:
            if cur_kind:
                cur_txt.append(txt)
    flush()

    # --- Consolidar campos ---
    campo = {lbl: txt for lbl, txt in blocos}

    ini = perc = sentidos = ""
    if "iniciativa" in campo:
        t = campo["iniciativa"]
        m = re.search(rf"Iniciativa\s*([+{DASHES}]?\d+)", t, re.I)
        ini = norm_val(m.group(1)) if m else ""
        m = re.search(rf"Percep[çc][ãa]o\s*([+{DASHES}]?\d+)\s*,?\s*(.*)$", t, re.I)
        if m:
            perc = norm_val(m.group(1))
            sentidos = m.group(2).strip(" .,")

    defesa = fort = refl = vont = resist = ""
    if "defesa" in campo:
        t = campo["defesa"]
        m = re.search(rf"Defesa\s*(\d+|[{DASHES}])", t, re.I)
        defesa = norm_val(m.group(1)) if m else ""
        m = re.search(rf"Fort\.?\s*([+{DASHES}]?\d+|[{DASHES}])\s*,\s*Ref\.?\s*([+{DASHES}]?\d+|[{DASHES}])\s*,\s*Von\.?\s*([+{DASHES}]?\d+|[{DASHES}])\s*,?\s*(.*)$", t, re.I)
        if m:
            fort, refl, vont = norm_val(m.group(1)), norm_val(m.group(2)), norm_val(m.group(3))
            resist = m.group(4).strip(" .,")

    def _num(lbl):
        if lbl not in campo:
            return ""
        m = re.search(r"(\d[\d\.]*)", campo[lbl])
        if m:
            return m.group(1).replace(".", "")
        return "—" if re.search(rf"[{DASHES}]", campo[lbl]) else ""

    pv = _num("pv")
    pm = _num("pm")

    desloc = _sem_rotulo(campo.get("deslocamento", ""), r"^Deslocamento") if "deslocamento" in campo else ""
    cac = _sem_rotulo(campo.get("corpo", ""), r"^Corpo\s*a\s*Corpo") if "corpo" in campo else ""
    dist = _sem_rotulo(campo.get("distancia", ""), r"^[ÀA]\s*Dist[âa]ncia") if "distancia" in campo else ""
    pericias = _sem_rotulo(campo.get("pericias", ""), r"^Per[íi]cias") if "pericias" in campo else ""
    equip = _sem_rotulo(campo.get("equipamento", ""), r"^Equipamento\.?") if "equipamento" in campo else ""
    tesouro = _sem_rotulo(campo.get("tesouro", ""), r"^Tesouro") if "tesouro" in campo else ""

    atributos = {}
    if "atributos" in campo:
        pat = rf"For\s*{ATTR_VAL}\s*,\s*Des\s*{ATTR_VAL}\s*,\s*Con\s*{ATTR_VAL}\s*,\s*Int\s*{ATTR_VAL}\s*,\s*Sab\s*{ATTR_VAL}\s*,\s*Car\s*{ATTR_VAL}"
        m = re.search(pat, campo["atributos"], re.I)
        if m:
            atributos = {k: norm_val(m.group(i + 1)) for i, k in
                         enumerate(["for", "des", "con", "int", "sab", "car"])}

    habs = [{"nome": n, "descricao": d} for n, d in habs_raw if len(d) > 2]

    return dict(tipo_criatura=tipo, subtipo=subtipo, tamanho=tamanho, papel=papel,
                iniciativa=ini, percepcao=perc, sentidos=sentidos, defesa=defesa,
                fortitude=fort, reflexos=refl, vontade=vont, resistencias=resist,
                pv=pv, pm=pm, deslocamento=desloc, corpo_a_corpo=cac, distancia=dist,
                atributos=atributos, pericias=pericias, equipamento=equip, tesouro=tesouro,
                habilidades=habs)


def segmentar_criaturas(itens, grupo):
    """Segmenta os itens-linha em criaturas. Âncora = linha-nome (Tormenta20 >=13, não
    ND) seguida, nas próximas linhas, por um ND e/ou uma linha Tipo/Tamanho."""
    anchors = []  # (idx_nome, idx_apos_nome, nome_cand, pno)
    i = 0
    n = len(itens)
    while i < n:
        s = itens[i]
        if s["kind"] == "nome" and s["sz"] >= 13.0 and not re.match(r"^ND\b", s["t"], re.I):
            # coletar linhas-nome consecutivas (nome pode ocupar 2 linhas) até o ND
            j = i
            nome_spans = []
            while j < n and itens[j]["kind"] == "nome" and not re.match(r"^ND\b", itens[j]["t"], re.I):
                nome_spans.append(itens[j]["t"])
                j += 1
            nome_cand = " ".join(nome_spans).strip()
            proximos = " ".join(x["t"] for x in itens[j:j + 8])
            has_nd = bool(re.search(r"ND\s*[\d/S+]+", proximos, re.I))
            has_tipo = bool(re.search(rf"(?:{TIPOS})\s*(?:\([^)]{{0,40}}\))?\s*(?:{TAMS})", proximos, re.I))
            if has_nd or has_tipo:
                anchors.append((i, j, nome_cand, s["pno"]))
                i = j - 1
        i += 1

    criaturas = []
    for k, (start_i, apos_nome_i, raw_nome, pno) in enumerate(anchors):
        next_start = anchors[k + 1][0] if k + 1 < len(anchors) else n
        bloco = itens[apos_nome_i:next_start]

        # ND: procurar nas primeiras linhas do bloco
        texto_ini = " ".join(x["t"] for x in bloco[:6])
        m_nd = re.search(r"ND\s*([\d/S+]+)", texto_ini)
        if m_nd:
            nd = m_nd.group(1)
        elif re.search(rf"ND\s*[{DASHES}]", texto_ini):
            nd = "—"  # criatura sem ND (ex.: parceiro/não-combatente)
        else:
            nd = "?"

        # Tipo/Tamanho: primeira linha 'stat' com um TIPO+TAM (após remover a linha ND)
        tipo_txt = ""
        body_items = []
        for x in bloco:
            if not tipo_txt and re.search(rf"(?:{TIPOS})", x["t"], re.I) and re.search(rf"(?:{TAMS})", x["t"], re.I) and x["label"] is None:
                tipo_txt = x["t"]
                continue
            if re.match(r"^ND\b", x["t"], re.I):
                continue
            body_items.append(x)

        nome = limpar_nome(raw_nome, grupo)
        if not nome or len(nome) < 3:
            continue

        campos = campos_e_habilidades(body_items, tipo_txt)
        criaturas.append({
            "id": f"deuarton_{slug(nome)}",
            "tipo": "ameaca",
            "fonte": FONTE,
            "nome": nome,
            "grupo": grupo,
            "nd": nd,
            "pagina": pno,
            **campos,
        })
    return criaturas


OUT_PENDENTES = BASE / "dados" / "ameacas_deuses_pendentes.json"


def esta_completa(c):
    """Ficha completa = ND válido + Defesa + PV. (O formato compacto às vezes omite o
    array de atributos; não exigimos atributos para não perder fichas legítimas.)

    Exceção "stat-light": criaturas não-combatentes (ex.: Luminar) trazem Defesa/PV/ND
    como "—". Admite-se a ficha se tiver Iniciativa + Tipo detectado + >=2 habilidades —
    o que distingue uma ficha real de um cabeçalho-splash (sem Iniciativa nem habilidades)."""
    if (c.get("nd") not in (None, "", "?") and bool(c.get("defesa")) and bool(c.get("pv"))):
        return True
    return (bool(c.get("iniciativa")) and c.get("tipo_criatura") not in (None, "", "Monstro")
            and len(c.get("habilidades") or []) >= 2)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    todos = "--todos" in sys.argv
    doc = pymupdf.open(str(PDF))
    alvo = [g for g in GRUPOS if g[3] and (todos or g[0] in GRUPOS_PILOTO)]
    print(f"Extraindo {'TODOS os grupos' if todos else 'grupos-piloto'} de {PDF.name}")
    print(f"Fonte: {FONTE} ({fontes.titulo(FONTE)})\n")

    todas = []
    for nome, p0, p1, _ in alvo:
        itens = reconstruir_linhas(doc, p0, p1)
        cs = segmentar_criaturas(itens, nome)
        print(f"  {nome:22s} págs {p0:3d}-{p1:3d}: {len(cs):2d} criaturas")
        todas.extend(cs)

    completas = [c for c in todas if esta_completa(c)]
    pendentes = [c for c in todas if not esta_completa(c)]

    banco = {"fonte": FONTE, "livro": fontes.titulo(FONTE),
             "total_criaturas": len(completas), "criaturas": completas}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

    banco_pend = {"fonte": FONTE, "livro": fontes.titulo(FONTE),
                  "total_criaturas": len(pendentes), "criaturas": pendentes}
    OUT_PENDENTES.write_text(json.dumps(banco_pend, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nTotal bruto: {len(todas)} criaturas")
    print(f"  Completas (-> índice): {len(completas)} -> {OUT.name}")
    print(f"  Pendentes (isoladas) : {len(pendentes)} -> {OUT_PENDENTES.name}")


if __name__ == "__main__":
    main()
