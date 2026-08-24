# -*- coding: utf-8 -*-
r"""Integra o CAP 1 (Campeões) de *Heróis de Arton* ao índice FAISS.

Aditivo, `fonte="herois-arton"`. Idempotente (remove chunks herois-arton antes de
reinserir). Reconstrói só os vetores novos (não reembute núcleo/ameacas-arton).

Lê 3 JSONs já extraídos e validados:
  - dados/racas_herois.json     (5 raças)
  - dados/poderes_herois.json   (443 poderes: 288 classe + 155 gerais)
  - dados/treinador_herois.json (classe Treinador + pet)

Chunks gerados:
  - 1 por raça (tipo="raca")
  - 1 por poder (tipo="poder") + listas por classe/categoria (tipo="poder_lista")
  - Treinador: visão geral + 1 por habilidade + melhor_amigo (tipo="classe")

Uso: python integrar_herois_cap1.py
"""
import json, re, shutil, time
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import fontes

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
FONTE_ID = "herois-arton"
LIVRO = fontes.titulo(FONTE_ID)          # "Heróis de Arton"
SEC = "Heróis de Arton > Capítulo 1: Campeões de Arton"


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _load(nome):
    return json.loads((BASE / "dados" / nome).read_text(encoding="utf-8"))


def chunks_racas():
    data = _load("racas_herois.json")
    out = []
    for r in data["racas"]:
        nome, pag = r["nome"], r["pagina"]
        linhas = [f"Raça: {nome} ({LIVRO}, pág. {pag})."]
        if r.get("modificadores"):
            mods = []
            if r["modificadores"].get("_flexivel"):
                mods.append(r["modificadores"]["_flexivel"])
            mods += [f"{k} {v:+d}" for k, v in r["modificadores"].items() if k != "_flexivel"]
            if mods:
                linhas.append("Modificadores de atributo: " + ", ".join(mods) + ".")
        if r.get("resumo"):
            linhas.append(r["resumo"])
        if r.get("procedural") and r.get("texto_completo"):
            linhas.append(r["texto_completo"])
        for h in r.get("habilidades", []):
            linhas.append(f"{h['nome']}: {h['efeito']}")
        out.append({
            "titulo": nome, "secao": f"{SEC} > Novas Raças > {nome}", "pagina": pag,
            "fonte": FONTE_ID, "texto": "\n".join(linhas), "tipo": "raca",
            "nome": nome, "modificadores": r.get("modificadores", {}),
        })
    return out


def chunks_poderes():
    data = _load("poderes_herois.json")
    poderes = data["poderes"]
    out = []
    for p in poderes:
        nome, pag = p["nome"], p["pagina"]
        cat = p.get("categoria")
        if cat == "classe":
            cab = f"Poder de {p.get('classe','?')}: {nome} ({LIVRO}, pág. {pag})."
        else:
            cab = f"Poder geral ({cat}): {nome} ({LIVRO}, pág. {pag})."
        linhas = [cab, p["efeito"]]
        if p.get("pre_requisito"):
            linhas.append(f"Pré-requisito: {p['pre_requisito']}.")
        out.append({
            "titulo": f"{p.get('classe') or cat}: {nome}",
            "secao": f"{SEC} > Novos Poderes > {p.get('classe') or cat} > {nome}",
            "pagina": pag, "fonte": FONTE_ID, "texto": "\n".join(linhas),
            "tipo": "poder", "categoria": cat, "classe": p.get("classe"),
            "nome": nome, "pre_requisito": p.get("pre_requisito"),
        })
    # listas por classe (poderes de classe) e por categoria (gerais)
    from collections import defaultdict
    por_classe = defaultdict(list)
    por_cat = defaultdict(list)
    for p in poderes:
        if p.get("categoria") == "classe":
            por_classe[p.get("classe")].append(p)
        else:
            por_cat[p.get("categoria")].append(p)
    for classe, lst in sorted(por_classe.items()):
        nomes = ", ".join(x["nome"] for x in lst)
        out.append({
            "titulo": f"Novos poderes de {classe} ({LIVRO})",
            "secao": f"{SEC} > Novos Poderes de Classe > {classe}",
            "pagina": lst[0]["pagina"], "fonte": FONTE_ID,
            "texto": f"Novos poderes de classe de {classe} em {LIVRO} ({len(lst)}): {nomes}.",
            "tipo": "poder_lista", "categoria": "classe", "classe": classe,
        })
    for cat, lst in sorted(por_cat.items()):
        nomes = ", ".join(x["nome"] for x in lst)
        out.append({
            "titulo": f"Novos poderes gerais: {cat} ({LIVRO})",
            "secao": f"{SEC} > Novos Poderes Gerais > {cat}",
            "pagina": lst[0]["pagina"], "fonte": FONTE_ID,
            "texto": f"Novos poderes gerais de {cat} em {LIVRO} ({len(lst)}): {nomes}.",
            "tipo": "poder_lista", "categoria": cat,
        })
    return out


