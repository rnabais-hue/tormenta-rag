# -*- coding: utf-8 -*-
r"""
Integra as ORIGENS estruturadas (dados/origens.json) ao índice FAISS.

Granularidade (escolhida): 1 chunk por ORIGEM — resumo + itens + benefícios +
poder único no texto, com metadados `pericias`/`poderes`/`poder_unico` (base do
filtro híbrido em perguntar.py). Substitui os ~88 chunks de TEXTO CORRIDO das
entradas de origem (secao "...> Origens > <Nome>"), mantendo a introdução
("Origens", "Sua Própria Origem"). Reconstrói o índice SEM reembutir o resto.

Idempotente (remove origens estruturadas anteriores antes de reinserir).
Uso: python integrar_origens.py
"""

import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
ORIGENS_JSON = BASE / "dados" / "origens.json"
SEC_BASE = "Capítulo 1: Construção de Personagem > Origens"


def texto_origem(o):
    linhas = [f"Origem: {o['nome']} (Tormenta20, pág. {o['pagina']})."]
    if o.get("resumo"):
        linhas.append(o["resumo"])
    if o.get("itens"):
        linhas.append(f"Itens de origem: {o['itens']}.")
    if o.get("beneficios"):
        linhas.append(f"Benefícios (escolha dois): {o['beneficios']}")
    pu = o.get("poder_unico")
    if pu and pu.get("nome"):
        linhas.append(f"Poder único — {pu['nome']}: {pu.get('efeito', '')}")
    return "\n".join(linhas)


def chunk_de_origem(o):
    c = {
        "titulo": o["nome"],
        "secao": f"{SEC_BASE} > {o['nome']}",
        "pagina": o["pagina"],
        "texto": texto_origem(o),
        "tipo": "origem", "nome": o["nome"],
        "pericias": o.get("pericias", []),
        "poderes": o.get("poderes", []),
    }
    if o.get("poder_unico"):
        c["poder_unico"] = o["poder_unico"]
    return c


def main():
    if not ORIGENS_JSON.exists():
        raise SystemExit(f"Não achei {ORIGENS_JSON}. Rode extrair_origens.py antes.")
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py antes.")

    origens = json.loads(ORIGENS_JSON.read_text(encoding="utf-8"))
    nomes = {o["nome"] for o in origens}

    def eh_texto_corrido_origem(c):
        sec = c.get("secao", "")
        return (c.get("tipo") != "origem" and "> Origens >" in sec
                and sec.split(" > ")[-1].strip() in nomes)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = INDEX_DIR / f"backup-{stamp}"
    bkp.mkdir(parents=True)
    for nome in ("tormenta.faiss", "chunks.jsonl", "meta.json"):
        shutil.copy2(INDEX_DIR / nome, bkp / nome)
    print(f"[1/5] Backup do indice em {bkp.name}\\")

    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    chunks = [json.loads(l) for l in
              (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert index.ntotal == len(chunks), "indice e chunks.jsonl desalinhados!"
    dim = meta["dim"]
    vetores = index.reconstruct_n(0, index.ntotal)
    print(f"[2/5] Indice atual: {len(chunks)} chunks, dim {dim}")

    manter = [(c, vetores[i]) for i, c in enumerate(chunks)
              if not eh_texto_corrido_origem(c) and c.get("tipo") != "origem"]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos (texto corrido de origem + re-run)")

    novos = [chunk_de_origem(o) for o in origens]
    print(f"[3/5] {len(origens)} origens -> {len(novos)} chunks estruturados")

    print(f"[4/5] Carregando embedder {meta['modelo_embed']} e embutindo…")
    t = time.time()
    model = SentenceTransformer(meta["modelo_embed"])
    emb = model.encode([c["texto"] for c in novos], normalize_embeddings=True,
                       batch_size=8, show_progress_bar=False).astype("float32")
    print(f"      {len(novos)} vetores em {time.time() - t:.0f}s")

    vecs_manter = np.array([v for _, v in manter], dtype="float32") if manter else np.empty((0, dim), "float32")
    todos_vecs = np.vstack([vecs_manter, emb]).astype("float32")
    todos_chunks = [c for c, _ in manter] + novos
    for i, c in enumerate(todos_chunks):
        c["id"] = i

    novo_index = faiss.IndexFlatIP(dim)
    novo_index.add(todos_vecs)
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))
    with open(INDEX_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in todos_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    meta["n_chunks"] = len(todos_chunks)
    meta["origens_estruturadas"] = len(origens)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} origens). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
