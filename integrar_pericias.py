# -*- coding: utf-8 -*-
r"""
Integra as PERÍCIAS estruturadas (dados/pericias.json) ao índice FAISS.

Granularidade (escolhida): 1 chunk por PERÍCIA — resumo + usos no texto, com os
metadados atributo/so_treinada/penalidade_armadura (base do filtro híbrido em
perguntar.py). Substitui os 79 chunks de TEXTO CORRIDO das entradas de perícia
(secao "...> Perícias > <Nome>"), mantendo a introdução ("Escolhendo/Usando
Perícias"). Reconstrói o índice SEM reembutir o resto (só as 29 perícias, ~30s).

Idempotente (remove perícias estruturadas anteriores antes de reinserir).
Uso: python integrar_pericias.py
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
PERICIAS_JSON = BASE / "dados" / "pericias.json"
SEC_BASE = "Capítulo 2: Perícias & Poderes > Perícias"


def texto_pericia(p):
    linhas = [f"Perícia: {p['nome']} (Tormenta20, pág. {p['pagina']}). "
              f"Atributo-chave: {p['atributo']}."]
    marcas = []
    if p.get("so_treinada"):
        marcas.append("Só pode ser usada por quem é treinado na perícia.")
    if p.get("penalidade_armadura"):
        marcas.append("Sofre penalidade de armadura.")
    if marcas:
        linhas.append(" ".join(marcas))
    if p.get("resumo"):
        linhas.append(p["resumo"])
    if p.get("usos"):
        linhas.append("Usos:")
        for u in p["usos"]:
            tags = []
            if u.get("cd") is not None:
                tags.append(f"CD {u['cd']}")
            if u.get("apenas_treinado"):
                tags.append("apenas treinado")
            suf = f" ({', '.join(tags)})" if tags else ""
            linhas.append(f"- {u['nome']}{suf}: {u['efeito']}")
    return "\n".join(linhas)


def chunk_de_pericia(p):
    return {
        "titulo": p["nome"],
        "secao": f"{SEC_BASE} > {p['nome']}",
        "pagina": p["pagina"],
        "texto": texto_pericia(p),
        "tipo": "pericia", "nome": p["nome"],
        "atributo": p["atributo"],
        "so_treinada": bool(p.get("so_treinada")),
        "penalidade_armadura": bool(p.get("penalidade_armadura")),
        "usos": p.get("usos", []),
    }


def main():
    if not PERICIAS_JSON.exists():
        raise SystemExit(f"Não achei {PERICIAS_JSON}. Rode extrair_pericias.py antes.")
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py antes.")

    pericias = json.loads(PERICIAS_JSON.read_text(encoding="utf-8"))
    nomes = {p["nome"] for p in pericias}

    def eh_texto_corrido_pericia(c):
        sec = c.get("secao", "")
        return (c.get("tipo") != "pericia" and "> Perícias >" in sec
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
              if not eh_texto_corrido_pericia(c) and c.get("tipo") != "pericia"]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos (texto corrido de perícia + re-run)")

    novos = [chunk_de_pericia(p) for p in pericias]
    print(f"[3/5] {len(pericias)} perícias -> {len(novos)} chunks estruturados")

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
    meta["pericias_estruturadas"] = len(pericias)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} perícias). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
