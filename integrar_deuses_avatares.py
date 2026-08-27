# -*- coding: utf-8 -*-
r"""Integra os 20 DEUSES MAIORES (Cap. 3 do *Deuses de Arton*) ao índice FAISS.

`fonte="deuses-arton"`, `capitulo="deuses-maiores"`. Por deus: 1 chunk de OVERVIEW
(lore: abertura + Motivações + Relações + Igreja e Clero) + 1 chunk de AVATAR (stat
block versalete, tipo="ameaca" subtipo="avatar" — findável pela busca de criatura).
Mais 1 chunk-lista dos 20.

Idempotência ESTREITA por fonte+capítulo (não toca em Cap 1/2/4 nem no núcleo).

Uso: python integrar_deuses_avatares.py
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
FONTE_ID = "deuses-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "deuses-maiores"
SEC = "Deuses de Arton > Capítulo 3: Deuses e Avatares"
IN = BASE / "dados" / "deuses_avatares.json"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunk_overview(d):
    nome, titulo, pag = d["nome"], d["titulo"], d["pagina"]
    linhas = [f"Deus (expandido): {titulo} ({LIVRO}, Cap. 3, pág. {pag}). "
              f"Descrição aprofundada de {nome} no Deuses de Arton."]
    if d.get("abertura"):
        linhas.append(d["abertura"])
    if d.get("motivacoes"):
        linhas.append(f"Motivações: {d['motivacoes']}")
    if d.get("relacoes"):
        linhas.append(f"Relações: {d['relacoes']}")
    if d.get("igreja_clero"):
        linhas.append(f"Igreja e Clero: {d['igreja_clero']}")
    return base_chunk(titulo, f"{nome} > Visão Geral", pag, "\n".join(linhas),
                      tipo="deus_expandido", nome=nome, deus=nome)


def chunk_avatar(d):
    a = d.get("avatar")
    if not a:
        return None
    nome, pag = d["nome"], a.get("pagina", d["pagina"])
    subtipo = f" ({a['subtipo']})" if a.get("subtipo") else ""
    papel = f" ({a['papel']})" if a.get("papel") not in ("Normal", "", None) else ""
    linhas = [
        f"Avatar Divino: {a['nome']} ({LIVRO}, Cap. 3, pág. {pag}). Avatar de {nome}.",
        f"Deus: {nome} | Nível de Desafio: ND {a['nd']} | Tipo: {a['tipo_criatura']}{subtipo} {a['tamanho']}{papel}.",
        f"Defesa: {a['defesa']} | Fortitude: {a['fortitude']} | Reflexos: {a['reflexos']} | Vontade: {a['vontade']}.",
    ]
    if a.get("resistencias"):
        linhas.append(f"Resistências e Imunidades: {a['resistencias']}.")
    pm = f" | Pontos de Mana: {a['pm']}" if a.get("pm") and str(a.get("pm")) not in ("0", "") else ""
    linhas.append(f"Pontos de Vida: {a['pv']}{pm} | Deslocamento: {a['deslocamento']}.")
    sent = f", {a['sentidos']}" if a.get("sentidos") else ""
    linhas.append(f"Sentidos: Iniciativa {a['iniciativa']}, Percepção {a['percepcao']}{sent}.")
    if a.get("corpo_a_corpo"):
        linhas.append(f"Ataque Corpo a Corpo: {a['corpo_a_corpo']}")
    if a.get("distancia"):
        linhas.append(f"Ataque à Distância: {a['distancia']}")
    if a.get("habilidades"):
        linhas.append("Habilidades Especiais:")
        for h in a["habilidades"]:
            linhas.append(f"• {h['nome']}: {h['descricao']}")
    at = a.get("atributos", {})
    if at:
        linhas.append(f"Atributos: FOR {at.get('for','—')} | DES {at.get('des','—')} | CON {at.get('con','—')} | "
                      f"INT {at.get('int','—')} | SAB {at.get('sab','—')} | CAR {at.get('car','—')}")
    if a.get("pericias"):
        linhas.append(f"Perícias: {a['pericias']}.")
    return base_chunk(f"{a['nome']} (ND {a['nd']}) - Deuses de Arton",
                      f"{nome} > Avatar", pag, "\n".join(linhas),
                      tipo="ameaca", subtipo="avatar", nome=a["nome"], deus=nome,
                      grupo="Avatares", nd=a["nd"], tipo_criatura=a["tipo_criatura"],
                      tamanho=a["tamanho"])


def chunks_de(dados):
    deuses = dados["deuses"]
    out = []
    for d in deuses:
        out.append(chunk_overview(d))
        av = chunk_avatar(d)
        if av:
            out.append(av)
    nomes = ", ".join(d["titulo"] for d in deuses)
    out.append(base_chunk(f"Lista dos Deuses Maiores ({LIVRO})", "Lista", deuses[0]["pagina"],
                          f"Os {len(deuses)} Deuses Maiores do Panteão expandidos em {LIVRO} "
                          f"(Cap. 3), cada um com Avatar: {nomes}.",
                          tipo="deus_lista"))
    resumo = dict(deuses=len(deuses),
                  avatares=sum(1 for c in out if c.get("subtipo") == "avatar"),
                  total_chunks=len(out))
    return out, resumo


def eh_cap(c):
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
        if eh_cap(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks deuses-maiores anteriores (idempotência estreita)")

    novos, resumo = chunks_de(dados)
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
    meta["deuses_cap3_maiores_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
