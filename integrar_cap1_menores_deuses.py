# -*- coding: utf-8 -*-
r"""Integra os MENORES do Cap. 1 do *Deuses de Arton* — FECHA o capítulo.

Autoridade Eclesiástica (20), Outros Devotos (20), Linhagem Abençoada (1), Heranças do
Suraggel (22). `fonte="deuses-arton"`, `capitulo="cap1-menores"` (idempotência própria).

Uso: python integrar_cap1_menores_deuses.py
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
FONTE_ID = "deuses-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "cap1-menores"
SEC = "Deuses de Arton > Capítulo 1: Campeões dos Deuses"
D = BASE / "dados"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de():
    d = json.loads((D / "devotos_menores_deuses.json").read_text(encoding="utf-8"))
    out = []

    for o in d["outros_devotos"]:
        texto = (f"Devotos permitidos de {o['deus']} ({LIVRO}, Cap. 1, pág. {o['pagina']}): quais raças "
                 f"e classes podem cultuar {o['deus']}.\nRaças: {o['racas']}.\nClasses: {o['classes']}.")
        out.append(base_chunk(f"Devotos de {o['deus']} (raças e classes)", f"Outros Devotos > {o['deus']}",
                              o["pagina"], texto, tipo="devotos_permitidos", deus=o["deus"]))
    for a in d["autoridade_eclesiastica"]:
        texto = (f"Autoridade Eclesiástica de {a['deus']} ({LIVRO}, Cap. 1, pág. {a['pagina']}): o título/"
                 f"benefício de liderança do clero de {a['deus']}.\n{a['texto']}")
        out.append(base_chunk(f"Autoridade Eclesiástica: {a['deus']}", f"Autoridade Eclesiástica > {a['deus']}",
                              a["pagina"], texto, tipo="autoridade_eclesiastica", deus=a["deus"]))
    ab = d["linhagem_abencoada"]
    habs = "\n".join(f"{h['nome']}: {h['efeito']}" for h in ab["habilidades"])
    out.append(base_chunk("Linhagem Abençoada", "Nova Linhagem > Abençoada", ab["pagina"],
                          f"Nova linhagem de {LIVRO} (Cap. 1): {ab['nome']} — indivíduos com sangue divino. "
                          f"{ab['resumo']}\n{habs}", tipo="linhagem", nome="Linhagem Abençoada"))
    for h in d["heranca_suraggel"]:
        texto = f"Herança do Suraggel: {h['nome']} ({LIVRO}, Cap. 1, pág. {h['pagina']}).\n{h['efeito']}"
        out.append(base_chunk(f"Suraggel: {h['nome']}", f"Suraggel Variantes > {h['nome']}",
                              h["pagina"], texto, tipo="heranca_suraggel", nome=h["nome"]))
    out.append(base_chunk("Heranças do Suraggel (lista)", "Suraggel Variantes > Lista", 38,
                          f"As {len(d['heranca_suraggel'])} heranças do Suraggel de {LIVRO} (Cap. 1): "
                          f"{', '.join(h['nome'] for h in d['heranca_suraggel'])}.",
                          tipo="heranca_suraggel_lista"))

    resumo = dict(outros_devotos=len(d["outros_devotos"]), autoridade=len(d["autoridade_eclesiastica"]),
                  abencoada_habs=len(ab["habilidades"]), heranca_suraggel=len(d["heranca_suraggel"]),
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
        print(f"      Removendo {rem} chunks cap1-menores anteriores (idempotência estreita)")

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
    meta["deuses_cap1_menores_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
