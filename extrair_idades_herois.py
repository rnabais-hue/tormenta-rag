# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das IDADES VARIADAS — *Heróis de Arton* (Cap. 4, págs 290–293).

Regra opcional (fonte="herois-arton"). Personagens podem ter idades fora do padrão
(jovens dos 20). Conteúdo em três grupos:
  1. **7 faixas etárias** (Criança…Ancião): nome + intervalo de idade + modificadores
     de atributo + traços nomeados → `tipo="faixa_etaria"`.
  2. **O Peso da Idade**: mazelas que afligem personagens velhos, cada uma nome+efeito
     → `tipo="mazela_idade"`.
  3. Overview (intro, "Personagens de Idades Variadas", "Envelhecendo") + caixas
     (Tabela 4-2, "Idades das Raças") → introducao + regras_extra.

Layout (duas colunas). Caixas tingidas (Tabela 4-2 embutida na coluna; sidebar "Idades
das Raças") são separadas do fluxo via get_drawings() — senão a tabela rouba o texto que
a contorna. Banner de título (contém span ≥24pt) NÃO é caixa. Âncoras:
  • faixa/seção = Tormenta20 ~21pt; intervalo de idade = Tormenta20 ~16pt logo após a
    faixa (casa "\d+ a \d+ anos"/"\d+\+ anos"); "O Peso da Idade" (21pt) chaveia p/ mazelas;
  • mazela = Tormenta20 ~16pt; efeito/traço = corpo IowanOldStyle (negrito = rótulo);
  • modificadores parseados do corpo (Força/Destreza/…/Carisma ±N).

Saída: dados/idades_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "idades_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 290, 293

ATRIBS = {"força": "Força", "forca": "Força", "destreza": "Destreza",
          "constituição": "Constituição", "constituicao": "Constituição",
          "inteligência": "Inteligência", "inteligencia": "Inteligência",
          "sabedoria": "Sabedoria", "carisma": "Carisma"}
RE_IDADE = re.compile(r"^\s*\d+\s*(a|\+|ou mais).*anos", re.I)
RE_MOD = re.compile(r"(Força|Destreza|Constituição|Inteligência|Sabedoria|Carisma)\s*([+\-−–]\s*\d+)", re.I)


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


def _dentro(r, sx, sy):
    return r.x0 - 1 <= sx <= r.x1 + 1 and r.y0 - 1 <= sy <= r.y1 + 1


def coletar_spans(doc):
    out = []
    for pg in range(PG_INI - 1, PG_FIM):
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
        boxes = [r for i, r in enumerate(boxes) if maxsz[i] < 24]   # descarta banners de título
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
                    box = next((i for i, r in enumerate(boxes) if _dentro(r, sx, sy)), None)
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "box": (pg, box) if box is not None else None,
                                "size": s["size"], "font": s["font"],
                                "ss": "SourceSans" in s["font"],
                                "t20": "Tormenta20" in s["font"],
                                "ios": "IowanOldStyle" in s["font"],
                                "bold": bool(s["flags"] & (2**4)) or "Bold" in s["font"],
                                "text": s["text"]})
    out.sort(key=lambda r: r["key"])
    return out


