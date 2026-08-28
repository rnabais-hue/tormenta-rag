# -*- coding: utf-8 -*-
r"""Integra as RAÇAS JOGÁVEIS de *Ameaças de Arton* (Apêndice A + caixas) ao índice FAISS.

`fonte="ameacas-arton"`, `capitulo="racas"`. 1 chunk fino por raça (modificadores de
atributo + habilidades raciais) + 1 lista. Idempotência ESTREITA por fonte+capítulo —
NÃO toca no bestiário (mesma fonte, `capitulo=None`).

Uso: python integrar_racas_ameacas.py
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
FONTE_ID = "ameacas-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "racas"
SEC = "Ameaças de Arton > Apêndice A: Raças e Parceiros"
IN = BASE / "dados" / "racas_ameacas.json"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunk_raca(r):
    nome = r["nome"]
    mods = r.get("modificadores") or r.get("modificadores_tabela") or ""
    linhas = [f"Raça jogável: {nome} ({LIVRO}, Apêndice A / pág. {r['pagina']}). "
              f"Ameaça do bestiário que pode ser usada como raça de personagem."]
    if mods:
        linhas.append(f"Modificadores de Atributos: {mods}")
    if r.get("modificadores_tabela") and r["modificadores_tabela"] not in mods:
        linhas.append(f"(Tabela A-1: {r['modificadores_tabela']}.)")
    if r.get("habilidades"):
        linhas.append("Habilidades de Raça:")
        for h in r["habilidades"]:
            linhas.append(f"• {h['nome']}: {h['efeito']}")
    return base_chunk(f"{nome} (raça jogável) - Ameaças de Arton", nome, r["pagina"],
                      "\n".join(linhas), tipo="raca", subtipo="ameacas", nome=nome,
                      modificadores=r.get("modificadores_tabela") or mods)


def chunks_de(dados):
    racas = dados["racas"]
    out = [chunk_raca(r) for r in racas]
    nomes = ", ".join(r["nome"] for r in racas)
    out.append(base_chunk(f"Lista de Raças Jogáveis ({LIVRO})", "Lista", 418,
                          f"As {len(racas)} raças jogáveis de {LIVRO} (ameaças que podem ser "
                          f"personagens, Apêndice A / Tabela A-1): {nomes}.",
                          tipo="raca_lista"))
    return out, dict(racas=len(racas), total_chunks=len(out))


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
        print(f"      Removendo {rem} chunks racas anteriores (idempotência estreita)")

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
    meta["ameacas_racas_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