def chunks_treinador():
    data = _load("treinador_herois.json")
    c = data["classes"][0]
    pag = c["pagina"]
    out = []
    car = c.get("caracteristicas", {})
    vg = [f"Classe: {c['nome']} ({LIVRO}, pág. {pag}). Classe nova de Heróis de Arton.",
          f"Atributo principal: {c['atributo_principal']['texto']}."]
    for k, lab in [("pv", "Pontos de Vida"), ("pm", "Pontos de Mana"),
                   ("pericias", "Perícias"), ("proficiencias", "Proficiências")]:
        if car.get(k):
            vg.append(f"{lab}: {car[k]}.")
    if c.get("resumo"):
        vg.append(c["resumo"])
    out.append({
        "titulo": f"{c['nome']}: visão geral", "secao": f"{SEC} > Nova Classe: Treinador",
        "pagina": pag, "fonte": FONTE_ID, "texto": "\n".join(vg),
        "tipo": "classe", "subtipo": "visao_geral", "classe": c["nome"], "nome": c["nome"],
    })
    for h in c.get("habilidades", []):
        out.append({
            "titulo": f"{c['nome']}: {h['nome']}",
            "secao": f"{SEC} > Nova Classe: Treinador > Habilidades > {h['nome']}",
            "pagina": pag, "fonte": FONTE_ID,
            "texto": f"Habilidade de Treinador: {h['nome']} ({LIVRO}, pág. {pag}).\n{h['efeito']}",
            "tipo": "classe", "subtipo": "habilidade", "classe": c["nome"], "nome": h["nome"],
        })
    if c.get("melhor_amigo"):
        out.append({
            "titulo": "Treinador: O Melhor Amigo (pet)",
            "secao": f"{SEC} > Nova Classe: Treinador > O Melhor Amigo",
            "pagina": 22, "fonte": FONTE_ID,
            "texto": f"O Melhor Amigo — o companheiro da classe Treinador ({LIVRO}, pág. 22).\n{c['melhor_amigo']}",
            "tipo": "classe", "subtipo": "companheiro", "classe": c["nome"], "nome": "O Melhor Amigo",
        })
    return out


def chunks_origens():
    data = _load("origens_herois.json")
    out = []
    for o in data["origens"]:
        nome, pag = o["nome"], o["pagina"]
        linhas = [f"Origem: {nome} ({LIVRO}, pág. {pag})."]
        if o.get("resumo"):
            linhas.append(o["resumo"])
        if o.get("itens"):
            linhas.append(f"Itens: {o['itens']}.")
        if o.get("beneficios"):
            linhas.append(f"Benefícios: {o['beneficios']}")
        if o.get("pericias"):
            linhas.append(f"Perícias concedidas: {', '.join(o['pericias'])}.")
        if o.get("poder_unico"):
            pu = o["poder_unico"]
            linhas.append(f"Poder único — {pu['nome']}: {pu['efeito']}")
        out.append({
            "titulo": nome, "secao": f"{SEC} > Novas Origens > {nome}", "pagina": pag,
            "fonte": FONTE_ID, "texto": "\n".join(linhas), "tipo": "origem",
            "nome": nome, "pericias": o.get("pericias", []), "poderes": o.get("poderes", []),
        })
    return out


