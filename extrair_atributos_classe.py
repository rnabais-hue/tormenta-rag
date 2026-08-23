# -*- coding: utf-8 -*-
r"""
Extrai o ATRIBUTO PRINCIPAL de cada classe da Tabela 1-3 (Classes), pág. 32 do
livro (pág. 38 do PDF) e grava o campo `atributo_principal` em dados/classes.json.

Por que esta tabela (e não as habilidades): o livro define, de forma AUTORITATIVA
e para TODAS as 14 classes, o atributo principal nesta tabela-resumo — inclusive a
FLEXIBILIDADE de build ("Força ou Destreza", "Destreza ou Inteligência", "Força e
Carisma"). É o fato impresso; a derivação por habilidades (derivar_atributo_chave.py)
só cobria conjuradores+Paladino. Este campo vira o texto do chunk da classe
(integrar_classes.py) — RAG, sem regex hard-coded.

Tipografia = schema: a coluna "Atributo" fica em x≈295–315 (fonte SourceSansPro,
~9pt); o nome da classe em x≈55 (mesma fonte). Valores de duas linhas ("Força ou /
Destreza") são unidos por proximidade vertical, cada span da coluna atribuído à
classe cujo nome está verticalmente mais próximo.

Uso:
  python extrair_atributos_classe.py            # grava em classes.json
  python extrair_atributos_classe.py --dry      # só mostra
"""

import argparse
import json
import re
import sys
import io
from pathlib import Path

import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
ARQ_CLASSES = BASE / "dados" / "classes.json"
PAGINA_PDF = 37                      # índice 0 → pág. 38 do PDF (pág. 32 do livro)

NOMES = ["Arcanista", "Bárbaro", "Bardo", "Bucaneiro", "Caçador", "Cavaleiro",
         "Clérigo", "Druida", "Guerreiro", "Inventor", "Ladino", "Lutador",
         "Nobre", "Paladino"]
ATTRS = {"Força", "Destreza", "Constituição", "Inteligência", "Sabedoria", "Carisma"}
_X_NOME = (45, 120)                  # coluna do nome da classe
_X_ATTR = (280, 345)                 # coluna "Atributo"


def _spans(pagina):
    out = []
    for b in pagina.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"].strip()
                if t:
                    out.append((s["bbox"][0], s["bbox"][1], round(s["size"], 1), t))
    return out


def _estruturar(texto):
    """'Força ou Destreza' → {texto, atributos:[...], relacao:'ou'|'e'|None}."""
    rel = "ou" if " ou " in texto else ("e" if re.search(r"\be\b", texto) else None)
    achados = [a for a in ["Força", "Destreza", "Constituição", "Inteligência",
                           "Sabedoria", "Carisma"] if a in texto]
    return {"texto": texto, "atributos": achados, "relacao": rel}


def extrair():
    doc = pymupdf.open(PDF)
    spans = _spans(doc[PAGINA_PDF])

    # linhas de nome de classe (x na coluna do nome, texto = nome conhecido)
    nomes_y = {}
    for x, y, sz, t in spans:
        if _X_NOME[0] <= x <= _X_NOME[1] and t in NOMES:
            nomes_y[t] = y

    # spans da coluna "Atributo" (exclui o cabeçalho 'Atributo' em negrito ~10pt)
    attr_spans = [(y, t) for x, y, sz, t in spans
                  if _X_ATTR[0] <= x <= _X_ATTR[1] and t != "Atributo"
                  and (any(a in t for a in ATTRS) or t in ("ou", "e",
                       "Força ou", "Destreza ou", "Força e"))]

    # atribui cada span ao nome de classe verticalmente mais próximo
    linhas = {n: [] for n in NOMES}
    for y, t in attr_spans:
        classe = min(nomes_y, key=lambda n: abs(nomes_y[n] - y))
        linhas[classe].append((y, t))

    resultado = {}
    for n in NOMES:
        partes = [t for _, t in sorted(linhas[n])]
        texto = re.sub(r"\s+", " ", " ".join(partes)).strip()
        resultado[n] = _estruturar(texto)
    return resultado


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    tabela = extrair()
    for n in NOMES:
        print(f"  {n:12} → {tabela[n]['texto']:22} {tabela[n]['atributos']} rel={tabela[n]['relacao']}")

    # sanidade: todos com ao menos 1 atributo
    faltando = [n for n in NOMES if not tabela[n]["atributos"]]
    if faltando:
        raise SystemExit(f"ERRO: sem atributo extraído para {faltando}")

    if args.dry:
        print("\n(dry-run — nada gravado)")
        return

    classes = json.loads(ARQ_CLASSES.read_text(encoding="utf-8"))
    for c in classes:
        if c["nome"] in tabela:
            c["atributo_principal"] = tabela[c["nome"]]
    ARQ_CLASSES.write_text(json.dumps(classes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGravado atributo_principal em {ARQ_CLASSES.name} ({len(tabela)} classes).")


if __name__ == "__main__":
    main()
