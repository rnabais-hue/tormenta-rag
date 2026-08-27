# -*- coding: utf-8 -*-
r"""Integra as CLASSES DIVINAS do *Deuses de Arton* (Cap. 1) ao FAISS — 1º recorte do 4º livro.

Variantes de classe por deus (Sacerdote/Druida/Paladino de X, 36) + a nova classe **Frade**.
`fonte="deuses-arton"` (estreia no índice), `capitulo="classes-divinas"` (idempotência própria).

Uso: python integrar_classes_divinas_deuses.py
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
CAP = "classes-divinas"
SEC = "Deuses de Arton > Capítulo 1: Campeões dos Deuses"
D = BASE / "dados"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de():
    out = []
    dv = json.loads((D / "devotos_deuses.json").read_text(encoding="utf-8"))
    fr = json.loads((D / "frade_deuses.json").read_text(encoding="utf-8"))

    # variantes de classe divina (1 chunk cada)
    for v in dv["variantes"]:
        habs = "\n".join(f"{h['nome']}: {h['efeito']}" for h in v["habilidades"])
        texto = (f"Variante de classe divina: {v['nome']} — {LIVRO}, pág. {v['pagina']}. "
                 f"É a classe {v['classe']} devotada a {v['deus']}, com traços próprios do culto.\n{habs}")
        out.append(base_chunk(v["nome"], f"{v['classe']}s > {v['nome']}", v["pagina"], texto,
                              tipo="devoto_variante", classe=v["classe"], deus=v["deus"], nome=v["nome"]))
    out.append(base_chunk("Variantes de Classe Divina (lista)", "Variantes > Lista", dv["pagina"],
                          f"As {dv['total']} variantes de classe divina de {LIVRO} (Cap. 1): "
                          + "; ".join(f"{cl} de {', '.join(v['deus'] for v in dv['variantes'] if v['classe']==cl)}"
                                      for cl in ("Sacerdote", "Druida", "Paladino")) + ".",
                          tipo="devoto_variante_lista"))

    # Frade — visão geral + 1 chunk por habilidade
    car = fr["caracteristicas"]
    vg = (f"Classe: Frade (nova classe de {LIVRO}, Cap. 1, pág. {fr['pagina']}). {fr['resumo']}\n"
          f"Pontos de Vida: {car['pv']}\nPontos de Mana: {car['pm']}\n"
          f"Perícias: {car['pericias']}\nProficiências: {car['proficiencias']}")
    out.append(base_chunk("Classe: Frade (visão geral)", "Frade > Visão Geral", fr["pagina"], vg,
                          tipo="classe", subtipo="visao_geral", nome="Frade", classe="Frade"))
    for h in fr["habilidades"]:
        texto = f"Habilidade da classe Frade: {h['nome']} ({LIVRO}, pág. {fr['pagina']}).\n{h['efeito']}"
        out.append(base_chunk(f"Frade: {h['nome']}", f"Frade > {h['nome']}", fr["pagina"], texto,
                              tipo="classe", subtipo="habilidade", nome=h["nome"], classe="Frade"))

    resumo = dict(variantes=dv["total"], por_classe=dv["por_classe"],
                  frade_habilidades=len(fr["habilidades"]), total_chunks=len(out))
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
        print(f"      Removendo {rem} chunks classes-divinas anteriores (idempotência estreita)")

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
    meta["deuses_classes_divinas_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
