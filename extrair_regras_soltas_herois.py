# -*- coding: utf-8 -*-
r"""Extração dos MÓDULOS MENORES do Cap. 4 (Regras Opcionais) — *Heróis de Arton*.

Fecha o Cap. 4 com as três seções procedurais que faltavam:
  • **Regras Mais Soltas** (282–283): Atributos Variados, Raças Abertas, Devoções Abertas.
  • **Culinária Avançada** (307–311): Fabricando + Ingredientes (lista) + Pratos Especiais
    (lista de pratos com efeito) + Novos Poderes (Ás da Cozinha, Bom de Garfo).
  • **Exploração de Masmorras** (312–315): Percorrendo a Masmorra, Encontros Aleatórios,
    Luz & Escuridão, Ruídos & Barulho, Gerenciamento de Recursos, Duração de Cenas,
    Sobrevivência em Masmorras.

Saídas: `modulos` (procedurais, tipo="regra_opcional") + `pratos` (tipo="prato_especial")
+ `ingredientes` (tipo="ingrediente_culinaria"). Máquina de estados dirigida por cabeçalhos
Tormenta20; 27/21pt = novo módulo, 16pt = subtítulo DOBRADO no módulo pai (evita criar
chunks "Khalmyr"/"Valkaria" que colidiriam com os deuses); nas seções Ingredientes/Pratos
Especiais o modo vira ENTITY (rótulo negrito terminando em "." = entidade). Caixas/tabelas
fora do fluxo via get_drawings(); drop-cap religado.

Saída: dados/regras_soltas_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "regras_soltas_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
FAIXAS = [(282, 283), (307, 315)]
RE_ENT = re.compile(r"^[A-ZÀ-Ú][\wÀ-ÿ][\wÀ-ÿ ()\-]{0,28}\.$")
# seções: título (normalizado) -> (nome exibição, subtipo)
SECOES = {   # "regras mais soltas" é a seção DEFAULT (não precisa de switch)
    "culinaria avancada": ("Culinária Avançada", "culinaria"),
    "exploracao de masmorras": ("Exploração de Masmorras", "exploracao_masmorras"),
}
ENT_ING = "ingredientes"
ENT_PRATO = "pratos especiais"


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
    return re.sub(r"[^a-z ]", "", slug(s).replace("-", " ")).strip()


def _dentro(r, sx, sy):
    return r.x0 - 1 <= sx <= r.x1 + 1 and r.y0 - 1 <= sy <= r.y1 + 1


def coletar_spans(doc):
    out = []
    for p0, p1 in FAIXAS:
        for pg in range(p0 - 1, p1):
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
                        if any(_dentro(r, sx, sy) for r in boxes):
                            continue
                        out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                    "size": s["size"], "font": s["font"],
                                    "t20": "Tormenta20" in s["font"], "ios": "IowanOldStyle" in s["font"],
                                    "bold": bool(s["flags"] & (2**4)) or "Bold" in s["font"],
                                    "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    modulos, pratos, ingredientes = [], [], []
    hdr, hdr_sz = [], 0.0
    secao, subtipo = "Regras Mais Soltas", "regras_soltas"
    modo = "proc"            # proc | ing | prato
    # módulo de intro da 1ª seção (o splash/eixos Complexidade/Desequilíbrio/Clima e o
    # texto do drop-cap "E" vêm ANTES do título "Regras Mais Soltas" no fluxo de 2 colunas)
    cur_mod = {"nome": "Regras Mais Soltas (Estilos de Jogo)", "corpo": [], "pg": 281,
               "sub": "regras_soltas", "secao": "Regras Mais Soltas"}
    cur_ent = None
    dropcap = ""

    def fecha_mod():
        nonlocal cur_mod
        if cur_mod and cur_mod["corpo"]:
            nome = cur_mod["nome"]
            modulos.append({
                "id": f"regropc:herois:{slug(cur_mod['sub'])}:{slug(nome)}", "tipo": "regra_opcional",
                "subtipo": cur_mod["sub"], "regra": cur_mod["secao"], "nome": nome,
                "fonte": FONTE, "versao": "1.1", "pagina": cur_mod["pg"] + 1,
                "efeito": dehyph(juntar(cur_mod["corpo"])).strip(),
            })
        cur_mod = None

    def fecha_ent():
        nonlocal cur_ent
        if cur_ent:
            nome = dehyph(cur_ent["nome"]).rstrip(". ")
            desc = dehyph(juntar(cur_ent["desc"])).strip()
            if nome and desc:
                alvo = pratos if cur_ent["tipo"] == "prato" else ingredientes
                tp = "prato_especial" if cur_ent["tipo"] == "prato" else "ingrediente_culinaria"
                alvo.append({"id": f"{tp}:herois:{slug(nome)}", "tipo": tp, "nome": nome,
                             "fonte": FONTE, "versao": "1.1", "pagina": cur_ent["pg"] + 1,
                             "descricao": desc})
        cur_ent = None

    def flush_hdr(pg):
        nonlocal modo, cur_mod, secao, subtipo
        if not hdr:
            return
        nome = dehyph(juntar(hdr)).strip(); sz = hdr_sz
        hdr.clear()
        nn = _norm(nome)
        if nn in SECOES:                       # cabeçalho de SEÇÃO grande
            fecha_ent(); fecha_mod()
            secao, subtipo = SECOES[nn]; modo = "proc"
            cur_mod = {"nome": nome, "corpo": [], "pg": pg, "sub": subtipo, "secao": secao}
            return
        if nn == ENT_ING:                      # match EXATO (não casa "Fabricando Pratos Especiais")
            fecha_ent(); fecha_mod(); modo = "ing"
            cur_mod = {"nome": f"{secao} — Ingredientes", "corpo": [], "pg": pg, "sub": subtipo, "secao": secao}
            return
        if nn == ENT_PRATO:
            fecha_ent(); fecha_mod(); modo = "prato"
            cur_mod = {"nome": f"{secao} — Pratos Especiais", "corpo": [], "pg": pg, "sub": subtipo, "secao": secao}
            return
        if sz < 19 and cur_mod is not None:    # subtítulo 16pt → DOBRA no módulo pai
            cur_mod["corpo"].append(f" {nome}:")
            return
        # 21/27pt → novo módulo procedural
        fecha_ent(); fecha_mod(); modo = "proc"
        cur_mod = {"nome": nome, "corpo": [], "pg": pg, "sub": subtipo, "secao": secao}

    for s in spans:
        t = s["text"]; z = s["size"]
        if s["t20"] and z >= 40:
            tt = t.strip()
            if len(tt) == 1 and tt.isalpha():
                dropcap = tt
            else:
                hdr.append(t); hdr_sz = max(hdr_sz, z)   # splash de seção (Culinária/Exploração)
            continue
        if s["t20"] and 15 <= z < 40:
            hdr.append(t); hdr_sz = max(hdr_sz, z)
            continue
        # corpo → fecha cabeçalho pendente
        if hdr:
            flush_hdr(s["pg"]); hdr_sz = 0.0
        if not s["ios"]:
            continue
        if dropcap:
            t = dropcap + t.lstrip(); dropcap = ""
        if modo in ("ing", "prato"):
            if s["bold"] and RE_ENT.match(dehyph(t).strip()):
                fecha_ent()
                cur_ent = {"nome": t, "desc": [], "pg": s["pg"], "tipo": "prato" if modo == "prato" else "ing"}
            elif cur_ent is not None:
                cur_ent["desc"].append(t)
            elif cur_mod is not None:
                cur_mod["corpo"].append(t)     # intro da seção (antes da 1ª entidade)
        elif cur_mod is not None:
            cur_mod["corpo"].append(t)
    flush_hdr(314); fecha_ent(); fecha_mod()

    banco = {
        "fonte": FONTE, "livro": "Heróis de Arton", "secao": "Regras Opcionais (módulos menores)",
        "total_modulos": len(modulos), "total_pratos": len(pratos), "total_ingredientes": len(ingredientes),
        "modulos": modulos, "pratos": pratos, "ingredientes": ingredientes,
    }
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(modulos)} módulos + {len(pratos)} pratos + {len(ingredientes)} ingredientes -> {OUT.name}\n")
    for m in modulos:
        print(f"  MOD [{m['subtipo'][:12]:<12}] {m['nome']:<26} pg{m['pagina']} | {len(m['efeito']):>4}c")
    print("\n  pratos:", ", ".join(p["nome"] for p in pratos))
    print("\n  ingredientes:", ", ".join(i["nome"] for i in ingredientes))


if __name__ == "__main__":
    main()
