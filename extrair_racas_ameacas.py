# -*- coding: utf-8 -*-
r"""Extração das RAÇAS JOGÁVEIS de *Ameaças de Arton* — as "raças novas" que ficaram
FORA da Fase 1 do bestiário (só criaturas). `fonte="ameacas-arton"`, `capitulo="racas"`.

O Apêndice A (pg 418) lista, na **Tabela A-1**, as ameaças que podem ser jogadas como
personagem (nome + modificadores de atributo + página). Cada raça tem, na sua página,
uma **caixa "{Nome}: Habilidades de Raça"** (retângulo preenchido) com: linha de
modificadores de atributo (por extenso) + habilidades raciais no padrão rótulo-bold
("Nome. descrição") — o mesmo formato das raças do núcleo.

Motor: acha os headers "Habilidades de Raça" (Tormenta20 >=12.5pt), delimita a caixa
via `get_drawings()`, ordena o texto em 2 colunas, e parseia modificadores + habilidades.
O nome vem antes do ":" no header, ou na linha Tormenta20 imediatamente acima.

Saída: dados/racas_ameacas.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "Ameacas-de-Arton-v1.0-17-11-2023.pdf"
OUT = Path(__file__).parent / "dados" / "racas_ameacas.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "ameacas-arton"

ATRIBS = r"Força|Destreza|Constituição|Inteligência|Sabedoria|Carisma|For|Des|Con|Int|Sab|Car"


def dehyph(s):
    s = re.sub(r"(\w)[\-­]\s+(\w)", r"\1\2", s)
    return re.sub(r"\s+", " ", s).strip()


def _limpa_nome(s):
    """Nome próprio da raça: as 1–3 primeiras palavras capitalizadas; remove resíduo de
    header ('Habilidades', 'de Raça') e dedup de palavra repetida ('Trog Anão Trog'→'Trog Anão')."""
    s = re.sub(r"[\s:]*Habilidades\b.*$", "", dehyph(s)).strip(" :.,")
    ws = s.split()
    out = []
    for w in ws:
        if not re.match(r"^[A-ZÀ-Ý0-9]", w):     # para na 1ª palavra minúscula (início do corpo)
            break
        if out and w.lower() == out[-1].lower():
            continue
        out.append(w)
        if len(out) >= 3:
            break
    nome = " ".join(out)
    # dedup de bigrama repetido ("Trog Anão Trog" -> "Trog Anão")
    p = nome.split()
    if len(p) >= 3 and p[0].lower() == p[2].lower():
        nome = " ".join(p[:2])
    return nome.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def parse_tabela_a1(doc):
    """Tabela A-1 (pg 418, col direita): {nome_slug: (modificadores, pagina)}."""
    page = doc[417]
    spans = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                st = s["text"].strip()
                if st and s["bbox"][0] > 300 and s["bbox"][1] > 195:
                    spans.append((s["bbox"][1], s["bbox"][0], st))
    pgs = [(y, t) for y, x, t in spans if x > 480 and re.match(r"^\d+$", t)]
    nomes = [(y, t) for y, x, t in spans if x < 345]
    mods = [(y, t) for y, x, t in spans if 350 < x < 478]
    out = {}
    for y, pg in pgs:
        nm = min(((abs(yy - y), t) for yy, t in nomes if abs(yy - y) < 9), default=(9, ""))[1]
        md = " ".join(t for yy, t in sorted(mods) if abs(yy - y) < 12)
        if nm:
            out[slug(nm)] = (dehyph(md), int(pg))
    return out


def achar_caixas(doc):
    """[(idx, nome, header_rect)] das caixas 'Habilidades de Raça' (Tormenta20 >=12.5)."""
    achados = []
    for idx in range(11, 360):
        page = doc[idx]
        linhas = []
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                sp = [s for s in l["spans"] if s["text"].strip()]
                if sp:
                    linhas.append(l)
        for i, l in enumerate(linhas):
            buf = dehyph("".join(s["text"] for s in l["spans"]))
            # o header do box pode vir em 2 linhas ("…: Habilidades" + "de Raça"): junta a próxima
            buf2 = buf
            if i + 1 < len(linhas):
                buf2 = dehyph(buf + " " + "".join(s["text"] for s in linhas[i+1]["spans"]))
            eh_hab = bool(re.search(r"Habilidades de Ra[çc]a", buf2))
            eh_var = bool(re.search(r"Ra[çc]a Variante\s*:", buf2))
            if not (eh_hab or eh_var):
                continue
            fonts = [s["font"] for s in l["spans"]]
            # header de box = SourceSansPro-Bold / Mansalva / SpecialElite (NÃO IowanOldStyle do corpo)
            if not any(f.startswith(("SourceSansPro", "Mansalva", "SpecialElite")) for f in fonts):
                continue
            if eh_var:
                # "Raça Variante: X" — nome após o ':' (nesta linha; senão na seguinte)
                m = re.search(r"Ra[çc]a Variante\s*:\s*(\S.*)$", buf)
                raw = m.group(1) if m else (
                    dehyph("".join(s["text"] for s in linhas[i+1]["spans"])) if i + 1 < len(linhas) else "")
                nome = _limpa_nome(raw)
            else:
                nome = re.sub(r"[\s:]*Habilidades\b.*$", "", buf).strip(" :")
                if not nome and i > 0:
                    prev = dehyph("".join(s["text"] for s in linhas[i-1]["spans"])).strip(" :")
                    pf = [s["font"] for s in linhas[i-1]["spans"]]
                    if prev and any(f.startswith(("SourceSansPro", "Mansalva")) for f in pf):
                        nome = re.sub(r"[\s:]*Habilidades\b.*$", "", prev).strip(" :")
            nome = _limpa_nome(nome)
            achados.append((idx, nome, l["bbox"]))
    return achados


def texto_da_caixa(doc, idx, header_bbox):
    """Linhas dentro da caixa (retângulo) que contém o header, em ordem 2-colunas."""
    page = doc[idx]
    hx, hy = header_bbox[0], header_bbox[1]
    caixas = [d["rect"] for d in page.get_drawings()
              if d.get("fill") and d["rect"].width > 80 and d["rect"].height > 40]
    cont = [r for r in caixas if r.y0 - 3 <= hy <= r.y1 + 3 and r.x0 - 3 <= hx <= r.x1 + 3]
    if cont:
        r = min(cont, key=lambda z: z.width * z.height)   # a caixa mais justa
    else:
        # FALLBACK sem retângulo (ex.: Kobolds): sintetiza a caixa na coluna do header,
        # do topo do header até ~260px abaixo (as caixas de raça têm ~5-7 habilidades)
        r = pymupdf.Rect(max(0, hx - 8), hy - 4, hx + 230, hy + 300)
    xmid = (r.x0 + r.x1) / 2
    itens = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            sp = [s for s in l["spans"] if s["text"].strip()]
            if not sp:
                continue
            lx, ly = l["bbox"][0], l["bbox"][1]
            if not (r.y0 - 3 <= ly <= r.y1 + 3 and r.x0 - 3 <= lx <= r.x1 + 3):
                continue
            col = 0 if lx < xmid else 1
            fn0 = sp[0]["font"]
            texto = dehyph("".join(s["text"] for s in sp))
            # rótulo em negrito = IowanOldStyle-Black OU *-Bold (o corpo da caixa é IowanOldStyle)
            is_bold = ("Black" in fn0) or ("Bold" in fn0)
            # header = a própria linha "…: Habilidades de Raça" (SourceSansPro-Bold/Mansalva) ou Tormenta20
            is_hdr = bool(re.search(r"Habilidades de Ra[çc]a", texto)) or \
                any(s["font"].startswith(("Tormenta20", "Mansalva")) for s in sp)
            itens.append((col, ly, texto, is_bold, is_hdr))
    itens.sort(key=lambda z: (z[0], z[1]))
    return itens


def parse_caixa(itens):
    """Modificadores (por extenso) + habilidades [{nome, efeito}]. As linhas iniciais
    (não-rótulo) são os modificadores; cada habilidade = rótulo NEGRITO "Nome." + descrição."""
    corpo = [(t, bold) for col, y, t, bold, hdr in itens if not hdr and t.strip()]
    habs, mods = [], []
    cur_nome, cur_desc = None, []
    viu_hab = False
    for t, bold in corpo:
        m = re.match(r"^([A-ZÀ-Ý][^.!?…]{1,44}[.!?…])\s*(.*)$", t)
        # rótulo de habilidade: negrito + casa "Nome." + NÃO é a linha de modificador
        eh_mod = bool(re.match(rf"^(?:{ATRIBS})\b", t)) and bool(re.search(r"[+\-–]\s*\d|em (?:um|dois|outro)", t))
        eh_label = bold and m and not eh_mod
        if eh_label:
            viu_hab = True
            if cur_nome:
                habs.append({"nome": cur_nome.rstrip(" .:"), "efeito": dehyph(" ".join(cur_desc))})
            cur_nome, cur_desc = m.group(1).rstrip(" .:"), ([m.group(2)] if m.group(2) else [])
        elif not viu_hab:
            mods.append(t)                     # modificadores (antes da 1ª habilidade)
        elif cur_nome:
            cur_desc.append(t)
    if cur_nome:
        habs.append({"nome": cur_nome.rstrip(" .:"), "efeito": dehyph(" ".join(cur_desc))})
    return dehyph(" ".join(mods)), habs


def main():
    print(f"Abrindo {PDF.name}...")
    doc = pymupdf.open(PDF)
    a1 = parse_tabela_a1(doc)
    print(f"Tabela A-1: {len(a1)} raças indexadas")
    caixas = achar_caixas(doc)

    racas = []
    vistos = set()
    for idx, nome, hbbox in caixas:
        if not nome or nome.lower() in ("habilidades de raça",):
            continue
        chave = slug(nome)
        if chave in vistos:
            continue
        vistos.add(chave)
        itens = texto_da_caixa(doc, idx, hbbox)
        modificadores, habs = parse_caixa(itens)
        if len(habs) < 1:                       # sem habilidades = extração incompleta/ruído
            continue
        tab = a1.get(chave) or a1.get(slug(nome.replace("s", "")))  # kobolds↔kobold
        racas.append({
            "id": f"raca:ameacas:{chave}",
            "tipo": "raca", "fonte": FONTE, "capitulo": "racas",
            "nome": nome, "pagina": idx,
            "modificadores": modificadores,
            "modificadores_tabela": tab[0] if tab else "",
            "habilidades": habs,
        })
        print(f"  {nome:16.16} idx{idx:3} mods={len(modificadores):3}c habs={len(habs):2} "
              f"{'[sem A-1]' if not tab else ''}")

    dados = {"fonte": FONTE, "livro": "Ameaças de Arton", "capitulo": "Apêndice A / caixas de raça",
             "total": len(racas), "racas": racas}
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] {len(racas)} raças jogáveis -> {OUT}")


if __name__ == "__main__":
    main()
