# -*- coding: utf-8 -*-
r"""Integra o BESTIÁRIO DIVINO (Cap. 4 do *Deuses de Arton*) ao índice FAISS.

`fonte="deuses-arton"`, `capitulo="cap4-ameacas-divinas"` (idempotência ESTREITA por
capítulo — NÃO toca nos 325 chunks do Cap. 1, que compartilham a mesma fonte).

Granularidade:
  - 1 chunk fino por CRIATURA (56) com stat block completo, ataques, habilidades e atributos.
  - 1 chunk-LISTA por grupo (6: Abissais, Aspectos, Celestiais, Fadas, Gênios, Gigantes).
  - chunks-LISTA por faixa de ND (Iniciante/Veterano/Campeão/Lendário).

Integração ADITIVA; reconstrói o índice sem reembutir as outras famílias.

Uso: python integrar_ameacas_deuses.py
"""
import json
import shutil
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import fontes

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
AMEACAS_DEUSES_JSON = BASE / "dados" / "ameacas_deuses.json"
FONTE_ID = "deuses-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "cap4-ameacas-divinas"
SEC_BASE = "Deuses de Arton > Capítulo 4: Ameaças Divinas"


def chunk_criatura(c):
    """Chunk fino de uma criatura do bestiário divino."""
    nome = c["nome"]
    grupo = c["grupo"]
    nd = c["nd"]
    tipo = c["tipo_criatura"]
    subtipo = f" ({c['subtipo']})" if c.get("subtipo") else ""
    tamanho = c["tamanho"]
    papel = f" ({c['papel']})" if c.get("papel") not in ("Normal", "", None) else ""
    pag = c.get("pagina", 254)

    linhas = [
        f"Ameaça Divina: {nome} ({LIVRO}, Cap. 4, pág. {pag}).",
        f"Grupo: {grupo} | Nível de Desafio: ND {nd} | Tipo: {tipo}{subtipo} {tamanho}{papel}.",
        f"Defesa: {c['defesa']} | Fortitude: {c['fortitude']} | Reflexos: {c['reflexos']} | Vontade: {c['vontade']}.",
    ]
    if c.get("resistencias"):
        linhas.append(f"Resistências e Imunidades: {c['resistencias']}.")

    pm_str = f" | Pontos de Mana: {c['pm']}" if c.get("pm") and str(c.get("pm")) not in ("0", "") else ""
    linhas.append(f"Pontos de Vida: {c['pv']}{pm_str} | Deslocamento: {c['deslocamento']}.")

    sentidos_str = f", {c['sentidos']}" if c.get("sentidos") else ""
    linhas.append(f"Sentidos: Iniciativa {c['iniciativa']}, Percepção {c['percepcao']}{sentidos_str}.")

    if c.get("corpo_a_corpo"):
        linhas.append(f"Ataque Corpo a Corpo: {c['corpo_a_corpo']}")
    if c.get("distancia"):
        linhas.append(f"Ataque à Distância: {c['distancia']}")

    if c.get("habilidades"):
        linhas.append("Habilidades Especiais:")
        for h in c["habilidades"]:
            linhas.append(f"• {h['nome']}: {h['descricao']}")

    atrs = c.get("atributos", {})
    if atrs:
        linhas.append(
            f"Atributos: FOR {atrs.get('for', '—')} | DES {atrs.get('des', '—')} | CON {atrs.get('con', '—')} | "
            f"INT {atrs.get('int', '—')} | SAB {atrs.get('sab', '—')} | CAR {atrs.get('car', '—')}"
        )
    if c.get("pericias"):
        linhas.append(f"Perícias: {c['pericias']}.")
    if c.get("equipamento"):
        linhas.append(f"Equipamento: {c['equipamento']}.")
    if c.get("tesouro"):
        linhas.append(f"Tesouro: {c['tesouro']}.")

    return {
        "titulo": f"{nome} (ND {nd}) - Deuses de Arton",
        "secao": f"{SEC_BASE} > {grupo} > {nome}",
        "pagina": pag,
        "fonte": FONTE_ID,
        "capitulo": CAP,
        "texto": "\n".join(linhas),
        "tipo": "ameaca",
        "nome": nome,
        "grupo": grupo,
        "nd": nd,
        "tipo_criatura": tipo,
        "tamanho": tamanho,
        "papel": c.get("papel", "Normal"),
    }


def chunk_lista_grupo(grupo, criaturas):
    crias = [c for c in criaturas if c.get("grupo") == grupo]
    if not crias:
        return None
    linhas = [
        f"Lista de Ameaças Divinas: {grupo} ({LIVRO}, Cap. 4):",
        f"Total de {len(crias)} criaturas neste grupo:",
        "",
    ]
    for c in crias:
        linhas.append(
            f"• {c['nome']} (ND {c['nd']}): {c['tipo_criatura']} {c['tamanho']}, "
            f"Defesa {c['defesa']}, PV {c['pv']}. (pág. {c['pagina']})"
        )
    return {
        "titulo": f"Lista de Ameaças Divinas: {grupo} (Deuses de Arton)",
        "secao": f"{SEC_BASE} > Listas > Grupo {grupo}",
        "pagina": crias[0]["pagina"],
        "fonte": FONTE_ID,
        "capitulo": CAP,
        "texto": "\n".join(linhas),
        "tipo": "ameaca_lista",
        "categoria_filtro": "grupo",
        "grupo": grupo,
    }


