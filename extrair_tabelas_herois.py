# -*- coding: utf-8 -*-
r"""Extração das TABELAS PARA PERSONAGENS de *Heróis de Arton* (Cap. 1, págs 98–103).

Tabelas de rolagem (d%) de flavor/roleplay — 1-24 Nomes de Personagens (por raça),
1-25 Aparência, 1-26 Trejeitos, 1-27 Objetivos, 1-28 Nomes p/ Montarias e Mascotes,
1-29 Nomes p/ Guildas e Bandos. Não são entidades: o valor no RAG é recuperar a
TABELA inteira (1 chunk por tabela) — não vale estruturar célula a célula.

Saída: dados/tabelas_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "tabelas_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PAG_INI, PAG_FIM = 98, 103

RUIDO = re.compile(r"^(Campeões de Arton|Capítulo 1|\d{1,3})$")
MARCADOR = re.compile(r"Tabela\s+1-(\d+):\s*(.+)")


def limpa_linhas(txt):
    out = []
    for ln in txt.splitlines():
        ln = ln.strip()
        if not ln or RUIDO.match(ln):
            continue
        out.append(ln)
    return out


def main():
    doc = pymupdf.open(str(PDF))
    linhas = []
    for pno in range(PAG_INI, PAG_FIM + 1):
        linhas += limpa_linhas(doc[pno - 1].get_text())

    tabelas = []          # [{numero, titulo, corpo[]}]
    atual = None
    for ln in linhas:
        m = MARCADOR.match(ln)
        if m:
            num = m.group(1)
            titulo = m.group(2).strip()
            cont = "continua" in titulo.lower()
            titulo = re.sub(r"\s*\(Continua[^)]*\)", "", titulo).strip()
            if cont and atual and atual["numero"] == num:
                continue                      # continuação: mantém acumulando
            if atual and atual["numero"] == num:
                continue
            atual = {"numero": num, "titulo": titulo, "corpo": []}
            tabelas.append(atual)
            continue
        if atual is not None:
            atual["corpo"].append(ln)

    registros = []
    for t in tabelas:
        pagina = PAG_INI + int(t["numero"]) - 24    # 1-24->98 ... aproximado
        corpo = " ".join(t["corpo"])
        corpo = re.sub(r"\s+", " ", corpo).strip()
        registros.append({
            "id": f"tabela:herois:1-{t['numero']}",
            "tipo": "tabela", "fonte": FONTE, "versao": "1.1",
            "numero": f"1-{t['numero']}", "titulo": t["titulo"],
            "texto": corpo[:4000],
        })

    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "total": len(registros),
             "tabelas": registros}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(registros)} tabelas -> {OUT.name}\n")
    for r in registros:
        print(f"  - Tabela {r['numero']}: {r['titulo']:<34} ({len(r['texto'])} chars)")


if __name__ == "__main__":
    main()
