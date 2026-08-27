# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Cap. 3 "Deuses e Avatares" de *Deuses de Arton* — os 20
DEUSES MAIORES (lore + Avatar).

`fonte="deuses-arton"`, `capitulo="deuses-avatares"`, págs 150–229. Cada deus ocupa
4 págs: splash (nome ~100pt) + lore de abertura, depois seções **Motivações**,
**Relações**, **Igreja e Clero** (Tormenta20 27pt), e por fim **Avatar** — um STAT
BLOCK versalete idêntico ao do bestiário (Cap. 4).

REUSO: o parser de stat block versalete vem de `extrair_ameacas_deuses` (mesmo motor
base-linha). A lore é prosa IowanOldStyle em 2 colunas, coletada por seção.

Caso especial: **Nimb** (Deus do Caos) grafa os cabeçalhos com espaçamento decorativo
→ os 27pt saem fragmentados; a lore dele fica num único bloco de abertura (sem split
de seção) e o Avatar é achado pela âncora 16pt "Avatar de Nimb".

Saída: dados/deuses_avatares.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

import extrair_ameacas_deuses as best  # reusa reconstruir_linhas, segmentar_criaturas, slug, dehyph

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Deuses-de-Arton-Ebook.pdf"
OUT = Path(__file__).parent / "dados" / "deuses_avatares.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "deuses-arton"
COL_X = 280

# seção 27pt -> chave (accent-free match)
SEC_MAP = {
    "motivacoes": "motivacoes",
    "relacoes": "relacoes",
    "igreja e clero": "igreja_clero",
    "avatar": "avatar",
}


def _acc(s):
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return s


def deuses_toc(doc):
    """(titulo, pagina) dos 20 deuses maiores (págs 150–229)."""
    gods = [(t.strip(), p) for lvl, t, p in doc.get_toc() if lvl == 2 and 150 <= p <= 229]
    gods.sort(key=lambda x: x[1])
    return gods


def coletar_lore(doc, p0, p1):
    """Coleta a prosa (IowanOldStyle) do deus, dividida pelas seções 27pt. Retorna
    (secoes_dict, avatar_pno) onde avatar_pno é a 1ª página com o cabeçalho 'Avatar'
    (ou None). A lore para no 'Avatar'."""
    secoes = {"abertura": [], "motivacoes": [], "relacoes": [], "igreja_clero": []}
    cur = "abertura"
    avatar_pno = None
    for pno in range(p0, p1 + 1):
        page = doc[pno - 1]
        linhas = []
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                sp = [s for s in l["spans"] if s["text"].strip()]
                if not sp:
                    continue
                lx = min(s["bbox"][0] for s in sp)
                ly = min(s["bbox"][1] for s in sp)
                col = 0 if lx < COL_X else 1
                linhas.append((col, ly, sp))
        linhas.sort(key=lambda z: (z[0], z[1]))
        for col, ly, sp in linhas:
            # cabeçalho de seção 27pt?
            hdr = "".join(s["text"] for s in sp
                          if s["font"].startswith("Tormenta20") and 24 <= s["size"] <= 30)
            hdr = _acc(re.sub(r"\s+", " ", hdr).strip().lower())
            if hdr in SEC_MAP:
                if SEC_MAP[hdr] == "avatar":
                    if avatar_pno is None:
                        avatar_pno = pno
                    return secoes, avatar_pno   # lore termina no Avatar
                cur = SEC_MAP[hdr]
                continue
            # corpo: IowanOldStyle não-BoldItalic; drop-cap Tormenta20 grande vira prefixo
            partes = []
            for s in sp:
                fn, sz, t = s["font"], s["size"], s["text"]
                if fn.startswith("Tormenta20") and sz >= 30 and len(t.strip()) <= 2:
                    partes.append(t.strip())            # drop-cap
                elif "IowanOldStyle" in fn and "BoldItalic" not in fn:
                    partes.append(t)
            if partes:
                secoes[cur].append(" ".join(partes))
    return secoes, avatar_pno