def chunk_lista_nd(rotulo, nds, criaturas, pag):
    crias = [c for c in criaturas if str(c.get("nd")) in nds]
    if not crias:
        return None
    linhas = [
        f"Lista de Ameaças Divinas por Nível de Desafio: {rotulo} ({LIVRO}):",
        f"Total de {len(crias)} criaturas nesta faixa de ND:",
        "",
    ]
    for c in crias:
        linhas.append(
            f"• {c['nome']} (ND {c['nd']} - Grupo: {c['grupo']}): "
            f"{c['tipo_criatura']} {c['tamanho']}, Def {c['defesa']}, PV {c['pv']}."
        )
    return {
        "titulo": f"Lista de Ameaças Divinas por ND: {rotulo} (Deuses de Arton)",
        "secao": f"{SEC_BASE} > Listas > ND {rotulo}",
        "pagina": pag,
        "fonte": FONTE_ID,
        "capitulo": CAP,
        "texto": "\n".join(linhas),
        "tipo": "ameaca_lista",
        "categoria_filtro": "nd",
        "faixa_nd": rotulo,
    }


def gerar_chunks():
    data = json.loads(AMEACAS_DEUSES_JSON.read_text(encoding="utf-8"))
    criaturas = data.get("criaturas", [])
    novos = [chunk_criatura(c) for c in criaturas]

    for g in [x[0] for x in [
        ("Abissais",), ("Aspectos dos Deuses",), ("Celestiais",),
        ("Fadas",), ("Gênios",), ("Gigantes",)]]:
        ck = chunk_lista_grupo(g, criaturas)
        if ck:
            novos.append(ck)

    faixas = [
        ("Iniciante (ND 1/4 a ND 1)", ["1/4", "1/2", "1"], 254),
        ("Veterano (ND 2 a ND 4)", ["2", "3", "4"], 254),
        ("Campeão (ND 5 a ND 9)", ["5", "6", "7", "8", "9"], 254),
        ("Lendário (ND 10 a ND 20)", ["10", "11", "12", "13", "14", "15", "16",
                                      "17", "18", "19", "20", "S", "S+"], 254),
    ]
    for rot, nds, pag in faixas:
        ck = chunk_lista_nd(rot, nds, criaturas, pag)
        if ck:
            novos.append(ck)

    resumo = dict(criaturas=len(criaturas),
                  listas=len(novos) - len(criaturas),
                  total_chunks=len(novos))
    return novos, resumo


def eh_cap(c):
    return c.get("fonte") == FONTE_ID and c.get("capitulo") == CAP


def integrar():
    t0 = time.time()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = INDEX_DIR / f"backup-{ts}"
    print(f"[1/5] Backup em {backup_dir.name}")
    backup_dir.mkdir(exist_ok=True)
    for fn in ["chunks.jsonl", "meta.json", "tormenta.faiss"]:
        p = INDEX_DIR / fn
        if p.exists():
            shutil.copy2(p, backup_dir / fn)

    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    chunks_atuais = [json.loads(l) for l in (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    idx_faiss = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    dim = idx_faiss.d
    n_antes = len(chunks_atuais)
    print(f"[2/5] Índice atual: {n_antes} chunks, dim {dim}")

    manter_idx, mantidos, rem = [], [], 0
    for i, c in enumerate(chunks_atuais):
        if eh_cap(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks cap4-ameacas-divinas anteriores (idempotência estreita)")

    novos, resumo = gerar_chunks()
    print(f"[3/5] {len(novos)} chunks gerados: {resumo}.")

    if manter_idx:
        vecs_m = np.empty((len(manter_idx), dim), dtype="float32")
        for pos, old in enumerate(manter_idx):
            vecs_m[pos] = idx_faiss.reconstruct(int(old))
    else:
        vecs_m = np.empty((0, dim), dtype="float32")

    print(f"[4/5] Embutindo {len(novos)} chunks novos (BAAI/bge-m3)...")
    te = time.time()
    model = SentenceTransformer("BAAI/bge-m3")
    vecs_n = model.encode([c["texto"] for c in novos], batch_size=8,
                          show_progress_bar=False, normalize_embeddings=True).astype("float32")
    print(f"      {len(novos)} vetores em {time.time()-te:.1f}s")

    todos_vecs = np.vstack([vecs_m, vecs_n]) if len(vecs_m) else vecs_n
    novo_index = faiss.IndexFlatIP(dim)
    novo_index.add(todos_vecs)

    todos_chunks = mantidos + novos
    for i, c in enumerate(todos_chunks):
        c["id"] = i
    (INDEX_DIR / "chunks.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in todos_chunks) + "\n", encoding="utf-8")
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))

    meta["n_chunks"] = len(todos_chunks)
    meta["fontes"] = dict(Counter(c.get("fonte", "nucleo") for c in todos_chunks))
    meta["deuses_cap4_ameacas_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
