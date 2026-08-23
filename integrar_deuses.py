# -*- coding: utf-8 -*-
r"""
Integra os DEUSES estruturados (dados/deuses.json) ao índice FAISS.

Granularidade: 1 chunk por DEUS — resumo + campos no texto, com metadados
`energia`/`devotos`/`poderes_concedidos` (base do filtro híbrido em perguntar.py).
Substitui os ~47 chunks de TEXTO CORRIDO das entradas de deus (secao "...> Deuses
> <Nome>"), mantendo a introdução. Reconstrói o índice SEM reembutir o resto.

Idempotente (remove deuses estruturados anteriores antes de reinserir).
Uso: python integrar_deuses.py
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
DEUSES_JSON = BASE / "dados" / "deuses.json"
SEC_BASE = "Capítulo 2: Perícias & Poderes > Deuses"


def texto_deus(d):
    linhas = [f"Deus: {d['nome']} (Tormenta20, pág. {d['pagina']})."]
    if d.get("resumo"):
        linhas.append(d["resumo"])
    if d.get("crencas"):
        linhas.append(f"Crenças e objetivos: {d['crencas']}")
    if d.get("energia"):
        linhas.append(f"Canaliza energia: {d['energia']}.")
    if d.get("arma_preferida"):
        linhas.append(f"Arma preferida: {d['arma_preferida']}.")
    if d.get("simbolo"):
        linhas.append(f"Símbolo sagrado: {d['simbolo']}")
    if d.get("devotos"):
        linhas.append(f"Devotos (quem pode segui-lo): {', '.join(d['devotos'])}.")
    if d.get("poderes_concedidos"):
        linhas.append(f"Poderes concedidos: {', '.join(d['poderes_concedidos'])}.")
    if d.get("obrigacoes"):
        linhas.append(f"Obrigações e restrições: {d['obrigacoes']}")
    return "\n".join(linhas)


def chunk_de_deus(d):
    return {
        "titulo": d["nome"],
        "secao": f"{SEC_BASE} > {d['nome']}",
        "pagina": d["pagina"],
        "texto": texto_deus(d),
        "tipo": "deus", "nome": d["nome"],
        "energia": d.get("energia"),
        "devotos": d.get("devotos", []),
        "poderes_concedidos": d.get("poderes_concedidos", []),
    }


def main():
    if not DEUSES_JSON.exists():
        raise SystemExit(f"Não achei {DEUSES_JSON}. Rode extrair_deuses.py antes.")
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py antes.")

    deuses = json.loads(DEUSES_JSON.read_text(encoding="utf-8"))
    nomes = {d["nome"] for d in deuses}

    def eh_texto_corrido_deus(c):
        sec = c.get("secao", "")
        return (c.get("tipo") != "deus" and "> Deuses >" in sec
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
              if not eh_texto_corrido_deus(c) and c.get("tipo") != "deus"]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos (texto corrido de deus + re-run)")

    novos = [chunk_de_deus(d) for d in deuses]
    print(f"[3/5] {len(deuses)} deuses -> {len(novos)} chunks estruturados")

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
    meta["deuses_estruturados"] = len(deuses)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} deuses). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
