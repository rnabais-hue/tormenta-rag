# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das NOVAS RAÇAS de *Heróis de Arton* (Cap. 1, págs 10–17).

Livro de expansão (fonte="herois-arton"). Adapta o extrator do núcleo
(extrair_racas.py): mesmo schema e mesma estratégia tipográfica (nome em
Tormenta20 ≥20pt; lore roman antes do 1º negrito = resumo; 1ª sequência negrito
com "Atributo ±N" = modificadores; depois nome(negrito)->efeito).

Diferenças deste livro:
  - O corpo é IowanOldStyle (não SourceSansPro) → negrito detectado por flag OU
    "Bold" no nome da fonte; spans SourceSansPro (pull-quotes/caixas) são descartados.
  - A raça **Duende** é PROCEDURAL ("monte sua raça": Passo 1 Natureza, Passo 2
    Tamanho, Passo 3 Dons, Passo 4 Presentes) → marcada com `procedural=True`;
    guarda o resumo e os passos como habilidades, sem tentar modificadores fixos.

Saída: dados/racas_herois.json. NÃO toca no índice FAISS.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "racas_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PAG_INI, PAG_FIM = 9, 16            # 0-based, inclusivo (Duende p10 .. Sátiro p17)

BOLD, ITAL = 2**4, 2**1
ATR = r"For[çc]a|Destreza|Constitui[çc][ãa]o|Intelig[êe]ncia|Sabedoria|Carisma"
# Marcadores de seção/título que NÃO são nome de raça (ou vazam no corpo).
STOP = re.compile(
    r"^(Novas Raças|Habilidades de Raça|Passo\s*\d|Campeões de Arton|Capítulo|"
    r"Sonhos Malucos|Tabela|Regras|Dons|Presentes|Natureza|Tamanho)\b", re.I)
NOMES_ESPERADOS = {"Duende", "Eiradaan", "Galokk", "Meio-Elfo", "Sátiro"}
PROCEDURAIS = {"Duende"}


def dehyph(s):
    s = re.sub("[­�]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def is_bold(s):
    return bool(s["flags"] & BOLD) or "Bold" in s["font"]


def coletar_spans(doc):
    out = []
    for pg in range(PAG_INI, PAG_FIM + 1):
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
                    if s["size"] <= 8.2:
                        continue
                    if "SourceSans" in s["font"] or "Spirals" in s["font"]:
                        continue          # pull-quotes e caixas laterais
                    y = s["bbox"][1]
                    if y < H * 0.06 or y > H * 0.94:
                        continue
                    out.append({
                        "key": (pg, bcol, round(by0, 1), li, si),
                        "pg": pg, "size": s["size"], "font": s["font"],
                        "bold": is_bold(s), "ital": bool(s["flags"] & ITAL),
                        "text": s["text"],
                    })
    out.sort(key=lambda r: r["key"])
    return out


def eh_nome(s):
    t = dehyph(s["text"])
    return ("Tormenta20" in s["font"] and s["size"] >= 20 and not STOP.match(t)
            and len(t) >= 3)


def eh_estrutural(s):
    return (("Tormenta20" in s["font"] and s["size"] >= 16)
            or STOP.match(dehyph(s["text"])))


def limpar_resumo(txt):
    txt = re.sub(r'^[a-zà-ÿ]{0,4}["”\')]+[,.]?\s+', "", txt)
    return txt.strip()[:800]


def _mods(txt):
    d = {}
    for atr, sig, val in re.findall(rf"({ATR})\s*([+\-–])\s*(\d)", dehyph(txt)):
        d[dehyph(atr)] = int(("-" if sig in "-–" else "+") + val)
    return d


def parse_raca(nome, pagina, spans):
    spans = [s for s in spans if not eh_estrutural(s)]
    b0 = next((i for i, s in enumerate(spans) if s["bold"]), None)
    resumo = ""
    if b0 is not None:
        roman = [s["text"] for s in spans[:b0] if not s["ital"] and not s["bold"]]
        resumo = limpar_resumo(dehyph(" ".join(roman)))
    mech = spans[b0:] if b0 is not None else []

    procedural = nome in PROCEDURAIS
    modificadores = {}
    j = 0
    if procedural:
        # Raça modular ("monte sua raça"): fragmentar em habilidades nome->efeito
        # produz lixo. Guarda o corpo inteiro como texto para o RAG recuperar.
        corpo = dehyph(" ".join(s["text"] for s in spans))
        slug = re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")
        return {
            "id": f"raca:herois:{slug}", "tipo": "raca", "nome": nome,
            "fonte": FONTE, "versao": "1.1", "pagina": pagina,
            "modificadores": {}, "resumo": resumo, "habilidades": [],
            "procedural": True, "texto_completo": corpo[:4000],
        }
    if not procedural:
        # modificadores = 1ª sequência negrito até fechar frase
        mtxt = ""
        while j < len(mech) and mech[j]["bold"]:
            mtxt += mech[j]["text"]; j += 1
            if "." in mech[j - 1]["text"]:
                break
        mtxt_c = dehyph(mtxt)
        flex_m = re.search(
            r"[+\-–]?\d+\s+em\s+(?:um|dois|tr[êe]s|quatro)\s+atributos?"
            r"(?:\s+diferentes)?(?:,?\s*exceto\s+[A-Za-zÀ-ÿ]+)?", mtxt_c, re.I)
        has_fixed = re.search(rf"({ATR})\s*[+\-–]\s*\d", mtxt_c)
        if flex_m or has_fixed:
            if flex_m:
                modificadores["_flexivel"] = re.sub(r"\s+", " ", flex_m.group(0)).strip()
            modificadores.update(_mods(mtxt_c))
        else:
            j = 0

    # habilidades: nome(negrito) -> efeito(demais) até o próximo negrito
    habs, cur = [], None
    for s in mech[j:]:
        if s["bold"]:
            if cur is None or cur["_ef"].strip():
                cur = {"nome": "", "_ef": ""}; habs.append(cur)
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
        "id": f"raca:herois:{slug}", "tipo": "raca", "nome": nome,
        "fonte": FONTE, "versao": "1.1", "pagina": pagina,
        "modificadores": modificadores, "resumo": resumo,
        "habilidades": habilidades,
    }
    if procedural:
        rec["procedural"] = True
    return rec


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)
    anchors = [(i, s) for i, s in enumerate(spans) if eh_nome(s)]
    racas = []
    for a, (idx, s) in enumerate(anchors):
        fim = anchors[a + 1][0] if a + 1 < len(anchors) else len(spans)
        conteudo = spans[idx + 1:fim]
        nome = dehyph(s["text"])
        pagina = s["pg"] + 1
        racas.append(parse_raca(nome, pagina, conteudo))

    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "total": len(racas),
             "racas": racas}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(racas)} raças extraídas -> {OUT.name}\n")
    for r in racas:
        mods_parts = []
        if r["modificadores"].get("_flexivel"):
            mods_parts.append(r["modificadores"]["_flexivel"])
        mods_parts += [f"{k} {v:+d}" for k, v in r["modificadores"].items() if k != "_flexivel"]
        mods = ", ".join(mods_parts) or ("(procedural)" if r.get("procedural") else "(sem mods)")
        print(f"- {r['nome']:<12} pág {r['pagina']:>3} | {len(r['habilidades'])} habs | {mods}")


if __name__ == "__main__":
    main()
