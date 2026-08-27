# -*- coding: utf-8 -*-
r"""Integra as ORIGENS REGIONAIS do *Atlas de Arton* (Apêndice) ao FAISS.

1º recorte do 3º livro de expansão. `fonte="atlas-arton"`, `capitulo="origens-regionais"`
(idempotência estreita própria). 66 origens ligadas a reinos/regiões de Arton.

Uso: python integrar_origens_regionais_atlas.py
"""
import json, shutil, time
from collections import Counter
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import fontes

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
FONTE_ID = "atlas-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "origens-regionais"
SEC = "Atlas de Arton > Apêndice: Origens Regionais"
D = BASE / "dados"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de():
    d = json.loads((D / "origens_regionais_atlas.json").read_text(encoding="utf-8"))
    out = []
    out.append(base_chunk("Origens Regionais (visão geral)", "Visão Geral", d["pagina"],
                          f"Regra do {LIVRO} (Apêndice). Origens Regionais: {d['introducao']}",
                          tipo="regra", subtipo="overview"))
    for o in d["origens"]:
        reg = f" (região: {o['regiao']})" if o.get("regiao") else ""
        per = f"\nPerícias treinadas: {', '.join(o['pericias'])}." if o.get("pericias") else ""
        texto = (f"Origem regional: {o['nome']}{reg} — {LIVRO}, pág. {o['pagina']}. É uma origem "
                 f"ligada a um reino/região (escolhida no lugar da origem comum).\n"
                 f"Itens: {o['itens']}\nBenefício: {o['beneficio']}{per}")
        out.append(base_chunk(f"Origem Regional: {o['nome']}", f"{o.get('regiao') or 'Origem'} > {o['nome']}",
                              o["pagina"], texto, tipo="origem", subtipo="regional", nome=o["nome"],
                              regiao=o.get("regiao"), pericias=o.get("pericias", [])))
    # lista por região
    porreg = {}
    for o in d["origens"]:
        porreg.setdefault(o.get("regiao") or "—", []).append(o["nome"])
    lst = "; ".join(f"{reg}: {', '.join(ns)}" for reg, ns in sorted(porreg.items()))
    out.append(base_chunk("Lista das Origens Regionais (por região)", "Lista", d["pagina"],
                          f"As {d['total']} Origens Regionais de {LIVRO} (Apêndice), por região — {lst}.",
                          tipo="origem_lista"))
    resumo = dict(origens=d["total"], regioes=len({o.get("regiao") for o in d["origens"]}),
                  total_chunks=len(out))
    return out, resumo


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
        print(f"      Removendo {rem} chunks origens-regionais anteriores (idempotência estreita)")

    novos, resumo = chunks_de()
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
    meta["atlas_origens_regionais_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
