# -*- coding: utf-8 -*-
r"""
Integra as classes ESTRUTURADAS (dados/classes.json) ao índice FAISS.

Granularidade (diferente das raças — classes são grandes):
  - 1 chunk de VISÃO GERAL por classe (resumo + características PV/PM/Perícias/
    Proficiências) — para "me fale do Paladino", "proficiências do Guerreiro".
  - 1 chunk por HABILIDADE (cada um se identifica pela classe) — para "o que faz
    Golpe Divino", "Protótipo do Inventor". Chunks pequenos = busca precisa e
    sem estourar o contexto de 4096 do Ollama.
  As habilidades "Poder de X" ficam como um chunk único (lista de poderes de
  classe); granularidade por poder individual é da futura família "poderes".

Substitui os chunks antigos de classe (texto corrido, seção "...> Classes > Nome")
mantendo a introdução "...> Classes". Reconstrói o índice SEM reembutir os outros
chunks (só as ~111 unidades de classe são embutidas).

Idempotente. Uso: python integrar_classes.py
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
CLASSES_JSON = BASE / "dados" / "classes.json"
ORDEM = ["Pontos de Vida", "Pontos de Mana", "Perícias", "Proficiências"]


def chunks_de_classe(c):
    """Gera os chunks (visão geral + 1 por habilidade) de uma classe."""
    sec = f"Capítulo 1: Construção de Personagem > Classes > {c['nome']}"
    pg = c["pagina"]
    saida = []

    # visão geral
    linhas = [f"Classe: {c['nome']} (Tormenta20, pág. {pg})."]
    if c.get("resumo"):
        linhas.append(c["resumo"])
    linhas.append("Características de classe:")
    chaves = [k for k in ORDEM if k in c["caracteristicas"]] + \
             [k for k in c["caracteristicas"] if k not in ORDEM]
    for k in chaves:
        linhas.append(f"- {k}: {c['caracteristicas'][k]}")
    saida.append({
        "titulo": c["nome"], "secao": sec, "pagina": pg,
        "texto": "\n".join(linhas),
        "tipo": "classe", "subtipo": "visao_geral", "classe": c["nome"],
        "caracteristicas": c["caracteristicas"],
    })

    # uma por habilidade
    for h in c["habilidades"]:
        saida.append({
            "titulo": f"{c['nome']}: {h['nome']}",
            "secao": f"{sec} > {h['nome']}", "pagina": pg,
            "texto": f"Classe {c['nome']} — {h['nome']} (pág. {pg}).\n{h['efeito']}",
            "tipo": "classe", "subtipo": "habilidade", "classe": c["nome"],
        })
    return saida


def eh_classe_especifica(chunk):
    return "Classes >" in chunk.get("secao", "")


def main():
    if not CLASSES_JSON.exists():
        raise SystemExit(f"Não achei {CLASSES_JSON}. Rode extrair_classes.py antes.")
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

    manter = [(c, vetores[i]) for i, c in enumerate(chunks) if not eh_classe_especifica(c)]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos de classe (texto corrido)")

    classes = json.loads(CLASSES_JSON.read_text(encoding="utf-8"))
    novos = []
    for c in classes:
        novos.extend(chunks_de_classe(c))
    print(f"[3/5] {len(classes)} classes -> {len(novos)} chunks estruturados "
          f"(14 visao geral + {len(novos) - len(classes)} habilidades)")

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
    meta["classes_estruturadas"] = len(classes)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} de classe). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
