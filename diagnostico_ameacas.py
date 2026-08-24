# -*- coding: utf-8 -*-
r"""Ferramenta de DEEP DIVE e DIAGNÓSTICO do Bestiário de Ameaças de Arton.

Permite inspecionar criaturas com pendências, visualizar os spans brutos do PDF,
entender exatamente por que um campo falhou e testar correções.

Uso:
    python diagnostico_ameacas.py                      # Resumo geral e lista de pendências
    python diagnostico_ameacas.py --tipo ND            # Lista criaturas com ND ausente/inválido
    python diagnostico_ameacas.py --tipo defesa        # Lista criaturas sem Defesa
    python diagnostico_ameacas.py --tipo atributos     # Lista criaturas sem Atributos
    python diagnostico_ameacas.py --nome "Sckhar"      # Raio-X completo de uma criatura (PDF + JSON)
    python diagnostico_ameacas.py --pagina 79          # Inspeciona todos os spans e blocos da página
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF_PATH = BASE / "livro" / "Ameacas-de-Arton-v1.0-17-11-2023.pdf"
DADOS_PATH = BASE / "dados" / "ameacas_arton.json"


def carregar_dados():
    if not DADOS_PATH.exists():
        print(f"Erro: Arquivo {DADOS_PATH} não encontrado. Execute extrair_ameacas_arton.py primeiro.")
        sys.exit(1)
    return json.loads(DADOS_PATH.read_text(encoding="utf-8"))


def diagnosticar_criatura(c):
    probs = []
    if c.get("nd") in (None, "", "?"):
        probs.append("ND")
    if not c.get("defesa"):
        probs.append("defesa")
    if not c.get("pv"):
        probs.append("pv")
    at = c.get("atributos") or {}
    preenchidos = [k for k, v in at.items() if v]
    if len(preenchidos) < 4:
        probs.append("atributos")
    if not c.get("corpo_a_corpo") and not c.get("distancia"):
        probs.append("ataques")
    if not c.get("habilidades"):
        probs.append("habilidades")
    nome = c.get("nome", "")
    if len(nome) < 3:
        probs.append("nome_curto")
    return probs


def mostrar_resumo(dados):
    crias = dados.get("criaturas", [])
    total = len(crias)
    counter = Counter()
    com_problema = []

    for c in crias:
        p = diagnosticar_criatura(c)
        if p:
            com_problema.append((c, p))
            for prob in p:
                counter[prob] += 1

    print(f"\n{'='*25} RESUMO DO BESTIÁRIO ({total} criaturas) {'='*25}")
    print(f"Criaturas 100% completas: {total - len(com_problema)} ({((total - len(com_problema))/total)*100:.1f}%)")
    print(f"Criaturas com alguma pendência: {len(com_problema)} ({(len(com_problema)/total)*100:.1f}%)\n")

    print("Contagem de Pendências por Campo:")
    for campo, qtd in counter.most_common():
        print(f"  - {campo.upper():12s}: {qtd:3d} criaturas ({(qtd/total)*100:.1f}%)")

    print(f"\nPara filtrar por tipo de pendência:")
    print("  python diagnostico_ameacas.py --tipo ND")
    print("  python diagnostico_ameacas.py --tipo defesa")
    print("  python diagnostico_ameacas.py --tipo atributos")
    print("\nPara inspecionar uma criatura específica:")
    print("  python diagnostico_ameacas.py --nome \"Nome da Criatura\"")


def listar_por_tipo(dados, tipo_filtro):
    tipo_filtro = tipo_filtro.lower()
    crias = dados.get("criaturas", [])
    matches = []
    for c in crias:
        probs = diagnosticar_criatura(c)
        if tipo_filtro in [p.lower() for p in probs]:
            matches.append((c, probs))

    print(f"\n{'='*20} CRIATURAS COM PROBLEMA EM '{tipo_filtro.upper()}' ({len(matches)}) {'='*20}")
    for c, probs in matches:
        print(f"- [{c.get('grupo')}] {c.get('nome'):35s} | ND: {str(c.get('nd')):4s} | pág {c.get('pagina'):3d} | Pendências: {probs}")


def inspecionar_criatura(dados, nome_busca):
    doc = pymupdf.open(str(PDF_PATH))
    crias = dados.get("criaturas", [])
    alvo = None
    for c in crias:
        if nome_busca.lower() in c.get("nome", "").lower():
            alvo = c
            break

    if not alvo:
        print(f"Criatura com '{nome_busca}' não encontrada no JSON.")
        return

    pno = alvo.get("pagina")
    print(f"\n{'='*25} RAIO-X: {alvo.get('nome')} (pág {pno}) {'='*25}")
    print(f"Grupo : {alvo.get('grupo')}")
    print(f"ND    : {alvo.get('nd')}")
    print(f"Tipo  : {alvo.get('tipo_criatura')} {alvo.get('subtipo')} {alvo.get('tamanho')} ({alvo.get('papel')})")
    print(f"Defesa: {alvo.get('defesa')} | PV: {alvo.get('pv')} | PM: {alvo.get('pm')}")
    print(f"Resist: Fort {alvo.get('fortitude')}, Ref {alvo.get('reflexos')}, Von {alvo.get('vontade')} | {alvo.get('resistencias')}")
    print(f"Atrib : {alvo.get('atributos')}")
    print(f"Ataque: CaC: {alvo.get('corpo_a_corpo')} | Dist: {alvo.get('distancia')}")
    print(f"Habil : {len(alvo.get('habilidades', []))} habilidades capturadas")
    for h in alvo.get("habilidades", []):
        print(f"  • {h.get('nome')}: {h.get('descricao')[:80]}...")

    print(f"\nPendências diagnosticadas: {diagnosticar_criatura(alvo)}")

    print(f"\n--- Spans brutos no PDF (Páginas {pno} a {min(pno+1, len(doc))}) ---")
    for p in range(pno, min(pno + 2, len(doc) + 1)):
        page = doc[p - 1]
        for b in page.get_text("dict")["blocks"]:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    fn, sz, tx = s["font"], s["size"], s["text"].strip()
                    if not tx or fn.startswith("Helvetica") or fn.startswith("Iowan"):
                        continue
                    x0, y0 = s["bbox"][0], s["bbox"][1]
                    col = "C1" if x0 < 300 else "C2"
                    print(f"  [Pág {p} {col} {fn[:16]:16s} sz={sz:4.1f} y={y0:5.1f}] {tx!r}")


def inspecionar_pagina(pno):
    doc = pymupdf.open(str(PDF_PATH))
    if pno < 1 or pno > len(doc):
        print(f"Página inválida (livro tem 1 a {len(doc)} págs).")
        return
    page = doc[pno - 1]
    print(f"\n{'='*25} SPANS E BLOCOS DA PÁGINA {pno} {'='*25}")
    for b_idx, b in enumerate(page.get_text("dict")["blocks"]):
        if "lines" not in b:
            continue
        bbox = [round(x, 1) for x in b["bbox"]]
        print(f"\n--- Bloco {b_idx} (x0={bbox[0]}, y0={bbox[1]}, x1={bbox[2]}, y1={bbox[3]}) ---")
        for l in b["lines"]:
            for s in l["spans"]:
                fn, sz, tx = s["font"], s["size"], s["text"]
                if not tx.strip():
                    continue
                bbox_s = [round(x, 1) for x in s["bbox"]]
                col = "Col 1" if bbox_s[0] < 300 else "Col 2"
                print(f"  [{col} {fn[:16]:16s} sz={sz:4.1f} y={bbox_s[1]:5.1f}] {tx!r}")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    dados = carregar_dados()

    args = sys.argv[1:]
    if not args:
        mostrar_resumo(dados)
        return

    if "--tipo" in args:
        idx = args.index("--tipo")
        if idx + 1 < len(args):
            listar_por_tipo(dados, args[idx + 1])
        else:
            print("Especifique o tipo: --tipo ND, --tipo defesa, --tipo atributos, etc.")
    elif "--nome" in args:
        idx = args.index("--nome")
        if idx + 1 < len(args):
            inspecionar_criatura(dados, args[idx + 1])
        else:
            print("Especifique o nome: --nome \"Sckhar\"")
    elif "--pagina" in args:
        idx = args.index("--pagina")
        if idx + 1 < len(args):
            try:
                inspecionar_pagina(int(args[idx + 1]))
            except ValueError:
                print("Número de página inválido.")
        else:
            print("Especifique o número da página: --pagina 79")
    else:
        mostrar_resumo(dados)


if __name__ == "__main__":
    main()
