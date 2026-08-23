# -*- coding: utf-8 -*-
r"""
Integra os PODERES DE CLASSE estruturados (dados/poderes_classe.json) ao índice
FAISS — Stage A da família "poderes" (ver README §11).

Granularidade FINA: cada poder vira 1 chunk (nome + efeito + pré-requisito COMO
TEXTO). Isso substitui os 14 chunks GROSSOS "Poder de <Classe>" (que integrar_
classes.py criara como habilidade única, uma lista enorme) por ~296 chunks
precisos — para "o que faz o poder Arcano de Batalha", "poderes com pré-requisito
de Bruxo", etc.

Mantém a capacidade de LISTAR: gera também 1 chunk-lista LEVE por classe (só os
NOMES dos poderes) para "quais poderes o Arcanista pode escolher". Curto, não
estoura o contexto de 4096 do Ollama.

Metadados por chunk de poder (insumo dos Stages B/C/D): tipo="poder",
categoria="classe", classe, nome, pre_requisito (texto), pagina.

Reconstrói o índice SEM reembutir os outros chunks (só as unidades de poder são
embutidas). Idempotente: rodar de novo remove os chunks de poder anteriores antes
de reinserir (não duplica). Uso: python integrar_poderes_classe.py
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
PODERES_JSON = BASE / "dados" / "poderes_classe.json"


def nome_habilidade(chunk):
    """'Arcanista: Poder de Arcanista' -> 'Poder de Arcanista'."""
    return chunk.get("titulo", "").split(": ", 1)[-1]


def eh_poder_de_x_antigo(chunk):
    """Chunk grosso 'Poder de <Classe>' criado por integrar_classes.py."""
    return (chunk.get("tipo") == "classe"
            and chunk.get("subtipo") == "habilidade"
            and nome_habilidade(chunk).lower().startswith("poder de"))


def eh_poder_estruturado(chunk):
    """Chunk de poder de CLASSE já inserido por ESTE script (p/ idempotência).
    IMPORTANTE: casa só categoria=="classe" — senão apaga os poderes GERAIS
    (combate/destino/magia/concedido/tormenta), que também são tipo=="poder"."""
    return chunk.get("tipo") == "poder" and chunk.get("categoria") == "classe"


def chunks_de_poderes(poderes):
    """Gera os chunks: 1 por poder + 1 chunk-lista por classe."""
    saida = []
    por_classe = {}
    for p in poderes:
        classe, pg = p["classe"], p["pagina"]
        por_classe.setdefault(classe, {"nomes": [], "pagina": pg})["nomes"].append(p["nome"])
        base_sec = (f"Capítulo 1: Construção de Personagem > Classes > {classe} "
                    f"> Poderes de {classe}")
        linhas = [f"Poder de {classe}: {p['nome']} (Tormenta20, pág. {pg}).", p["efeito"]]
        if p.get("pre_requisito"):
            linhas.append(f"Pré-requisito: {p['pre_requisito']}.")
        if p.get("opcoes"):                      # quadro de opção (Familiar, Totem…)
            linhas.append("Opções:")
            for o in p["opcoes"]:
                linhas.append(f"- {o['nome']}: {o['efeito']}")
        chunk = {
            "titulo": f"{classe}: {p['nome']}",
            "secao": f"{base_sec} > {p['nome']}",
            "pagina": pg,
            "texto": "\n".join(linhas),
            "tipo": "poder", "categoria": "classe", "subtipo": "poder",
            "classe": classe, "nome": p["nome"],
            "pre_requisito": p.get("pre_requisito"),
        }
        if p.get("opcoes"):
            chunk["opcoes"] = p["opcoes"]
        saida.append(chunk)

    # chunk-lista leve por classe (preserva "quais poderes o X pode escolher")
    for classe, d in por_classe.items():
        nomes = d["nomes"]
        texto = (f"Poderes de classe do {classe} (Tormenta20, pág. {d['pagina']}). "
                 f"No 2º nível, e a cada nível seguinte, o {classe} escolhe um "
                 f"destes {len(nomes)} poderes: " + ", ".join(nomes) + ".")
        saida.append({
            "titulo": f"{classe}: lista de poderes de classe",
            "secao": (f"Capítulo 1: Construção de Personagem > Classes > {classe} "
                      f"> Poderes de {classe}"),
            "pagina": d["pagina"],
            "texto": texto,
            "tipo": "poder", "categoria": "classe", "subtipo": "lista",
            "classe": classe,
        })
    return saida


def main():
    if not PODERES_JSON.exists():
        raise SystemExit(f"Não achei {PODERES_JSON}. Rode extrair_poderes_classe.py antes.")
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
              if not eh_poder_de_x_antigo(c) and not eh_poder_estruturado(c)]
    removidos = len(chunks) - len(manter)
    print(f"      removendo {removidos} chunks antigos (grosso 'Poder de X' + poderes de re-run)")

    poderes = json.loads(PODERES_JSON.read_text(encoding="utf-8"))
    novos = chunks_de_poderes(poderes)
    n_lista = sum(1 for c in novos if c["subtipo"] == "lista")
    print(f"[3/5] {len(poderes)} poderes -> {len(novos)} chunks estruturados "
          f"({len(novos) - n_lista} poderes + {n_lista} listas por classe)")

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
    meta["poderes_classe_estruturados"] = len(poderes)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} de poder). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
