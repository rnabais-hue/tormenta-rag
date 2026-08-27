# -*- coding: utf-8 -*-
r"""Integra o ARSENAL MENOR (Cap. 3 de *Heróis de Arton*) ao FAISS — fecha o capítulo.

Novas Melhorias, Capangas, Veículos e Bases (módulos + Cômodos + Mobílias).
`fonte="herois-arton"`, `capitulo="arsenal-menor"` (idempotência estreita PRÓPRIA — não
toca em `arsenal`/`arsenal-magico` nem no resto).

Uso: python integrar_arsenal_menor_herois.py
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
FONTE_ID = "herois-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "arsenal-menor"
SEC = "Heróis de Arton > Capítulo 3: Arsenal dos Heróis"
D = BASE / "dados"
TIPO_ROT = {"melhoria_item": "Nova Melhoria de item", "capanga": "Capanga (grupo)",
            "veiculo": "Veículo", "comodo_base": "Cômodo de Base"}


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de():
    out = []
    am = json.loads((D / "arsenal_menor_herois.json").read_text(encoding="utf-8"))

    for e in am["entidades"]:
        rot = TIPO_ROT.get(e["tipo"], e["tipo"])
        texto = f"{rot} ({LIVRO}, Cap. 3, pág. {e['pagina']}): {e['nome']}.\n{e['descricao']}"
        out.append(base_chunk(f"{rot}: {e['nome']}", f"{e['categoria']} > {e['nome']}", e["pagina"],
                              texto, tipo=e["tipo"], categoria=e["categoria"], nome=e["nome"]))
    for m in am["modulos"]:
        texto = f"Arsenal (regra) — {m['nome']} ({LIVRO}, Cap. 3, pág. {m['pagina']}).\n{m['efeito']}"
        out.append(base_chunk(f"Arsenal: {m['nome']}", f"Regras > {m['nome']}", m["pagina"],
                              texto, tipo="regra_opcional", subtipo="arsenal_menor", nome=m["nome"]))
    if am.get("mobilias"):
        corpo = "\n".join(f"{mb['nome']}: {mb['beneficio']}" for mb in am["mobilias"])
        out.append(base_chunk("Mobílias de Base (Tabela 3-8)", "Bases > Mobílias", 252,
                              f"Mobílias que podem ser adicionadas a cômodos de uma base ({LIVRO}, Cap. 3). "
                              f"São {len(am['mobilias'])} mobílias (Mobília: benefício).\n{corpo}",
                              tipo="mobilia_lista", nome="Mobílias"))
    # listas de recuperação por tipo
    from collections import defaultdict
    porcat = defaultdict(list)
    for e in am["entidades"]:
        porcat[e["categoria"]].append(e["nome"])
    for cat, nomes in porcat.items():
        out.append(base_chunk(f"Lista: {cat}", f"{cat} > Lista", am["pagina"],
                              f"{cat} de {LIVRO} (Cap. 3): {', '.join(nomes)}.",
                              tipo="arsenal_menor_lista", categoria=cat))

    resumo = dict(por_tipo=am["por_tipo"], modulos=am["total_modulos"], mobilias=am["total_mobilias"],
                  total_chunks=len(out))
    return out, resumo


def eh_arsenal_menor(c):
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
        if eh_arsenal_menor(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks arsenal-menor anteriores (idempotência estreita)")

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
    meta["herois_cap3_arsenal_menor_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
