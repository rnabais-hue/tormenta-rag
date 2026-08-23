# -*- coding: utf-8 -*-
r"""
Integra os PODERES GERAIS estruturados (dados/poderes_gerais.json) ao índice FAISS
— Stage A da família "poderes", categorias combate/destino/magia/concedido/tormenta.

Substitui os ~29 chunks de TEXTO CORRIDO da seção "Poderes Gerais" (págs 130–143,
gerados pela ingestão via TOC) por granularidade FINA:
  - 1 chunk por PODER (nome + efeito + pré-requisito + deus verbalizados).
  - 1 chunk-lista por CATEGORIA (só os nomes) — "quais poderes de combate existem".
  - 1 chunk-lista por DEUS (nomes dos concedidos) — "que poderes o Khalmyr concede".
    O agrupamento por deus é o análogo dos concedidos ao "por classe".

Metadados por chunk de poder (insumo dos Stages B/C/D): tipo="poder", categoria,
nome, pre_requisito, e deuses[] (só concedidos → elegibilidade por devoção).

NÃO toca nos poderes de CLASSE (categoria="classe") nem em outros chunks — reconstrói
o índice sem reembutir o resto. Idempotente (remove poderes-gerais anteriores antes de
reinserir). Uso: python integrar_poderes_gerais.py
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
PODERES_JSON = BASE / "dados" / "poderes_gerais.json"

GERAIS = {"combate", "destino", "magia", "concedido", "tormenta"}
CAT_TEXT = {"combate": "de combate", "destino": "de destino", "magia": "de magia",
            "concedido": "concedido", "tormenta": "da tormenta"}
CAT_SEC = {"combate": "Poderes de Combate", "destino": "Poderes de Destino",
           "magia": "Poderes de Magia", "concedido": "Poderes Concedidos",
           "tormenta": "Poderes da Tormenta"}
SEC_BASE = "Capítulo 2: Perícias & Poderes > Poderes Gerais"


def eh_texto_corrido_gerais(chunk):
    """Chunk antigo (ingestão via TOC) da seção Poderes Gerais — a substituir."""
    return chunk.get("tipo") != "poder" and "Poderes Gerais" in chunk.get("secao", "")


def eh_poder_geral(chunk):
    """Chunk de poder-geral já inserido por ESTE script (idempotência).
    NÃO casa os poderes de classe (categoria='classe')."""
    return chunk.get("tipo") == "poder" and chunk.get("categoria") in GERAIS


def chunks_de_poderes(poderes):
    """Gera os chunks: 1 por poder + 1 lista por categoria + 1 lista por deus."""
    saida = []
    por_cat = {}
    por_deus = {}
    for p in poderes:
        cat, pg = p["categoria"], p["pagina"]
        sec = f"{SEC_BASE} > {CAT_SEC[cat]} > {p['nome']}"
        linhas = [f"Poder {CAT_TEXT[cat]}: {p['nome']} (Tormenta20, pág. {pg})."]
        deuses = p.get("deuses") or []
        if deuses:
            linhas.append(f"Concedido pelo(s) deus(es): {', '.join(deuses)}.")
        linhas.append(p["efeito"])
        if p.get("pre_requisito"):
            linhas.append(f"Pré-requisito: {p['pre_requisito']}.")
        chunk = {
            "titulo": p["nome"],
            "secao": sec, "pagina": pg,
            "texto": "\n".join(linhas),
            "tipo": "poder", "categoria": cat, "subtipo": "poder",
            "nome": p["nome"], "pre_requisito": p.get("pre_requisito"),
        }
        if deuses:
            chunk["deuses"] = deuses
        saida.append(chunk)

        por_cat.setdefault(cat, {"nomes": [], "pagina": pg})["nomes"].append(p["nome"])
        for d in deuses:
            por_deus.setdefault(d, {"nomes": [], "pagina": pg})["nomes"].append(p["nome"])

    # lista por categoria
    for cat, d in por_cat.items():
        nomes = d["nomes"]
        texto = (f"{CAT_SEC[cat]} de Tormenta20 (pág. {d['pagina']}). "
                 f"São {len(nomes)} poderes: " + ", ".join(nomes) + ".")
        saida.append({
            "titulo": f"{CAT_SEC[cat]}: lista",
            "secao": f"{SEC_BASE} > {CAT_SEC[cat]}", "pagina": d["pagina"],
            "texto": texto,
            "tipo": "poder", "categoria": cat, "subtipo": "lista",
        })

    # lista por deus (concedidos)
    for deus, d in sorted(por_deus.items()):
        nomes = d["nomes"]
        texto = (f"Poderes concedidos pelo deus {deus} em Tormenta20 (pág. {d['pagina']}). "
                 f"Um devoto de {deus} pode escolher estes {len(nomes)} poderes concedidos: "
                 + ", ".join(nomes) + ".")
        saida.append({
            "titulo": f"Poderes concedidos por {deus}",
            "secao": f"{SEC_BASE} > {CAT_SEC['concedido']} > {deus}", "pagina": d["pagina"],
            "texto": texto,
            "tipo": "poder", "categoria": "concedido", "subtipo": "lista_deus",
            "deus": deus,
        })
    return saida


def main():
    if not PODERES_JSON.exists():
        raise SystemExit(f"Não achei {PODERES_JSON}. Rode extrair_poderes_gerais.py antes.")
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py antes.")

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
              if not eh_texto_corrido_gerais(c) and not eh_poder_geral(c)]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos (texto corrido Poderes Gerais + re-run)")

    poderes = json.loads(PODERES_JSON.read_text(encoding="utf-8"))
    novos = chunks_de_poderes(poderes)
    n_pod = sum(1 for c in novos if c["subtipo"] == "poder")
    n_cat = sum(1 for c in novos if c["subtipo"] == "lista")
    n_deus = sum(1 for c in novos if c["subtipo"] == "lista_deus")
    print(f"[3/5] {len(poderes)} poderes -> {len(novos)} chunks "
          f"({n_pod} poderes + {n_cat} listas-categoria + {n_deus} listas-deus)")

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
    meta["poderes_gerais_estruturados"] = len(poderes)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} de poder). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