def chunks_variantes():
    data = _load("variantes_herois.json")
    out = []
    for v in data["variantes"]:
        nome, pag = v["nome"], v["pagina"]
        car = v.get("caracteristicas", {})
        vg = [f"Classe variante: {nome} ({LIVRO}, pág. {pag}). Variante de classe de Heróis de Arton."]
        for k, lab in [("pv", "Pontos de Vida"), ("pm", "Pontos de Mana"),
                       ("pericias", "Perícias"), ("proficiencias", "Proficiências")]:
            if car.get(k):
                vg.append(f"{lab}: {car[k]}.")
        if v.get("resumo"):
            vg.append(v["resumo"])
        out.append({
            "titulo": f"{nome} (variante)", "secao": f"{SEC} > Classes Variantes > {nome}",
            "pagina": pag, "fonte": FONTE_ID, "texto": "\n".join(vg),
            "tipo": "classe", "subtipo": "variante", "classe": nome, "nome": nome,
        })
        for h in v.get("habilidades", []):
            out.append({
                "titulo": f"{nome} (variante): {h['nome']}",
                "secao": f"{SEC} > Classes Variantes > {nome} > {h['nome']}",
                "pagina": pag, "fonte": FONTE_ID,
                "texto": f"Habilidade da variante {nome}: {h['nome']} ({LIVRO}, pág. {pag}).\n{h['efeito']}",
                "tipo": "classe", "subtipo": "variante_habilidade", "classe": nome, "nome": h["nome"],
            })
    return out


def chunks_tabelas():
    p = BASE / "dados" / "tabelas_herois.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for t in data["tabelas"]:
        out.append({
            "titulo": f"Tabela {t['numero']}: {t['titulo']} ({LIVRO})",
            "secao": f"{SEC} > Tabelas para Personagens > {t['titulo']}",
            "pagina": 98, "fonte": FONTE_ID,
            "texto": f"Tabela {t['numero']} — {t['titulo']} ({LIVRO}, Cap. 1).\n{t['texto']}",
            "tipo": "tabela", "nome": t["titulo"],
        })
    return out


def eh_herois(c):
    return c.get("fonte") == FONTE_ID or str(c.get("secao", "")).startswith("Heróis de Arton")


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
        if eh_herois(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks herois-arton anteriores (idempotência)")

    novos = (chunks_racas() + chunks_poderes() + chunks_treinador()
             + chunks_origens() + chunks_variantes() + chunks_tabelas())
    n_raca = sum(1 for c in novos if c["tipo"] == "raca")
    n_pod = sum(1 for c in novos if c["tipo"] == "poder")
    n_cls = sum(1 for c in novos if c["tipo"] == "classe")
    n_ori = sum(1 for c in novos if c["tipo"] == "origem")
    n_tab = sum(1 for c in novos if c["tipo"] == "tabela")
    print(f"[3/5] {len(novos)} chunks gerados (raças {n_raca}, poderes {n_pod}+listas, "
          f"classes {n_cls}, origens {n_ori}, tabelas {n_tab}).")

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
    meta.setdefault("fontes", {})[FONTE_ID] = len(novos)
    meta["herois_cap1_estruturado"] = {"racas": n_raca, "poderes": n_pod,
                                       "classes": n_cls, "origens": n_ori, "tabelas": n_tab}
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)}). "
          f"Tempo {time.time()-t0:.1f}s. Backup {backup_dir.name}")


if __name__ == "__main__":
    integrar()