def parse_mods(texto):
    mods = {}
    for m in RE_MOD.finditer(texto):
        atr = ATRIBS.get(m.group(1).lower(), m.group(1))
        val = int(re.sub(r"[^\d\-]", "", m.group(2).replace("−", "-").replace("–", "-")))
        mods[atr] = val
    return mods


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)

    faixas, mazelas, intro = [], [], []
    caixas = {}
    modo = "faixas"            # faixas → mazelas → epilogo
    cur = None                 # faixa atual (dict acumulador) ou mazela
    campo = None
    dropcap = ""

    def fecha_faixa():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ")
        corpo = dehyph(juntar(cur["corpo"])).strip()
        if nome:
            # traços: rótulos negrito → nome; texto seguinte → efeito. 1º rótulo que é
            # linha de modificadores vira `modificadores`, não traço.
            tracos = []
            for lbl, ef in cur["tracos"]:
                lbl = dehyph(lbl).strip().rstrip(".")
                ef = dehyph(juntar(ef)).strip()
                if RE_MOD.search(lbl):
                    continue
                if lbl:
                    tracos.append({"nome": lbl, "efeito": ef})
            faixas.append({
                "id": f"faixa-etaria:herois:{slug(nome)}", "tipo": "faixa_etaria",
                "nome": nome, "idade": dehyph(juntar(cur["idade"])).strip(),
                "fonte": FONTE, "versao": "1.1", "pagina": cur["pg"] + 1,
                "modificadores": parse_mods(corpo),
                "resumo": dehyph(juntar(cur["resumo"])).strip(),
                "tracos": tracos, "efeito": corpo,
            })
        cur = None

    def fecha_mazela():
        nonlocal cur
        if not cur:
            return
        nome = dehyph(juntar(cur["nome"])).rstrip(". ")
        if nome:
            mazelas.append({
                "id": f"mazela-idade:herois:{slug(nome)}", "tipo": "mazela_idade",
                "nome": nome, "fonte": FONTE, "versao": "1.1", "pagina": cur["pg"] + 1,
                "efeito": dehyph(juntar(cur["corpo"])).strip(),
            })
        cur = None

    def fecha():
        if modo == "mazelas":
            fecha_mazela()
        else:
            fecha_faixa()

    for s in spans:
        if s["box"] is not None:
            caixas.setdefault(s["box"], []).append(s)
            continue
        t = s["text"]; z = s["size"]; low = dehyph(t).lower()
        if s["t20"] and z >= 24:
            tt = t.strip()
            if z >= 36 and len(tt) == 1 and tt.isalpha():
                dropcap = tt
            elif "envelhecendo" in low:              # 27pt → epílogo
                fecha(); modo = "epilogo"
            continue
        if s["t20"] and 19 <= z < 24:                # 21pt: faixa OU "O Peso da Idade"
            if "peso da idade" in low:
                fecha(); modo = "mazelas"
                continue
            if modo == "faixas":
                fecha_faixa()
                cur = {"nome": [t], "idade": [], "resumo": [], "corpo": [],
                       "tracos": [], "pg": s["pg"]}
                campo = "resumo"
                continue
            # 21pt em outros modos → ignora (não deve ocorrer)
            continue
        if s["t20"] and 13 <= z < 19:                # 16pt
            if modo == "faixas" and cur is not None and RE_IDADE.match(t):
                cur["idade"].append(t)               # intervalo de idade da faixa atual
                continue
            if modo == "mazelas":
                fecha_mazela()
                cur = {"nome": [t], "corpo": [], "pg": s["pg"]}
                continue
            # 16pt fora de contexto → trata como corpo/nome conforme modo
            continue
        if s["ios"]:
            if dropcap:
                t = dropcap + t.lstrip(); dropcap = ""
            if cur is None:
                intro.append(t)
                continue
            if modo == "faixas":
                if s["bold"]:
                    if re.match(r"(?i)^tabela\s+\d", dehyph(t).strip()):
                        campo = "skip"          # título de tabela vazado (fora da caixa)
                        continue
                    cur["tracos"].append([t, []]); campo = "traco"
                    cur["corpo"].append(t)       # alimenta parse de modificadores
                elif campo == "skip":
                    continue                     # legenda órfã da tabela → descarta
                elif campo == "traco" and cur["tracos"]:
                    cur["tracos"][-1][1].append(t)
                    cur["corpo"].append(t)
                else:
                    cur["resumo"].append(t); cur["corpo"].append(t)
            else:  # mazelas / epilogo
                cur["corpo"].append(t)
    fecha()

    # caixas (sidebars / tabela)
    sidebars = []
    for (pg, _), sps in caixas.items():
        titulo, corpo = "", []
        for s in sps:
            if not titulo and (s["ss"] or s["t20"] or s["bold"]) and s["size"] >= 12:
                titulo = s["text"]
            else:
                corpo.append(s["text"])
        if corpo:
            sidebars.append({"titulo": dehyph(titulo).strip() or "(tabela)",
                             "texto": dehyph(juntar(corpo)).strip(), "pagina": pg + 1})

    banco = {
        "fonte": FONTE, "livro": "Heróis de Arton", "secao": "Idades Variadas",
        "pagina": PG_INI, "total_faixas": len(faixas), "total_mazelas": len(mazelas),
        "introducao": dehyph(juntar(intro)).strip(),
        "faixas": faixas, "mazelas": mazelas, "regras_extra": sidebars,
    }
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(faixas)} faixas + {len(mazelas)} mazelas -> {OUT.name}")
    print(f"  intro {len(banco['introducao'])}c · {len(sidebars)} caixa(s): "
          f"{[s['titulo'] for s in sidebars]}\n")
    for f in faixas:
        mods = ", ".join(f"{k} {v:+d}" for k, v in f["modificadores"].items()) or "—"
        print(f"  {f['nome']:<12} {f['idade']:<14} | mods: {mods:<40} | {len(f['tracos'])} traços")
    print("  mazelas:", ", ".join(m["nome"] for m in mazelas))


if __name__ == "__main__":
    main()
