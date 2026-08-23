# -*- coding: utf-8 -*-
r"""
Integra o início do Capítulo 1 ao índice FAISS:
  - 6 chunks de ATRIBUTO (dados/atributos.json) — 1 por atributo, com
    `pericias_governadas` no texto e metadados.
  - 2 chunks PROCEDURAIS (dados/criacao_personagem.json):
      * "Passos da Construção de Personagem" (os 9 passos)
      * "Definindo seus atributos" (Pontos/Rolagens + tabela de custo) — corrige a
        falha do §10 (a "criação por pontos" ficava diluída no rank 20).

Substitui os chunks de texto corrido das seções "Conceito de Personagem" e
"Atributos Básicos" (pgs 22–23); mantém o título do capítulo (pg20). Reconstrói o
índice SEM reembutir o resto. Idempotente. Uso: python integrar_atributos.py
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
ATR_JSON = BASE / "dados" / "atributos.json"
CRI_JSON = BASE / "dados" / "criacao_personagem.json"
SEC = "Capítulo 1: Construção de Personagem"
TIPOS_NOVOS = ("atributo", "regra_criacao")


def eh_texto_corrido(c):
    if c.get("tipo"):
        return False
    seg = c.get("secao", "").split(" > ")[-1]
    return seg.endswith("Atributos Básicos") or ("Conceito" in seg and "Personagem" in seg)


def chunk_atributo(a):
    linhas = [f"Atributo: {a['nome']} ({a['abrev']}) (Tormenta20, pág. {a['pagina']}).",
              a["descricao"]]
    if a.get("pericias_governadas"):
        linhas.append(f"Perícias governadas por {a['nome']}: "
                      f"{', '.join(a['pericias_governadas'])}.")
    return {
        "titulo": a["nome"], "secao": f"{SEC} > Atributos Básicos > {a['nome']}",
        "pagina": a["pagina"], "texto": "\n".join(linhas),
        "tipo": "atributo", "nome": a["nome"], "abrev": a["abrev"],
        "pericias_governadas": a.get("pericias_governadas", []),
    }


def chunk_passos(cri):
    linhas = ["Passos da Construção de Personagem em Tormenta20 (pág. 22). "
              "Para criar um personagem, siga estes passos:"]
    for p in cri["passos"]:
        linhas.append(f"{p['n']}. {p['titulo']}. {p['descricao']}")
    return {
        "titulo": "Passos da Construção de Personagem",
        "secao": f"{SEC} > Conceito de Personagem > Passos", "pagina": 22,
        "texto": "\n".join(linhas),
        "tipo": "regra_criacao", "subtipo": "passos",
    }


def chunk_definindo(cri):
    linhas = ["Definindo seus atributos na criação de personagem (Tormenta20, pág. 23). "
              "Há duas maneiras: por pontos ou por rolagens.",
              cri["definindo_atributos"]]
    if cri.get("tabela_custo"):
        partes = [f"atributo {r.get('atributo','?')} custa {r.get('custo','?')} "
                  f"(rolagem 4d6: {r.get('rolagem','?')})" for r in cri["tabela_custo"]]
        linhas.append("Tabela de custo/rolagem por valor de atributo: " + "; ".join(partes) + ".")
    return {
        "titulo": "Definindo seus atributos (pontos e rolagens)",
        "secao": f"{SEC} > Atributos Básicos > Definindo seus atributos", "pagina": 23,
        "texto": "\n".join(linhas),
        "tipo": "regra_criacao", "subtipo": "definindo_atributos",
    }


def main():
    for p in (ATR_JSON, CRI_JSON):
        if not p.exists():
            raise SystemExit(f"Não achei {p}. Rode extrair_atributos.py antes.")
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
              if not eh_texto_corrido(c) and c.get("tipo") not in TIPOS_NOVOS]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos (Conceito + Atributos Básicos + re-run)")

    atributos = json.loads(ATR_JSON.read_text(encoding="utf-8"))
    cri = json.loads(CRI_JSON.read_text(encoding="utf-8"))
    novos = [chunk_atributo(a) for a in atributos] + [chunk_passos(cri), chunk_definindo(cri)]
    print(f"[3/5] {len(atributos)} atributos + 2 procedurais -> {len(novos)} chunks")

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
    meta["atributos_estruturados"] = len(atributos)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} novos). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
