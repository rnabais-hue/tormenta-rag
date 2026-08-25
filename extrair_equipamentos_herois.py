# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA dos NOVOS EQUIPAMENTOS de *Heróis de Arton*
(Cap. 3 "Arsenal dos Heróis", Novos Equipamentos, págs 216–243).

Livro de expansão (fonte="herois-arton", versao=1.1). Layout IowanOldStyle
(corpo/negrito), diferente do núcleo (SourceSansPro). Tabelas de stats saem
com linhas fundidas no find_tables → montamos as linhas por POSIÇÃO-X das
colunas (robusto a nomes que quebram e a células multi-linha).

Método por seção:
  - A TABELA é a lista autoritativa de entidades (nome + stats).
  - As DESCRIÇÕES (nome em IowanOldStyle-Bold terminando em "." + corpo Roman)
    são casadas por slug e anexadas.

Escopo desta fase: Armas & Munições. (Armaduras, Itens Gerais, Superiores,
Capangas e Veículos entram em passos seguintes; Bases fica FORA do Cap 3 por ora.)

Saída: dados/equipamentos_herois.json. NÃO toca no índice FAISS.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "equipamentos_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
VERSAO = "1.1"

# offset: página impressa P -> índice PDF (P+1)
def idx(p): return p + 1


def dehyph(s):
    if not s:
        return ""
    s = re.sub(r"[\xad­]\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ---------------------------------------------------------------------------
# Descrições: nome em IowanOldStyle-Bold terminando em "." → corpo em Roman.
# ---------------------------------------------------------------------------
def extrair_descricoes(doc, pg_ini, pg_fim, excluir=None):
    excluir = set(excluir or [])
    descs = {}
    atual = None
    buf = []
    for pg in range(idx(pg_ini), idx(pg_fim) + 1):
        page = doc[pg]
        H = page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    txt = s["text"]
                    fn = s["font"]
                    sz = s["size"]
                    y = s["bbox"][1]
                    if y < H * 0.05 or y > H * 0.95:
                        continue
                    stripped = txt.strip()
                    # novo item: nome bold Iowan curto terminando em "."
                    if ("IowanOldStyle-Bold" in fn and 8.8 <= sz <= 10.5
                            and stripped.endswith(".") and len(stripped) <= 45
                            and not stripped[:1].islower()):
                        nome = dehyph(stripped.rstrip("."))
                        if nome and nome not in excluir and not nome.startswith("Tabela"):
                            if atual:
                                descs[atual] = dehyph(" ".join(buf))
                            atual = nome
                            buf = []
                            continue
                    if atual and "IowanOldStyle" in fn:
                        buf.append(txt)
    if atual:
        descs[atual] = dehyph(" ".join(buf))
    return descs


# ---------------------------------------------------------------------------
# Tabela de armas: montagem por posição-x das 7 colunas.
# ---------------------------------------------------------------------------
COLS = [  # (nome_col, x_min, x_max)
    ("nome", 0, 190),
    ("preco", 190, 240),
    ("dano", 240, 285),
    ("critico", 285, 330),
    ("alcance", 330, 395),
    ("tipo", 395, 455),
    ("espacos", 455, 9999),
]

def _col(x):
    for nome, lo, hi in COLS:
        if lo <= x < hi:
            return nome
    return "nome"


def _linhas_por_y(page, y_tol=6):
    """Agrupa spans em linhas por proximidade de y; retorna [(y, [(x,txt)])]."""
    spans = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                t = s["text"].strip()
                if t:
                    spans.append((round(s["bbox"][1], 1), round(s["bbox"][0], 1), t))
    spans.sort()
    linhas = []
    for y, x, t in spans:
        if linhas and abs(linhas[-1][0] - y) <= y_tol:
            linhas[-1][1].append((x, t))
        else:
            linhas.append((y, [(x, t)]))
    return linhas


def extrair_tabela_armas(doc, paginas):
    """Lê Tabela 3-1 (Armas) nas páginas dadas → lista de dicts com stats."""
    armas = []
    prof = "Simples"
    empun = "Corpo a Corpo — Leves"
    for pg in paginas:
        page = doc[idx(pg)]
        for y, cells in _linhas_por_y(page):
            cells.sort()
            txt_full = " ".join(t for _, t in cells)
            xs = [x for x, _ in cells]
            # cabeçalho de proficiência (nome à esquerda + "Preço" na 2ª col)
            if "Preço" in txt_full and "Dano" in txt_full:
                if "Simples" in txt_full: prof = "Simples"
                elif "Marciais" in txt_full: prof = "Marcial"
                elif "Exóticas" in txt_full: prof = "Exótica"
                elif "Fogo" in txt_full: prof = "Fogo"
                continue
            # sub-cabeçalho de empunhadura (centralizado, sem preço)
            if ("Corpo a Corpo" in txt_full or "Ataque à Distância" in txt_full) \
                    and not any(190 <= x < 240 for x in xs):
                e = "Corpo a Corpo" if "Corpo a Corpo" in txt_full else "Ataque à Distância"
                if "Leve" in txt_full: sub = "Leves"
                elif "Uma Mão" in txt_full: sub = "Uma Mão"
                elif "Duas Mãos" in txt_full: sub = "Duas Mãos"
                else: sub = ""
                empun = f"{e} — {sub}".strip(" —")
                continue
            # linha de arma: precisa de nome (x<190) + preço (190..240)
            col = {}
            for x, t in cells:
                c = _col(x)
                col.setdefault(c, []).append(t)
            if "nome" not in col or "preco" not in col:
                continue
            nome = dehyph(" ".join(col["nome"]))
            preco = dehyph(" ".join(col.get("preco", ["—"])))
            if not preco.startswith("T$") and preco != "—":
                continue
            armas.append({
                "id": f"equip:herois:{slug(nome)}",
                "tipo": "equipamento",
                "categoria": "arma",
                "nome": nome,
                "proficiencia": prof,
                "empunhadura": empun,
                "preco": preco,
                "dano": dehyph(" ".join(col.get("dano", ["—"]))),
                "critico": dehyph(" ".join(col.get("critico", ["—"]))),
                "alcance": dehyph(" ".join(col.get("alcance", ["—"]))),
                "tipo_dano": dehyph(" ".join(col.get("tipo", ["—"]))),
                "espacos": dehyph(" ".join(col.get("espacos", ["—"]))),
                "pagina": pg,
                "fonte": FONTE,
                "versao": VERSAO,
            })
    return armas


_AMMO_RE = re.compile(r"^(virotes|flechas|balas|pedras|bola de ferro)\b", re.I)

def eh_municao_generica(nome):
    """Munição-padrão do núcleo repetida na Tabela 3-1 (referência, não é item novo)."""
    return bool(_AMMO_RE.match(nome.strip()))


# Colunas da Tabela 3-2: Munições (coluna direita da pág): Item | Preço | Espaços.
COLS_MUNI = [("nome", 280, 415), ("preco", 415, 470), ("espacos", 470, 9999)]

def _col_muni(x):
    for nome, lo, hi in COLS_MUNI:
        if lo <= x < hi:
            return nome
    return None


def extrair_tabela_municoes(doc, pg):
    """Tabela 3-2: Munições especiais (coluna direita, x~290–500)."""
    munis = []
    page = doc[idx(pg)]
    for y, cells in _linhas_por_y(page):
        cells.sort()
        col = {}
        for x, t in cells:
            c = _col_muni(x)
            if c:
                col.setdefault(c, []).append(t)
        if "nome" not in col or "preco" not in col:
            continue
        preco = dehyph(" ".join(col["preco"]))
        if not preco.startswith("T$"):
            continue
        nome = dehyph(" ".join(col["nome"])).lstrip("-–— ").strip()
        if not nome or nome.startswith("Item") or "Muniç" in nome:
            continue
        munis.append({
            "id": f"equip:herois:{slug(nome)}",
            "tipo": "equipamento",
            "categoria": "municao",
            "nome": nome,
            "preco": preco,
            "espacos": dehyph(" ".join(col.get("espacos", ["—"]))),
            "pagina": pg,
            "fonte": FONTE,
            "versao": VERSAO,
        })
    return munis


# Colunas da Tabela 3-3: Armaduras & Escudos.
COLS_ARM = [("nome", 0, 200), ("preco", 200, 270), ("bonus_defesa", 270, 345),
            ("penalidade", 345, 435), ("espacos", 435, 9999)]

def _col_arm(x):
    for nome, lo, hi in COLS_ARM:
        if lo <= x < hi:
            return nome
    return "nome"


def extrair_tabela_armaduras(doc, paginas):
    """Tabela 3-3: Armaduras & Escudos (subcats Leves/Pesadas/Escudos)."""
    itens = []
    subcat = "Armaduras Leves"
    for pg in paginas:
        page = doc[idx(pg)]
        for y, cells in _linhas_por_y(page):
            cells.sort()
            txt_full = " ".join(t for _, t in cells)
            xs = [x for x, _ in cells]
            if "Preço" in txt_full and ("Defesa" in txt_full or "Penalidade" in txt_full):
                continue
            # sub-cabeçalho: linha sem preço "T$" e com nome de subcategoria
            if "T$" not in txt_full:
                if "Armaduras Leves" in txt_full: subcat = "Armaduras Leves"; continue
                if "Armaduras Pesadas" in txt_full: subcat = "Armaduras Pesadas"; continue
                if txt_full.strip() == "Escudos": subcat = "Escudos"; continue
                continue  # outra linha sem preço (texto de descrição vazado) → ignora
            col = {}
            for x, t in cells:
                col.setdefault(_col_arm(x), []).append(t)
            if "nome" not in col or "preco" not in col:
                continue
            preco = dehyph(" ".join(col["preco"]))
            if not preco.startswith("T$"):
                continue
            nome = dehyph(" ".join(col["nome"]))
            cat = "escudo" if subcat == "Escudos" else "armadura"
            itens.append({
                "id": f"equip:herois:{slug(nome)}",
                "tipo": "equipamento",
                "categoria": cat,
                "subcategoria": subcat,
                "nome": nome,
                "preco": preco,
                "bonus_defesa": dehyph(" ".join(col.get("bonus_defesa", ["—"]))),
                "penalidade": dehyph(" ".join(col.get("penalidade", ["—"]))),
                "espacos": dehyph(" ".join(col.get("espacos", ["—"]))),
                "pagina": pg,
                "fonte": FONTE, "versao": VERSAO,
            })
    return itens


def casar_descricoes(itens, descs):
    """Anexa descricao por slug (match exato/contido)."""
    usados = set()
    for it in itens:
        sn = slug(it["nome"])
        best = ""
        for k, v in descs.items():
            sk = slug(k)
            if sk == sn or sk in sn or sn in sk:
                best = v
                usados.add(k)
                break
        it["descricao"] = best
    orfas = {k: v for k, v in descs.items() if k not in usados}
    return orfas


def main():
    print(f"Abrindo {PDF.name}...")
    doc = pymupdf.open(PDF)

    # --- Armas (exclui munição-padrão de referência interleaved na tabela) ---
    print("Extraindo tabela de Armas (Tabela 3-1, págs 218–219)...")
    todas = extrair_tabela_armas(doc, [218, 219])
    armas = [a for a in todas if not eh_municao_generica(a["nome"])]
    # dedupe por slug preservando ordem
    vistos, armas_u = set(), []
    for a in armas:
        if a["id"] in vistos:
            continue
        vistos.add(a["id"]); armas_u.append(a)
    armas = armas_u
    print(f"  -> {len(todas)} linhas na tabela; {len(armas)} armas novas (munição-padrão excluída).")

    print("Extraindo Munições especiais (Tabela 3-2, pág 223)...")
    munis = extrair_tabela_municoes(doc, 223)
    print(f"  -> {len(munis)} munições especiais.")

    print("Extraindo tabela de Armaduras & Escudos (Tabela 3-3, pág 224)...")
    armaduras = extrair_tabela_armaduras(doc, [224])
    print(f"  -> {len(armaduras)} armaduras/escudos.")

    print("Extraindo descrições (págs 216–226)...")
    descs = extrair_descricoes(doc, 216, 226, excluir={
        "Novas Habilidades de Armas", "Armas", "Munições", "Novos Equipamentos",
        "Armaduras & Escudos", "Armaduras e Escudos", "Estatísticas de Escudos"})
    print(f"  -> {len(descs)} blocos de descrição.")

    # habilidades de arma novas (quadro "Novas Habilidades de Armas")
    HAB = {"Ocultável", "Surpreendente"}
    habilidades = []
    for h in HAB:
        if h in descs:
            habilidades.append({
                "id": f"equip:herois:hab:{slug(h)}",
                "tipo": "habilidade_arma",
                "nome": h,
                "descricao": descs[h],
                "pagina": 217,
                "fonte": FONTE, "versao": VERSAO,
            })
    print(f"  -> {len(habilidades)} habilidades de arma novas.")

    itens_desc = armas + munis + armaduras
    orfas = casar_descricoes(itens_desc, descs)
    # descrição combinada "Flechas/Virotes Pesados" cobre ambas as munições pesadas
    comb = next((v for k, v in descs.items() if "Pesados" in k and "/" in k), "")
    if comb:
        for m in munis:
            if "pesad" in slug(m["nome"]) and not m["descricao"]:
                m["descricao"] = comb
    orfas = {k: v for k, v in orfas.items() if k not in HAB and not ("Pesados" in k and "/" in k)}
    com_desc = sum(1 for a in itens_desc if a["descricao"])
    print(f"  -> {com_desc}/{len(itens_desc)} com descrição casada; {len(orfas)} descrições órfãs.")
    if orfas:
        print("     órfãs:", ", ".join(list(orfas)[:20]))

    dados = {
        "fonte": FONTE,
        "livro": "Heróis de Arton",
        "versao": VERSAO,
        "capitulo": "Capítulo 3: Arsenal dos Heróis",
        "secao": "Novos Equipamentos",
        "armas": armas,
        "municoes": munis,
        "armaduras_escudos": armaduras,
        "habilidades_arma": habilidades,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    total = len(armas) + len(munis) + len(armaduras) + len(habilidades)
    print(f"\n[OK] {total} registros gravados em {OUT}")


if __name__ == "__main__":
    main()
