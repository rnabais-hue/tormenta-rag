# -*- coding: utf-8 -*-
r"""
Integra as raças ESTRUTURADAS (dados/racas.json) ao índice FAISS de consulta.

O que faz:
  1. Faz backup de index\ (tormenta.faiss, chunks.jsonl, meta.json).
  2. Remove os chunks ANTIGOS de raça (texto corrido — seção "...> Raças > Nome"),
     mantendo o chunk de introdução ("...> Raças", regra geral de modificadores).
  3. Serializa cada raça de dados/racas.json em um chunk 'texto_busca' (que serve
     tanto ao embedding quanto ao contexto do LLM) + metadados estruturados.
  4. Reconstrói o índice SEM reembutir os outros chunks (o FAISS guarda os vetores;
     só as ~17 raças novas são embutidas) e sobrescreve index\.

Idempotente: rodar de novo remove os chunks de raça (inclusive os estruturados,
cuja seção também casa "> Raças >") e recria — não duplica.

Uso:  python integrar_racas.py
Depois a consulta (perguntar.py / interface.py) já usa as raças estruturadas.
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
RACAS_JSON = BASE / "dados" / "racas.json"
ATTRS = ["Força", "Destreza", "Constituição", "Inteligência", "Sabedoria", "Carisma"]


def sinal(n):
    return f"+{n}" if n > 0 else str(n)


def verbalizar_mods(r):
    if r.get("modificadores_variantes"):
        return "; ".join(
            f"{lbl}: " + ", ".join(f"{k} {sinal(v)}" for k, v in d.items())
            for lbl, d in r["modificadores_variantes"].items()
        )
    m = r["modificadores"]
    partes = []
    if m.get("_flexivel"):
        partes.append(m["_flexivel"])
    partes += [f"{k} {sinal(v)}" for k, v in m.items() if k != "_flexivel"]
    return ", ".join(partes) or "nenhum modificador fixo"


def texto_busca(r):
    """Serialização canônica: boa para o embedding E legível para o LLM."""
    linhas = [f"Raça: {r['nome']} (Tormenta20, pág. {r['pagina']})."]
    linhas.append(f"Modificadores de atributo: {verbalizar_mods(r)}.")
    if r.get("resumo"):
        linhas.append(r["resumo"])
    linhas.append("Habilidades de raça:")
    for h in r["habilidades"]:
        linhas.append(f"- {h['nome']}: {h['efeito']}")
    return "\n".join(linhas)


def eh_raca_especifica(chunk):
    """Chunk antigo de uma raça específica (a substituir). O de introdução
    ('...> Raças', sem '>' depois) é preservado."""
    return "Raças >" in chunk.get("secao", "")


def main():
    if not RACAS_JSON.exists():
        raise SystemExit(f"Não achei {RACAS_JSON}. Rode extrair_racas.py antes.")
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado em index\\. Rode ingestao.py antes.")

    # 1) backup
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = INDEX_DIR / f"backup-{stamp}"
    bkp.mkdir(parents=True)
    for nome in ("tormenta.faiss", "chunks.jsonl", "meta.json"):
        shutil.copy2(INDEX_DIR / nome, bkp / nome)
    print(f"[1/5] Backup do índice em {bkp.name}\\")

    # 2) carrega índice + chunks e reconstrói os vetores existentes
    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    chunks = [json.loads(l) for l in
              (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert index.ntotal == len(chunks), "índice e chunks.jsonl desalinhados!"
    dim = meta["dim"]
    vetores = index.reconstruct_n(0, index.ntotal)  # (N, dim) — sem reembutir
    print(f"[2/5] Índice atual: {len(chunks)} chunks, dim {dim}")

    # separa: mantém tudo que NÃO é raça específica
    manter = [(c, vetores[i]) for i, c in enumerate(chunks) if not eh_raca_especifica(c)]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos de raça (texto corrido)")

    # 3) monta os chunks estruturados de raça
    racas = json.loads(RACAS_JSON.read_text(encoding="utf-8"))
    novos = []
    for r in racas:
        novos.append({
            "titulo": r["nome"],
            "secao": f"Capítulo 1: Construção de Personagem > Raças > {r['nome']}",
            "pagina": r["pagina"],
            "texto": texto_busca(r),
            "tipo": "raca",
            "fonte": r.get("fonte", "nucleo"),
            "modificadores": r.get("modificadores", {}),
            **({"modificadores_variantes": r["modificadores_variantes"]}
               if r.get("modificadores_variantes") else {}),
        })
    print(f"[3/5] {len(novos)} raças estruturadas serializadas")

    # 4) embute SÓ as raças novas
    print(f"[4/5] Carregando embedder {meta['modelo_embed']} e embutindo raças…")
    t = time.time()
    model = SentenceTransformer(meta["modelo_embed"])
    emb = model.encode([c["texto"] for c in novos], normalize_embeddings=True,
                       batch_size=8).astype("float32")
    print(f"      {len(novos)} vetores em {time.time() - t:.0f}s")

    # 5) remonta índice: vetores mantidos + vetores das raças; reindexa ids
    vecs_manter = np.array([v for _, v in manter], dtype="float32") if manter else np.empty((0, dim), "float32")
    todos_vecs = np.vstack([vecs_manter, emb]).astype("float32")
    todos_chunks = [c for c, _ in manter] + novos
    for i, c in enumerate(todos_chunks):
        c["id"] = i  # id = posição (invariante que a busca assume)

    novo_index = faiss.IndexFlatIP(dim)
    novo_index.add(todos_vecs)
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))
    with open(INDEX_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in todos_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    meta["n_chunks"] = len(todos_chunks)
    meta["racas_estruturadas"] = len(novos)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} racas). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
