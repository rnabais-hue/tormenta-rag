# -*- coding: utf-8 -*-
r"""Limpeza da pendência "quadros de opção" (README §11): recupera o conteúdo dos
QUADROS DE OPÇÃO que `extrair_classes.py` descarta (fonte IowanOldStyle-Black) e o
anexa, como campo `opcoes`, ao PODER dono em dados/poderes_classe.json.

Quadros de opção de PODER (Black font), cada bloco = uma opção "• Nome. efeito":
  - pg44  Arcanista → Familiar         (10 animais)
  - pg48  Bárbaro   → Totem Espiritual (8 totens)
  - pg68  Druida    → Companheiro Animal (6 papéis) — o Caçador usa os MESMOS papéis
    (o "quadro na página 62" do Caçador é cross-ref furado, como o TOC do §7).

FORA daqui (não são quadro de opção de poder): Forma Selvagem do Druida (é TABELA,
"veja a seguir") e as 17 melhorias de arma do Inventor (pertencem a uma habilidade de
classe, não a um poder selecionável). Anotados no README como sub-pendências.

Enriquece poderes_classe.json in-place (idempotente). NÃO toca no índice — depois,
`integrar_poderes_classe.py` leva as opções ao chunk do poder. Uso:
  python extrair_opcoes_poder.py
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
POD = Path(__file__).parent / "dados" / "poderes_classe.json"

# página do quadro (1-based) -> (classe dona, nome do poder dono)
QUADROS = {
    44: ("Arcanista", "Familiar"),
    48: ("Bárbaro", "Totem Espiritual"),
    68: ("Druida", "Companheiro Animal"),
}
# poderes que reaproveitam as opções de outro poder (mesmo quadro no livro)
ALIAS = [("Caçador", "Companheiro Animal", "Druida", "Companheiro Animal")]


def dehyph(s):
    s = re.sub("[­\xad]\\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def opcoes_da_pagina(doc, pg1):
    """Extrai as opções (blocos Black) da página pg1 (1-based). Cada bloco é
    '• Nome. efeito'; um bloco pode conter >1 bullet."""
    page = doc[pg1 - 1]; W = page.rect.width; H = page.rect.height
    blocos = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        spans = [s for l in b["lines"] for s in l["spans"] if s["text"].strip()]
        if not any("Black" in s["font"] for s in spans):
            continue
        y0 = b["bbox"][1]
        x0 = b["bbox"][0]
        texto = "".join(s["text"] for s in spans)
        blocos.append((x0 < W * 0.40, y0, texto))
    blocos.sort(key=lambda r: (not r[0], r[1]))     # coluna esq primeiro, depois y
    opcoes = []
    for _, _, texto in blocos:
        for frag in texto.split("•"):
            frag = dehyph(frag)
            if not frag:
                continue
            nome, _, efeito = frag.partition(".")
            nome = nome.strip()
            efeito = efeito.strip()
            if nome and efeito:
                opcoes.append({"nome": nome, "efeito": efeito})
    return opcoes


def main():
    doc = pymupdf.open(PDF)
    poderes = json.loads(POD.read_text(encoding="utf-8"))
    idx = {(p["classe"], p["nome"]): p for p in poderes}

    extraidas = {}
    for pg1, (classe, nome) in QUADROS.items():
        ops = opcoes_da_pagina(doc, pg1)
        extraidas[(classe, nome)] = ops
        p = idx.get((classe, nome))
        if not p:
            print(f"  ! não achei o poder {classe} > {nome} em poderes_classe.json")
            continue
        p["opcoes"] = ops
        print(f"- {classe:<10} {nome:<20} {len(ops)} opções: "
              f"{', '.join(o['nome'] for o in ops)}")

    for classe, nome, src_classe, src_nome in ALIAS:
        p = idx.get((classe, nome))
        ops = extraidas.get((src_classe, src_nome))
        if p and ops:
            p["opcoes"] = [dict(o) for o in ops]
            print(f"- {classe:<10} {nome:<20} {len(ops)} opções (via {src_classe})")

    POD.write_text(json.dumps(poderes, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in extraidas.values())
    print(f"\npoderes_classe.json enriquecido com opções ({total} opções em "
          f"{len(QUADROS)} quadros + {len(ALIAS)} alias).")


if __name__ == "__main__":
    main()
