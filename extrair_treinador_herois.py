# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA da nova classe TREINADOR de *Heróis de Arton* (Cap. 1, págs 18–23).

Classe completa (não é variante): schema compatível com dados/classes.json do núcleo
(nome, resumo, caracteristicas, habilidades[{nome,efeito}], atributo_principal), +
`melhor_amigo` (o companheiro "O Melhor Amigo" + seus Truques — o pet da classe).

Seções (headers Tormenta20 ≥21pt, na ordem de leitura):
  Lore -> Características de Classe -> Habilidades de Classe -> O Melhor Amigo -> Truques.

Saída: dados/treinador_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "treinador_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PAG_INI, PAG_FIM = 18, 23
BOLD = 2**4


def dehyph(s):
    s = re.sub("[­�]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def coletar(doc):
    out = []
    for pg in range(PAG_INI, PAG_FIM + 1):
        page = doc[pg - 1]; W, H = page.rect.width, page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            bx0, by0 = b["bbox"][0], b["bbox"][1]
            bcol = 0 if bx0 < W * 0.40 else 1
            for li, l in enumerate(b["lines"]):
                for si, s in enumerate(l["spans"]):
                    tx = s["text"]
                    if not tx.strip() or s["size"] <= 8.2:
                        continue
                    if "SourceSans" in s["font"] or "Spirals" in s["font"] or "LetterGothic" in s["font"]:
                        continue
                    y = s["bbox"][1]
                    if (y < H * 0.06 or y > H * 0.94) and s["size"] < 20:
                        continue
                    dc = "Tormenta20" in s["font"] and s["size"] >= 36 and len(tx.strip()) <= 2
                    out.append({"key": (pg, bcol, round(by0, 1), li, si), "pg": pg,
                                "size": s["size"], "font": s["font"], "text": tx,
                                "bold": bool(s["flags"] & BOLD) or "Bold" in s["font"],
                                "dropcap": dc})
    out.sort(key=lambda r: r["key"])
    return [s for s in out if not s["dropcap"]]


def eh_header(s, minsz=20):
    return "Tormenta20" in s["font"] and s["size"] >= minsz


def header_txt(spans, i):
    """Junta spans de header consecutivos a partir de i. Retorna (texto, prox_i)."""
    partes = [spans[i]["text"]]; j = i + 1
    while j < len(spans) and eh_header(spans[j]) and spans[j]["pg"] == spans[i]["pg"]:
        partes.append(spans[j]["text"]); j += 1
    return dehyph(" ".join(partes)), j


def parse_habilidades(spans):
    """nome(negrito) -> efeito(demais) até o próximo negrito. Ignora nome do próprio treinador."""
    habs, cur = [], None
    for s in spans:
        if eh_header(s):
            continue
        if s["bold"]:
            if cur is None or cur["_ef"].strip():
                cur = {"nome": "", "_ef": ""}; habs.append(cur)
            cur["nome"] += s["text"]
        else:
            if cur is None:
                cur = {"nome": "", "_ef": ""}; habs.append(cur)
            cur["_ef"] += s["text"]
    out = []
    for h in habs:
        nm = dehyph(h["nome"]).rstrip(". ")
        ef = dehyph(h["_ef"])
        if nm and ef and len(nm) <= 40:
            out.append({"nome": nm, "efeito": ef})
    return out


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar(doc)

    # localizar limites de seção pelos headers
    limites = {}  # nome_secao -> (ini, fim)
    heads = []
    i = 0
    while i < len(spans):
        if eh_header(spans[i]):
            txt, j = header_txt(spans, i)
            heads.append((i, j, txt))
            i = j
        else:
            i += 1

    def idx_de(frag):
        for (i0, j0, t) in heads:
            if frag.lower() in t.lower():
                return i0, j0
        return None

    h_carac = idx_de("Características")
    h_hab = idx_de("Habilidades de Classe")
    h_pet = idx_de("Melhor Amigo")
    n = len(spans)

    # resumo = lore antes de "Características" (só roman, não-negrito)
    fim_lore = h_carac[0] if h_carac else n
    # o nome "treinador" é o 1º header (66pt); pula-o
    nome = "Treinador"
    lore_spans = [s for s in spans[:fim_lore] if not eh_header(s)]
    resumo = dehyph(" ".join(s["text"] for s in lore_spans))[:900]

    # características (PV/PM/Perícias/Proficiências)
    car_ini = h_carac[1] if h_carac else n
    car_fim = h_hab[0] if h_hab else n
    car_txt = dehyph(" ".join(s["text"] for s in spans[car_ini:car_fim] if not eh_header(s)))
    caracteristicas = {}
    for lab, key in [("Pontos de Vida", "pv"), ("Pontos de Mana", "pm"),
                     ("Perícias", "pericias"), ("Proficiências", "proficiencias")]:
        m = re.search(re.escape(lab) + r"[.:]?\s*(.+?)(?=Pontos de|Perícias|Proficiências|$)", car_txt)
        if m:
            caracteristicas[key] = m.group(1).strip().rstrip(".")

    # habilidades de classe (entre "Habilidades de Classe" e "O Melhor Amigo")
    hab_ini = h_hab[1] if h_hab else n
    hab_fim = h_pet[0] if h_pet else n
    habilidades = parse_habilidades(spans[hab_ini:hab_fim])

    # O Melhor Amigo (pet) + Truques: captura como texto
    pet_ini = h_pet[0] if h_pet else n
    melhor_amigo = dehyph(" ".join(s["text"] for s in spans[pet_ini:n]))[:3500]

    rec = {
        "id": "classe:herois:treinador", "tipo": "classe", "nome": nome,
        "fonte": FONTE, "versao": "1.1", "pagina": 18,
        "resumo": resumo, "caracteristicas": caracteristicas,
        "atributo_principal": {"texto": "Carisma", "atributos": ["Carisma"]},
        "habilidades": habilidades,
        "melhor_amigo": melhor_amigo,
    }
    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "classes": [rec]}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Classe Treinador extraída -> {OUT.name}")
    print(f"  atributo: {rec['atributo_principal']['texto']}")
    for k, v in caracteristicas.items():
        print(f"  {k}: {v[:70]}")
    print(f"  {len(habilidades)} habilidades:")
    for h in habilidades:
        print(f"     • {h['nome']}: {h['efeito'][:60]}")
    print(f"  melhor_amigo: {len(melhor_amigo)} chars — {melhor_amigo[:70]}")


if __name__ == "__main__":
    main()
