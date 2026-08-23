# -*- coding: utf-8 -*-
r"""
Integra um chunk de EVIDÊNCIA DE DEPENDÊNCIA DE ATRIBUTO por classe.

Motivação (discussão de arquitetura): "importância de atributo" por CONTAGEM de
menções é enganosa — mistura combate com flavor e chega a contradizer o livro
(Bucaneiro→Carisma vs Destreza, etc.). O que é FATO auditável são os
PRÉ-REQUISITOS de atributo (Stage B): um poder que exige "Des 2" é uma dependência
mecânica real. Este chunk lista, por classe, "o que cada atributo destrava" entre
os PODERES DA CLASSE (poderes gerais são compartilhados por todas as classes → não
enumerados por classe, só citados). Serve ao planejamento de build/min-maxer sem
afirmar importância nem contradizer o atributo principal do livro (que já está no
chunk de visão geral, via integrar_atributo_classe.py).

Cria 1 chunk `tipo=classe, subtipo=evidencia_atributo` por classe (14). Idempotente
(remove os antigos desse subtipo antes). Não toca em poderes nem no resto do índice.

Uso: python integrar_evidencia_atributo.py
"""

import json
import shutil
import time
import collections
from datetime import datetime
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
CLASSES_JSON = BASE / "dados" / "classes.json"
PODERES_CLASSE = BASE / "dados" / "poderes_classe.json"
AB = {"For": "Força", "Des": "Destreza", "Con": "Constituição",
      "Int": "Inteligência", "Sab": "Sabedoria", "Car": "Carisma"}
ORDEM_ATTR = ["Força", "Destreza", "Constituição", "Inteligência", "Sabedoria", "Carisma"]


def gates_por_classe(poderes):
    """{classe: {attr_completo: [(poder, valor)]}} — só pré-req de atributo (Stage B)."""
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for p in poderes:
        for grp in p.get("pre_requisito_estruturado", []):
            for a in grp["ou"]:
                if a.get("tipo") == "atributo":
                    out[p["classe"]][AB.get(a["attr"], a["attr"])].add((p["nome"], a["valor"]))
    return out


def texto_evidencia(classe_nome, ap, gates):
    L = [f"Dependência de atributo dos poderes de {classe_nome} "
         f"(o que cada atributo destrava)."]
    if ap:
        L.append(f"Atributo principal segundo o livro (Tabela 1-3): {ap['texto']}.")
    if gates:
        L.append(f"Poderes de {classe_nome} que exigem um atributo mínimo como "
                 f"pré-requisito:")
        for attr in ORDEM_ATTR:
            if attr in gates:
                itens = sorted(gates[attr])
                lista = ", ".join(f"{nome} ({attr[:3]} {val})" for nome, val in itens)
                L.append(f"- {attr}: {lista}")
    else:
        L.append(f"Nenhum poder da classe {classe_nome} exige um atributo mínimo — "
                 f"seus pré-requisitos são de nível ou de outros poderes.")
    L.append("Além destes, os poderes gerais (acessíveis a qualquer classe) ampliam as "
             "opções: os de combate exigem sobretudo Força ou Destreza; os de destino "
             "cobrem todos os atributos.")
    L.append("Nota: isto lista dependências MECÂNICAS reais (pré-requisitos), não uma "
             "medida de 'importância'. A importância de um atributo também vem das "
             "habilidades de classe e do estilo de jogo escolhido.")
    return "\n".join(L)


def main():
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py antes.")
    classes = json.loads(CLASSES_JSON.read_text(encoding="utf-8"))
    poderes = json.loads(PODERES_CLASSE.read_text(encoding="utf-8"))
    if not any("pre_requisito_estruturado" in p for p in poderes):
        raise SystemExit("poderes_classe.json sem pre_requisito_estruturado. Rode estruturar_prereqs.py antes.")

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
    vetores = index.reconstruct_n(0, index.ntotal).astype("float32")
    print(f"[2/5] Indice: {len(chunks)} chunks, dim {dim}")

    # remove chunks antigos deste subtipo (idempotência)
    manter = [(c, vetores[i]) for i, c in enumerate(chunks)
              if c.get("subtipo") != "evidencia_atributo"]
    removidos = len(chunks) - len(manter)

    gates = gates_por_classe(poderes)
    novos = []
    com_gate = 0
    for c in classes:
        g = gates.get(c["nome"], {})
        if g:
            com_gate += 1
        sec = f"Capítulo 1: Construção de Personagem > Classes > {c['nome']} > Dependência de atributo"
        novos.append({
            "titulo": f"{c['nome']}: dependência de atributo",
            "secao": sec, "pagina": c["pagina"],
            "texto": texto_evidencia(c["nome"], c.get("atributo_principal"), g),
            "tipo": "classe", "subtipo": "evidencia_atributo", "classe": c["nome"],
            "gates_atributo": {a: sorted(list(v)) for a, v in g.items()},
        })
    print(f"[3/5] {len(novos)} chunks de evidencia ({com_gate} com gate, "
          f"{len(novos) - com_gate} sem) | removidos {removidos} antigos")

    model = SentenceTransformer(meta["modelo_embed"])
    t = time.time()
    emb = model.encode([c["texto"] for c in novos], normalize_embeddings=True,
                       batch_size=8, show_progress_bar=False).astype("float32")
    print(f"[4/5] {len(novos)} vetores em {time.time() - t:.0f}s")

    vecs_manter = np.array([v for _, v in manter], dtype="float32")
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
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] OK - indice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(+{len(novos)} evidencia, -{removidos} antigos). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
