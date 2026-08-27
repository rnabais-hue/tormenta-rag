# -*- coding: utf-8 -*-
r"""Extração do RESTO do Cap. 3 de *Deuses de Arton* (fecha o capítulo):
Deuses Menores + Antigos Deuses + Artefatos Divinos.

`fonte="deuses-arton"`, `capitulo="deuses-menores"`, págs 230–251. Blocos:
  - **Antigos Deuses** (240–246): 5 deuses mortos (nome 27pt + subtítulo 21pt + prosa).
  - **Artefatos Divinos** (248–251): 6 artefatos (nome 21pt + prosa).
  - **Deuses Menores nomeados** (233–235): 3 (Gwendolynn/Mauziell/Tibar; nome 27pt +
    subtítulo 21pt + prosa, inclui o poder concedido).
  - **Dádivas de Deuses Menores** (236–238): 16 dádivas (nome 16pt + efeito) — as
    "habilidades" de um deus menor jogável.
  - **Visão geral dos Deuses Menores** (230–232, 235, 239): prosa mecânica agregada
    (Naturezas, Status Divino, Jogando como Deus Menor, Desafios Divinos) em 1 chunk.

Motor: coletor header-driven genérico (nome = linhas-cabeçalho consecutivas de um dado
tamanho Tormenta20; corpo = IowanOldStyle até o próximo cabeçalho). 2 colunas por x.

Saída: dados/deuses_menores.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

import extrair_ameacas_deuses as best  # slug, dehyph

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = Path(__file__).parent / "dados" / "deuses_menores.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"
COL_X = 280


def _linhas(doc, p0, p1):
    """Linhas em ordem de leitura (2 colunas), cada uma com spans."""
    out = []
    for pno in range(p0, p1 + 1):
        page = doc[pno - 1]
        buf = []
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                sp = [s for s in l["spans"] if s["text"].strip()]
                if not sp:
                    continue
                lx = min(s["bbox"][0] for s in sp)
                ly = min(s["bbox"][1] for s in sp)
                buf.append((0 if lx < COL_X else 1, ly, sp, pno))
        buf.sort(key=lambda z: (z[0], z[1]))
        out.extend(buf)
    return out


def _hdr(sp, lo, hi):
    """Texto do cabeçalho Tormenta20 em [lo,hi] na linha (ou '')."""
    t = "".join(s["text"] for s in sp if s["font"].startswith("Tormenta20") and lo <= s["size"] <= hi)
    return re.sub(r"\s+", " ", t).strip()


def _corpo(sp):
    """Texto de corpo IowanOldStyle (drop-cap grande vira prefixo)."""
    partes = []
    for s in sp:
        fn, sz, t = s["font"], s["size"], s["text"]
        if fn.startswith("Tormenta20") and sz >= 30 and len(t.strip()) <= 2:
            partes.append(t.strip())
        elif "IowanOldStyle" in fn and "BoldItalic" not in fn:
            partes.append(t)
    return " ".join(partes)


def _maxsz(sp):
    return max((s["size"] for s in sp if s["font"].startswith("Tormenta20")), default=0)


def coletar(doc, p0, p1, lo, hi, nomes_validos=None):
    """Coletor header-driven. Retorna [(nome, corpo)]: nome = cabeçalhos Tormenta20 em
    [lo,hi] consecutivos (junta nomes de 2 linhas); corpo = IowanOldStyle até o próximo
    cabeçalho. Cabeçalhos MAIORES que hi encerram/são ignorados (fronteira de seção)."""
    ents = []
    cur_nome = None
    cur_corpo = []
    aguardando_nome = False   # acabou de abrir nome, pode haver 2ª linha de nome
    for col, ly, sp, pno in _linhas(doc, p0, p1):
        msz = _maxsz(sp)
        h = _hdr(sp, lo, hi)
        corpo = _corpo(sp)
        eh_header = bool(h) and not corpo and lo <= msz <= hi
        if msz > hi + 0.5:
            # cabeçalho de seção maior → fecha entidade corrente
            if cur_nome:
                ents.append((cur_nome, best.dehyph(" ".join(cur_corpo))))
                cur_nome, cur_corpo = None, []
            aguardando_nome = False
            continue
        if eh_header:
            if aguardando_nome and cur_nome and not cur_corpo:
                cur_nome = (cur_nome + " " + h).strip()      # nome de 2 linhas
            else:
                if cur_nome:
                    ents.append((cur_nome, best.dehyph(" ".join(cur_corpo))))
                cur_nome, cur_corpo = h, []
                aguardando_nome = True
        else:
            if corpo:
                aguardando_nome = False
                if cur_nome:
                    cur_corpo.append(corpo)
    if cur_nome:
        ents.append((cur_nome, best.dehyph(" ".join(cur_corpo))))
    if nomes_validos is not None:
        ents = [(n, c) for n, c in ents if any(n.startswith(v) for v in nomes_validos)]
    return ents


def coletar_nomeados(doc, p0, p1, nomes, lo=20, hi=22):
    """Extrai deuses menores NOMEADOS (nome no tamanho [lo,hi], 21pt) cujo cabeçalho começa
    por um nome conhecido. Só abre entidade quando o header casa `nomes` (evita as seções
    e subtítulos do mesmo tamanho); corpo = IowanOldStyle até o próximo header nesse tamanho."""
    ents = []
    cur = None
    corpo = []
    for col, ly, sp, pno in _linhas(doc, p0, p1):
        msz = _maxsz(sp)
        h = _hdr(sp, lo, hi)
        c = _corpo(sp)
        if h and not c and lo <= msz <= hi:
            base = h.split(",")[0].strip()
            if any(base.startswith(nv) for nv in nomes):
                if cur:
                    ents.append({"nome": cur, "corpo": best.dehyph(" ".join(corpo))})
                cur, corpo = base, []
            # subtítulo/outra seção do mesmo tamanho: não fecha (continua o corrente)
        elif c and cur:
            corpo.append(c)
    if cur:
        ents.append({"nome": cur, "corpo": best.dehyph(" ".join(corpo))})
    return ents


def coletar_prosa(doc, p0, p1):
    """Junta TODA a prosa IowanOldStyle do range (para overview mecânico)."""
    partes = []
    for col, ly, sp, pno in _linhas(doc, p0, p1):
        c = _corpo(sp)
        if c:
            partes.append(c)
    s = best.dehyph(" ".join(partes))
    s = re.sub(r"^([A-ZÀ-Ý]) ([a-zà-ÿ])", r"\1\2", s, count=1)
    return s


def main():
    print(f"Abrindo {PDF.name}...")
    doc = pymupdf.open(PDF)

    # --- Antigos Deuses (240-246): nome 27pt + subtítulo 21pt ---
    antigos = []
    for nome, corpo in coletar(doc, 240, 246, 24, 30):
        # o subtítulo 21pt vem no corpo? não — 21pt não é IowanOldStyle. Recupera à parte:
        antigos.append({"nome": nome, "corpo": corpo})
    print(f"Antigos Deuses: {len(antigos)} -> {[a['nome'] for a in antigos]}")

    # --- Artefatos Divinos (248-251): nome 21pt ---
    artefatos = [{"nome": n, "corpo": c} for n, c in coletar(doc, 248, 251, 20, 22)]
    print(f"Artefatos: {len(artefatos)} -> {[a['nome'] for a in artefatos]}")

    # --- Deuses Menores nomeados (233-235): 27pt, ancorados por nome conhecido ---
    menores_nomeados = coletar_nomeados(doc, 233, 235, ["Gwendolynn", "Mauziell", "Tibar"])
    print(f"Menores nomeados: {len(menores_nomeados)} -> {[m['nome'] for m in menores_nomeados]}")

    # --- Dádivas (236-238): nome 16pt ---
    dadivas = [{"nome": n, "efeito": c} for n, c in coletar(doc, 236, 238, 15, 17)]
    print(f"Dádivas: {len(dadivas)} -> {[d['nome'] for d in dadivas]}")

    # --- Overview mecânico dos Deuses Menores (230-232 + 235 + 239) ---
    overview = coletar_prosa(doc, 230, 232)
    desafios = coletar_prosa(doc, 239, 239)

    dados = {
        "fonte": FONTE, "livro": "Deuses de Arton", "capitulo": "Capítulo 3: Deuses Menores/Antigos/Artefatos",
        "antigos_deuses": antigos,
        "artefatos_divinos": artefatos,
        "deuses_menores_nomeados": menores_nomeados,
        "dadivas": dadivas,
        "overview_menores": overview,
        "desafios_divinos": desafios,
    }
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] antigos={len(antigos)} artefatos={len(artefatos)} menores={len(menores_nomeados)} "
          f"dadivas={len(dadivas)} overview={len(overview)}c -> {OUT}")


if __name__ == "__main__":
    main()
