# -*- coding: utf-8 -*-
r"""Integra as DISTINÇÕES (Cap. 2) de *Heróis de Arton* ao índice FAISS.

Escopo SEGURO: 36 distinções (overview: conceito + admissão + marca + lista de
poderes) + os poderes com EFEITO LIMPO (efeito >= MIN_EF chars). Os poderes de
efeito fino (grid compacto) NÃO viram chunk próprio — ficam no BACKLOG (chunk
`tipo="pendencia"`), mas continuam nomeados no overview da distinção.

Aditivo, `fonte="herois-arton"`, `capitulo="distincoes"`. IDEMPOTÊNCIA ESTREITA:
remove só chunks com capitulo=="distincoes" (NÃO toca no Cap 1, no Arsenal nem no
núcleo/ameacas). Recomputa meta["fontes"] do zero. Embute só os vetores novos.

Uso: python integrar_distincoes_herois.py
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
FONTE_ID = "herois-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "distincoes"
SEC = "Heróis de Arton > Capítulo 2: Distinções"
IN = BASE / "dados" / "distincoes_herois.json"
MIN_EF = 40   # limiar de efeito "limpo"


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de(dados):
    dists = dados["distincoes"]
    out = []
    finos = []   # (distincao, poder) descartados p/ backlog

    for d in dists:
        nome, pag = d["nome"], d["pagina"]
        nomes_pod = [p["nome"] for p in d["poderes"]]
        # --- overview ---
        linhas = [f"Distinção: {nome} ({LIVRO}, Cap. 2, pág. {pag}). Distinção nova de Heróis de Arton."]
        if d.get("conceito"):
            linhas.append(f"Conceito: {d['conceito']}")
        if d.get("admissao"):
            linhas.append(f"Admissão (requisito): {d['admissao']}")
        m = d.get("marca", {})
        if m.get("nome"):
            linhas.append(f"Marca da Distinção — {m['nome']}: {m.get('efeito','')}")
        if nomes_pod:
            linhas.append(f"Poderes da distinção: {', '.join(nomes_pod)}.")
        out.append(base_chunk(nome, f"{nome} > Visão Geral", pag, "\n".join(linhas),
                              tipo="distincao", subtipo="visao_geral", nome=nome,
                              distincao=nome, marca=m.get("nome"),
                              poderes=nomes_pod))
        # --- poderes limpos ---
        for p in d["poderes"]:
            if len(p.get("efeito", "")) < MIN_EF:
                finos.append((nome, p["nome"]))
                continue
            tag = f" ({p['tag']})" if p.get("tag") else ""
            texto = (f"Poder da distinção {nome}: {p['nome']}{tag} ({LIVRO}, pág. {pag}).\n"
                     f"{p['efeito']}")
            out.append(base_chunk(f"{nome}: {p['nome']}", f"{nome} > Poderes > {p['nome']}",
                                  pag, texto, tipo="distincao_poder", nome=p["nome"],
                                  distincao=nome, tag=p.get("tag")))

    # --- lista geral das distinções ---
    todos = ", ".join(d["nome"] for d in dists)
    out.append(base_chunk(f"Lista das Distinções ({LIVRO})", "Lista", dists[0]["pagina"],
                          f"As {len(dists)} Distinções de {LIVRO} (Cap. 2): {todos}.",
                          tipo="distincao_lista"))

    # --- backlog: poderes de efeito fino não integrados ---
    lst = "; ".join(f"{dist} → {pod}" for dist, pod in finos)
    pend = (
        f"Backlog do Cap. 2 (Distinções) de {LIVRO}: {len(finos)} poderes de distinção NÃO "
        f"integrados como chunk próprio por efeito não capturado (layout compacto/grid). "
        f"Estão nomeados no overview de cada distinção, mas o texto do efeito precisa de "
        f"refino no extrator. São eles: {lst}."
    )
    out.append(base_chunk(f"Backlog de Distinções ({LIVRO})", "Backlog", dists[0]["pagina"],
                          pend, tipo="pendencia", nome="Backlog de Distinções"))

    resumo = dict(distincoes=len(dists),
                  poderes_integrados=sum(1 for c in out if c["tipo"] == "distincao_poder"),
                  poderes_finos_backlog=len(finos))
    return out, resumo, finos


def eh_distincoes(c):
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
        if eh_distincoes(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks distincoes anteriores (idempotência estreita)")

    novos, resumo, finos = chunks_de(dados)
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
    meta["herois_cap2_distincoes_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Backlog={len(finos)} poderes finos. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
