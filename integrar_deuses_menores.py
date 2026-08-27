# -*- coding: utf-8 -*-
r"""Integra o RESTO do Cap. 3 do *Deuses de Arton* (Deuses Menores + Antigos + Artefatos)
ao índice FAISS. FECHA o Capítulo 3.

`fonte="deuses-arton"`, `capitulo="deuses-menores"`. Chunks:
  - 5 Antigos Deuses (tipo="deus_antigo")
  - 6 Artefatos Divinos (tipo="artefato")
  - 3 Deuses Menores nomeados (tipo="deus_menor")
  - 16 Dádivas de Deuses Menores (tipo="dadiva_divina")
  - 1 overview mecânico dos Deuses Menores (tipo="regra")
  - 1 chunk de Desafios Divinos (tipo="regra")
  - 1 lista

Idempotência ESTREITA por fonte+capítulo. Uso: python integrar_deuses_menores.py
"""
import json, re, shutil, time
from collections import Counter
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import fontes

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
FONTE_ID = "deuses-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "deuses-menores"
SEC = "Deuses de Arton > Capítulo 3: Deuses e Avatares"
IN = BASE / "dados" / "deuses_menores.json"


def bc(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de(d):
    out = []
    for a in d["antigos_deuses"]:
        texto = f"Antigo Deus: {a['nome']} ({LIVRO}, Cap. 3). Um dos deuses mortos/antigos de Arton.\n{a['corpo']}"
        out.append(bc(f"{a['nome']} (Antigo Deus)", f"Antigos Deuses > {a['nome']}", 240, texto,
                      tipo="deus_antigo", nome=a["nome"], deus=a["nome"]))
    for a in d["artefatos_divinos"]:
        texto = f"Artefato Divino: {a['nome']} ({LIVRO}, Cap. 3).\n{a['corpo']}"
        out.append(bc(f"{a['nome']} (Artefato Divino)", f"Artefatos Divinos > {a['nome']}", 248, texto,
                      tipo="artefato", nome=a["nome"]))
    for m in d["deuses_menores_nomeados"]:
        texto = f"Deus Menor: {m['nome']} ({LIVRO}, Cap. 3). Deus menor nomeado de Arton.\n{m['corpo']}"
        out.append(bc(f"{m['nome']} (Deus Menor)", f"Deuses Menores > {m['nome']}", 233, texto,
                      tipo="deus_menor", nome=m["nome"], deus=m["nome"]))
    for dv in d["dadivas"]:
        texto = (f"Dádiva de Deus Menor: {dv['nome']} ({LIVRO}, Cap. 3). Habilidade divina "
                 f"disponível a um personagem que seja um deus menor.\n{dv['efeito']}")
        out.append(bc(f"Dádiva: {dv['nome']}", f"Deuses Menores > Dádivas > {dv['nome']}", 236, texto,
                      tipo="dadiva_divina", nome=dv["nome"]))
    if d.get("overview_menores"):
        texto = (f"Deuses Menores de Arton — regras ({LIVRO}, Cap. 3): como funcionam os deuses "
                 f"menores (naturezas, status divino, devotos, jogando como um deus menor).\n"
                 f"{d['overview_menores']}")
        out.append(bc("Deuses Menores (regras e naturezas)", "Deuses Menores > Visão Geral", 230, texto,
                      tipo="regra", subtipo="deuses_menores"))
    if d.get("desafios_divinos"):
        texto = f"Desafios Divinos ({LIVRO}, Cap. 3): tabela de complicações de ser um deus menor.\n{d['desafios_divinos']}"
        out.append(bc("Desafios Divinos", "Deuses Menores > Desafios Divinos", 239, texto,
                      tipo="regra", subtipo="desafios_divinos"))

    nomes_all = ([a["nome"] for a in d["antigos_deuses"]] + [a["nome"] for a in d["artefatos_divinos"]] +
                 [m["nome"] for m in d["deuses_menores_nomeados"]])
    out.append(bc(f"Lista de Deuses Menores, Antigos e Artefatos ({LIVRO})", "Lista", 230,
                  f"Deuses Menores, Antigos Deuses e Artefatos Divinos de {LIVRO} (Cap. 3): "
                  f"{', '.join(nomes_all)}. Dádivas: {', '.join(x['nome'] for x in d['dadivas'])}.",
                  tipo="deus_lista"))

    resumo = dict(antigos=len(d["antigos_deuses"]), artefatos=len(d["artefatos_divinos"]),
                  menores=len(d["deuses_menores_nomeados"]), dadivas=len(d["dadivas"]),
                  total_chunks=len(out))
    return out, resumo


def eh_cap(c):
    return c.get("fonte") == FONTE_ID and c.get("capitulo") == CAP


def integrar():
    t0 = time.time()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = INDEX_DIR / f"backup-{ts}"
    dados = json.loads(IN.read_text(encoding="utf-8"))

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
        print(f"      Removendo {rem} chunks deuses-menores anteriores (idempotência estreita)")

    novos, resumo = chunks_de(dados)
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
    meta["deuses_cap3_menores_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