def achar_pagina_avatar(doc, p0, p1):
    """Página com a ÂNCORA 16pt 'Avatar de X' (o stat block). NÃO usar a página do
    cabeçalho 27pt 'Avatar': lá os headers de seção 27pt viram âncoras bogus e mancham
    o nome do avatar (ex.: 'Igreja e Clero Avatar de Azgher')."""
    for pno in range(p0, p1 + 1):
        for b in doc[pno - 1].get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    if (s["font"].startswith("Tormenta20") and 13.5 <= s["size"] < 20
                            and s["text"].strip().lower().startswith("avatar")):
                        return pno
    return None


def extrair_avatar(doc, p0, p1):
    """Reusa o motor do bestiário no stat block do Avatar. Varre SÓ a página da âncora
    16pt (single page evita que os headers 27pt de seção virem âncoras)."""
    av_pno = achar_pagina_avatar(doc, p0, p1)
    if av_pno is None:
        return None, None
    for rng in [(av_pno, av_pno), (av_pno, min(av_pno + 1, p1))]:
        itens = best.reconstruir_linhas(doc, *rng)
        cs = best.segmentar_criaturas(itens, "Avatares")
        cand = [c for c in cs if c["nome"].lower().startswith("avatar")]
        if cand and cand[0].get("pv"):
            return cand[0], av_pno
    # último recurso: 1ª ficha da página single
    itens = best.reconstruir_linhas(doc, av_pno, av_pno)
    cs = best.segmentar_criaturas(itens, "Avatares")
    return (cs[0] if cs else None), av_pno


def junta(lst, dropcap=False):
    s = best.dehyph(" ".join(lst))
    if dropcap:
        s = re.sub(r"^([A-ZÀ-Ý]) ([a-zà-ÿ])", r"\1\2", s, count=1)
    return s


def main():
    print(f"Abrindo {PDF.name}...")
    doc = pymupdf.open(PDF)
    gods = deuses_toc(doc)
    print(f"deuses maiores no TOC: {len(gods)}")

    paginas = [p for _, p in gods]
    out = []
    for i, (titulo, p0) in enumerate(gods):
        p1 = (paginas[i + 1] - 1) if i + 1 < len(paginas) else 229
        nome = titulo.split(",")[0].strip()
        secoes, _ = coletar_lore(doc, p0, p1)
        avatar, av_pno = extrair_avatar(doc, p0, p1)
        # normaliza o nome do avatar com o nome PRÓPRIO do deus (TOC) — o versalete do
        # stat block às vezes rebaixa a caixa ("Avatar de nimb" -> "Avatar de Nimb")
        if avatar and avatar["nome"].lower().startswith("avatar de"):
            avatar["nome"] = f"Avatar de {nome}"

        d = {
            "id": f"deus-maior:deuses:{best.slug(nome)}",
            "tipo": "deus_expandido", "fonte": FONTE,
            "nome": nome, "titulo": titulo, "pagina": p0,
            "abertura": junta(secoes["abertura"], dropcap=True),
            "motivacoes": junta(secoes["motivacoes"]),
            "relacoes": junta(secoes["relacoes"]),
            "igreja_clero": junta(secoes["igreja_clero"]),
            "avatar": avatar,
        }
        out.append(d)
        av_ok = "A" if avatar and avatar.get("pv") else "-"
        print(f"  {nome:16.16} p{p0:>3}-{p1:<3} abert={len(d['abertura']):>4}c "
              f"motiv={len(d['motivacoes']):>4}c relac={len(d['relacoes']):>4}c "
              f"igreja={len(d['igreja_clero']):>4}c avatar={av_ok} "
              f"{'ND'+str(avatar['nd'])+' PV'+str(avatar['pv']) if avatar else ''}")

    dados = {"fonte": FONTE, "livro": "Deuses de Arton", "capitulo": "Capítulo 3: Deuses e Avatares",
             "total": len(out), "deuses": out}
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] {len(out)} deuses maiores -> {OUT}")


if __name__ == "__main__":
    main()
