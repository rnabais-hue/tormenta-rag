# -*- coding: utf-8 -*-
r"""Integra o RESTO do Cap. 1 do *Deuses de Arton* ao FAISS.

Complementa as Classes Divinas (já em `capitulo="classes-divinas"`) com o miolo mecânico
restante: **Magias Divinas** (29), **Novos Poderes Concedidos** (75) e **Equipamentos
Religiosos + Itens Litúrgicos** (110). `fonte="deuses-arton"`, `capitulo="cap1-resto"`.

Uso: python integrar_cap1_resto_deuses.py
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
CAP = "cap1-resto"
SEC = "Deuses de Arton > Capítulo 1: Campeões dos Deuses"
D = BASE / "dados"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de():
    out = []
    mag = json.loads((D / "magias_deuses.json").read_text(encoding="utf-8"))
    pod = json.loads((D / "poderes_concedidos_deuses.json").read_text(encoding="utf-8"))
    itr = json.loads((D / "itens_religiosos_deuses.json").read_text(encoding="utf-8"))

    # --- Magias Divinas ---
    for m in mag["magias"]:
        sb = (f"Execução: {m['execucao']}; Alcance: {m['alcance']}; "
              f"{m['alvo_tipo'] or 'Alvo'}: {m['alvo']}; Duração: {m['duracao']}"
              + (f"; Resistência: {m['resistencia']}" if m["resistencia"] else "") + ".")
        apr = "\n".join(f"{a['custo']}: {a['efeito']}" for a in m["aprimoramentos"])
        tp = m["arcana_divina"].capitalize()
        texto = (f"Magia {m['arcana_divina']} (nova, {LIVRO}, Cap. 1): {m['nome']} — {tp} {m['circulo']}º "
                 f"círculo, escola de {m['escola']}, custo {m['custo_pm']} PM.\n{sb}\n{m['descricao']}"
                 + (f"\nAprimoramentos:\n{apr}" if apr else ""))
        out.append(base_chunk(f"Magia Divina: {m['nome']}", f"Magias Divinas > {m['nome']}", m["pagina"],
                              texto, tipo="magia", nome=m["nome"], circulo=m["circulo"], escola=m["escola"],
                              arcana_divina=m["arcana_divina"]))
    out.append(base_chunk("Lista das Magias Divinas", "Magias Divinas > Lista", mag["pagina"],
                          f"As {mag['total']} magias divinas de {LIVRO} (Cap. 1): "
                          f"{', '.join(m['nome']+' ('+str(m['circulo'])+'º '+m['escola']+')' for m in mag['magias'])}.",
                          tipo="magia_lista"))

    # --- Novos Poderes Concedidos ---
    for p in pod["poderes"]:
        deus = ", ".join(p["deuses"]) if p["deuses"] else "—"
        texto = (f"Poder concedido: {p['nome']} — concedido por {deus} ({LIVRO}, Cap. 1, pág. {p['pagina']}). "
                 f"Poder que um devoto pode receber de seu deus.\n{p['efeito']}")
        out.append(base_chunk(f"Poder Concedido: {p['nome']}", f"Poderes Concedidos > {p['nome']}",
                              p["pagina"], texto, tipo="poder", categoria="concedido", nome=p["nome"],
                              deuses=p["deuses"]))
    # lista por deus
    pordeus = {}
    for p in pod["poderes"]:
        for g in (p["deuses"] or ["—"]):
            pordeus.setdefault(g, []).append(p["nome"])
    lst = "; ".join(f"{g}: {', '.join(ns)}" for g, ns in sorted(pordeus.items()))
    out.append(base_chunk("Novos Poderes Concedidos (por deus)", "Poderes Concedidos > Lista", pod["pagina"],
                          f"Os {pod['total']} novos poderes concedidos de {LIVRO} (Cap. 1), por deus — {lst}.",
                          tipo="poder_lista"))

    # --- Equipamentos Religiosos + Itens Litúrgicos ---
    for i in itr["itens"]:
        rot = "Item litúrgico (mágico)" if i["tipo"] == "item_liturgico" else f"Equipamento religioso ({i['categoria']})"
        texto = f"{rot}: {i['nome']} ({LIVRO}, Cap. 1, pág. {i['pagina']}).\n{i['descricao']}"
        out.append(base_chunk(f"{'Item Litúrgico' if i['tipo']=='item_liturgico' else 'Equip. Religioso'}: {i['nome']}",
                              f"{i['categoria']} > {i['nome']}", i["pagina"], texto,
                              tipo=i["tipo"], categoria=i["categoria"], nome=i["nome"]))
    lit = [i["nome"] for i in itr["itens"] if i["tipo"] == "item_liturgico"]
    eq = [i["nome"] for i in itr["itens"] if i["tipo"] == "equipamento_religioso"]
    out.append(base_chunk("Itens Litúrgicos e Equipamentos Religiosos (lista)", "Itens Religiosos > Lista",
                          itr["pagina"], f"{LIVRO} (Cap. 1). Itens litúrgicos ({len(lit)}): {', '.join(lit)}. "
                          f"Equipamentos religiosos ({len(eq)}): {', '.join(eq)}.",
                          tipo="item_religioso_lista"))

    resumo = dict(magias=mag["total"], poderes_concedidos=pod["total"],
                  itens_religiosos=itr["por_tipo"], total_chunks=len(out))
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
        print(f"      Removendo {rem} chunks cap1-resto anteriores (idempotência estreita)")

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
    meta["deuses_cap1_resto_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
