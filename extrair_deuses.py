# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA dos 20 DEUSES de Tormenta20 (núcleo), guiada pela
TIPOGRAFIA. Seção "Deuses", págs 102–111.

Tipografia = schema:
  - Nome do deus: Tormenta20-Regular ~21 E pertencente ao PANTEÃO (as 20
    divindades). Assim a intro ("Escolhendo seu deus", "Características dos
    deuses", cujos cabeçalhos também são ~21) é ignorada.
  - Campos rotulados em negrito ~9.5 (podem vir partidos em 2 spans; pula-se todo
    span negrito, trocando de campo só no rótulo conhecido):
      Crenças e Objetivos / Símbolo Sagrado / Canalizar Energia / Arma Preferida /
      Devotos / Poderes Concedidos / Obrigações & Restrições.
  - Lore: IowanOldStyle-Roman ~9.5 antes do 1º rótulo.

`devotos` (raças/classes que podem seguir) e `poderes_concedidos` são parseados em
listas; `energia` é o enum Positiva|Negativa|Qualquer. Ordena por bloco/coluna.

Lê o PDF; escreve dados/deuses.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
OUT = Path(__file__).parent / "dados" / "deuses.json"
OUT.parent.mkdir(exist_ok=True)
BOLD = 2**4
PG_INI, PG_FIM = 102, 111

PANTEAO = ["Aharadak", "Allihanna", "Arsenal", "Azgher", "Hyninn", "Kallyadranoch",
           "Khalmyr", "Lena", "Lin-Wu", "Marah", "Megalokk", "Nimb", "Oceano",
           "Sszzaas", "Tanna-Toh", "Tenebra", "Thwor", "Thyatis", "Valkaria", "Wynna"]

# rótulo (prefixo SEM acento, pois comparo com _norm(texto)) -> campo
LABELS = [("crencas", "crencas"), ("simbolo", "simbolo"), ("canalizar", "energia"),
          ("arma", "arma"), ("devotos", "devotos"),
          ("poderes concedidos", "poderes_concedidos"), ("obrigacoes", "obrigacoes")]


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _norm(s):
    s = dehyph(s).lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return s


_PANTEAO_N = {_norm(d): d for d in PANTEAO}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", _norm(s)).strip("-")


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
                    if not s["text"].strip() or s["size"] <= 8.4:
                        continue
                    y = s["bbox"][1]
                    if y < H * 0.05 or y > H * 0.95:
                        continue
                    out.append({
                        "key": (pg, bcol, round(by0, 1), li, si),
                        "pg": pg, "size": s["size"], "font": s["font"],
                        "bold": bool(s["flags"] & BOLD), "text": s["text"],
                    })
    out.sort(key=lambda r: r["key"])
    return out


def _lista(txt):
    return [x.strip(" .") for x in re.split(r"[,;]", dehyph(txt)) if x.strip(" .")]


def _carregar_concedidos_canon():
    """Nomes canônicos dos poderes concedidos (sentence case, da entrada do
    poder) para casar a caixa da tabela dos deuses (Title Case)."""
    p = Path(__file__).parent / "dados" / "poderes_gerais.json"
    if not p.exists():
        return {}
    m = {}
    for x in json.loads(p.read_text(encoding="utf-8")):
        if x.get("categoria") == "concedido":
            m[_norm(x["nome"])] = x["nome"]
    return m


_CONC_CANON = _carregar_concedidos_canon()


def canon_poder(nome):
    return _CONC_CANON.get(_norm(nome), nome)


def main():
    doc = pymupdf.open(PDF)
    spans = coletar_spans(doc)

    deuses = []
    cur = None
    campo = None

    def fecha():
        nonlocal cur
        if not cur:
            return
        energia = None
        m = re.search(r"(Positiva|Negativa|Qualquer)", dehyph(cur["energia"]), re.I)
        if m:
            energia = m.group(1).capitalize()
        rec = {
            "id": f"deus:{slug(cur['nome'])}", "tipo": "deus", "nome": cur["nome"],
            "fonte": "nucleo", "versao": "jogo-do-ano-2024", "pagina": cur["pg"] + 1,
            "resumo": dehyph(cur["lore"]).strip()[:600],
            "crencas": dehyph(cur["crencas"]).strip(),
            "simbolo": dehyph(cur["simbolo"]).strip(),
            "energia": energia,
            "arma_preferida": dehyph(cur["arma"]).strip().rstrip("."),
            "devotos": _lista(cur["devotos"]),
            "poderes_concedidos": [canon_poder(x) for x in _lista(cur["poderes_concedidos"])],
            "obrigacoes": dehyph(cur["obrigacoes"]).strip(),
        }
        deuses.append(rec)
        cur = None

    for s in spans:
        t20 = "Tormenta20" in s["font"]
        z = s["size"]
        low = _norm(s["text"])
        # nome de deus: Tormenta20 ~21 E no panteão
        if t20 and 19 <= z < 24 and low in _PANTEAO_N:
            fecha()
            cur = {k: "" for k in ("nome", "lore", "crencas", "simbolo", "energia",
                                   "arma", "devotos", "poderes_concedidos", "obrigacoes")}
            cur["nome"] = _PANTEAO_N[low]
            cur["pg"] = s["pg"]
            campo = "lore"
            continue
        if cur is None:
            continue
        if t20 and z >= 15:                 # outro título grande (ignora)
            continue
        if s["bold"]:                        # rótulo (pode vir partido) → só troca campo no conhecido
            for pref, nome_campo in LABELS:
                if low.startswith(pref):
                    campo = nome_campo
                    break
            continue
        if "IowanOldStyle" not in s["font"]:
            continue
        if campo:
            cur[campo] += s["text"]
    fecha()

    OUT.write_text(json.dumps(deuses, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(deuses)} deuses -> {OUT.name}\n")
    for d in deuses:
        print(f"  - {d['nome']:<14} pg{d['pagina']:>3} | {d['energia'] or '?':<8} | "
              f"arma: {d['arma_preferida'][:14]:<14} | {len(d['devotos'])} devotos | "
              f"{len(d['poderes_concedidos'])} poderes")


if __name__ == "__main__":
    main()
