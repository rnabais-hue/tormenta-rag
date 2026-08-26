# -*- coding: utf-8 -*-
r"""Integra o ARSENAL MÁGICO do Cap. 3 (Heróis de Arton) ao FAISS.

Recorte de alto valor das pendências do Arsenal: **Novas Magias Arcanas** (22), **Artefatos**
(8) e **Novos Itens Mágicos** (202 itens + 5 regras). `fonte="herois-arton"`,
`capitulo="arsenal-magico"` (idempotência estreita PRÓPRIA — não toca no `capitulo="arsenal"`
dos Novos Equipamentos, nem no resto).

Ficam de FORA (sub-backlog, chunk `tipo="pendencia"`): Itens Superiores/Novas Melhorias,
Capangas, Veículos (+5 do catálogo), Bases (adiada).

Uso: python integrar_arsenal_magico_herois.py
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
CAP = "arsenal-magico"
SEC = "Heróis de Arton > Capítulo 3: Arsenal dos Heróis"
D = BASE / "dados"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de():
    out = []
    mag = json.loads((D / "magias_herois.json").read_text(encoding="utf-8"))
    art = json.loads((D / "artefatos_herois.json").read_text(encoding="utf-8"))
    im = json.loads((D / "itens_magicos_herois.json").read_text(encoding="utf-8"))

    # ---------- Novas Magias Arcanas ----------
    for m in mag["magias"]:
        sb = (f"Execução: {m['execucao']}; Alcance: {m['alcance']}; "
              f"{m['alvo_tipo'] or 'Alvo'}: {m['alvo']}; Duração: {m['duracao']}"
              + (f"; Resistência: {m['resistencia']}" if m["resistencia"] else "") + ".")
        apr = "\n".join(f"{a['custo']}: {a['efeito']}" for a in m["aprimoramentos"])
        texto = (f"Magia arcana (nova, {LIVRO}, Cap. 3): {m['nome']} — Arcana {m['circulo']}º círculo, "
                 f"escola de {m['escola']}, custo {m['custo_pm']} PM.\n{sb}\n{m['descricao']}"
                 + (f"\nAprimoramentos:\n{apr}" if apr else ""))
        out.append(base_chunk(f"Magia: {m['nome']}", f"Novas Magias Arcanas > {m['nome']}", m["pagina"],
                              texto, tipo="magia", nome=m["nome"], circulo=m["circulo"],
                              escola=m["escola"], arcana_divina="arcana"))
    out.append(base_chunk("Lista das Novas Magias Arcanas", "Novas Magias Arcanas > Lista", mag["pagina"],
                          f"As {mag['total']} novas magias arcanas de {LIVRO} (Cap. 3): "
                          f"{', '.join(m['nome']+' ('+str(m['circulo'])+'º, '+m['escola']+')' for m in mag['magias'])}.",
                          tipo="magia_lista"))

    # ---------- Artefatos ----------
    for a in art["artefatos"]:
        texto = f"Artefato (lendário, {LIVRO}, Cap. 3): {a['nome']}.\n{a['descricao']}"
        out.append(base_chunk(f"Artefato: {a['nome']}", f"Artefatos > {a['nome']}", a["pagina"],
                              texto, tipo="artefato", nome=a["nome"]))
    out.append(base_chunk("Lista dos Artefatos", "Artefatos > Lista", art["pagina"],
                          f"Os {art['total']} Artefatos de {LIVRO} (Cap. 3): "
                          f"{', '.join(a['nome'] for a in art['artefatos'])}.",
                          tipo="artefato_lista"))

    # ---------- Novos Itens Mágicos ----------
    for i in im["itens"]:
        texto = (f"Item mágico ({i['categoria']}, {LIVRO}, Cap. 3): {i['nome']}.\n{i['descricao']}")
        out.append(base_chunk(f"Item Mágico: {i['nome']}", f"Novos Itens Mágicos > {i['categoria']} > {i['nome']}",
                              i["pagina"], texto, tipo="item_magico", subtipo=i["subtipo"],
                              categoria=i["categoria"], nome=i["nome"]))
    for m in im["modulos"]:
        texto = f"Itens mágicos — {m['nome']} (regra, {LIVRO}, Cap. 3, pág. {m['pagina']}).\n{m['efeito']}"
        out.append(base_chunk(f"Itens Mágicos: {m['nome']}", f"Novos Itens Mágicos > {m['nome']}",
                              m["pagina"], texto, tipo="regra_opcional", subtipo="itens_magicos", nome=m["nome"]))
    porcat = "; ".join(f"{cat}: {n}" for cat, n in im["por_categoria"].items())
    out.append(base_chunk("Lista dos Novos Itens Mágicos", "Novos Itens Mágicos > Lista", im["pagina"],
                          f"Os {im['total_itens']} novos itens mágicos de {LIVRO} (Cap. 3) por categoria — {porcat}. "
                          f"Nomes: {', '.join(i['nome'] for i in im['itens'])}.",
                          tipo="item_magico_lista"))

    # ---------- Sub-backlog do Arsenal ----------
    out.append(base_chunk("Backlog do Arsenal (Cap. 3)", "Backlog", 216,
        f"Backlog do Cap. 3 (Arsenal) de {LIVRO}: integrados os Novos Equipamentos (capitulo=arsenal) e agora "
        f"o Arsenal Mágico (22 magias arcanas + 8 artefatos + {im['total_itens']} itens mágicos + regras). "
        f"Ainda NÃO integrados: Itens Superiores/Novas Melhorias, Capangas, Veículos (+os 5 do catálogo de "
        f"itens gerais) e Bases (subseção adiada).",
        tipo="pendencia", nome="Backlog do Arsenal"))

    resumo = dict(magias=mag["total"], artefatos=art["total"], itens_magicos=im["total_itens"],
                  itens_regras=im["total_modulos"], por_categoria=im["por_categoria"],
                  listas=sum(1 for c in out if c["tipo"].endswith("_lista")), total_chunks=len(out))
    return out, resumo


def eh_arsenal_magico(c):
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
        if eh_arsenal_magico(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks arsenal-magico anteriores (idempotência estreita)")

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
    meta["herois_cap3_arsenal_magico_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
