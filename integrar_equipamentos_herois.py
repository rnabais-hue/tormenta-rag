# -*- coding: utf-8 -*-
r"""Integra os NOVOS EQUIPAMENTOS do Cap. 3 (Arsenal) de *Heróis de Arton* ao FAISS.

Escopo SEGURO (188 registros validados): Armas 39 + Munições especiais 5 +
Armaduras & Escudos 14 + Itens Gerais 128 (EXCLUI os 5 veículos-de-catálogo sem
descrição, que entram com a seção Veículos) + Habilidades de arma 2. Também grava
1 chunk de PENDÊNCIA documentando o que falta do Arsenal.

Aditivo, `fonte="herois-arton"`. IDEMPOTÊNCIA ESTREITA: remove apenas chunks
com capitulo=="arsenal" (NÃO toca no Cap 1 herois-arton nem no núcleo/ameacas).
Reconstrói só os vetores novos (não reembute o resto).

Uso: python integrar_equipamentos_herois.py
"""
import json, re, shutil, time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import fontes

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
FONTE_ID = "herois-arton"
LIVRO = fontes.titulo(FONTE_ID)                       # "Heróis de Arton"
CAP = "arsenal"                                        # marcador de idempotência estreita
SEC = "Heróis de Arton > Capítulo 3: Arsenal dos Heróis"
IN = BASE / "dados" / "equipamentos_herois.json"


def _fmt(campos):
    """Monta 'k v' pulando vazios/—."""
    partes = []
    for lab, val in campos:
        v = str(val or "").strip()
        if v and v != "—":
            partes.append(f"{lab} {v}")
    return ", ".join(partes)


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def chunks_de(dados):
    out = []
    armas = dados.get("armas", [])
    munis = dados.get("municoes", [])
    arms = dados.get("armaduras_escudos", [])
    gerais = [g for g in dados.get("itens_gerais", []) if g.get("subcategoria") != "Veículos"]
    habs = dados.get("habilidades_arma", [])

    # --- armas ---
    for a in armas:
        stats = _fmt([("proficiência", a.get("proficiencia")), ("empunhadura", a.get("empunhadura")),
                      ("preço", a.get("preco")), ("dano", a.get("dano")), ("crítico", a.get("critico")),
                      ("alcance", a.get("alcance")), ("tipo", a.get("tipo_dano")),
                      ("espaços", a.get("espacos"))])
        texto = f"Arma nova: {a['nome']} ({LIVRO}, pág. {a['pagina']}). {stats}."
        if a.get("descricao"):
            texto += "\n" + a["descricao"]
        out.append(base_chunk(a["nome"], f"Novas Armas > {a['nome']}", a["pagina"], texto,
                              tipo="equipamento", categoria="arma", nome=a["nome"],
                              proficiencia=a.get("proficiencia"), empunhadura=a.get("empunhadura")))

    # --- munições especiais ---
    for m in munis:
        stats = _fmt([("preço", m.get("preco")), ("espaços", m.get("espacos"))])
        texto = f"Munição especial: {m['nome']} ({LIVRO}, pág. {m['pagina']}). {stats}."
        if m.get("descricao"):
            texto += "\n" + m["descricao"]
        out.append(base_chunk(m["nome"], f"Munições Especiais > {m['nome']}", m["pagina"], texto,
                              tipo="equipamento", categoria="municao", nome=m["nome"]))

    # --- armaduras & escudos ---
    for a in arms:
        stats = _fmt([("preço", a.get("preco")), ("bônus na Defesa", a.get("bonus_defesa")),
                      ("penalidade de armadura", a.get("penalidade")), ("espaços", a.get("espacos"))])
        rot = "Escudo novo" if a.get("categoria") == "escudo" else "Armadura nova"
        texto = f"{rot}: {a['nome']} ({LIVRO}, pág. {a['pagina']}; {a.get('subcategoria','')}). {stats}."
        if a.get("descricao"):
            texto += "\n" + a["descricao"]
        out.append(base_chunk(a["nome"], f"Armaduras & Escudos > {a.get('subcategoria','')} > {a['nome']}",
                              a["pagina"], texto, tipo="equipamento", categoria=a.get("categoria"),
                              subcategoria=a.get("subcategoria"), nome=a["nome"]))

    # --- itens gerais ---
    for g in gerais:
        stats = _fmt([("preço", g.get("preco")), ("espaços", g.get("espacos"))])
        texto = f"Item geral novo ({g.get('subcategoria','')}): {g['nome']} ({LIVRO}, pág. {g['pagina']}). {stats}."
        if g.get("descricao"):
            texto += "\n" + g["descricao"]
        out.append(base_chunk(g["nome"], f"Itens Gerais > {g.get('subcategoria','')} > {g['nome']}",
                              g["pagina"], texto, tipo="equipamento", categoria="item_geral",
                              subcategoria=g.get("subcategoria"), nome=g["nome"]))

    # --- habilidades de arma ---
    for h in habs:
        texto = f"Nova habilidade de arma: {h['nome']} ({LIVRO}, pág. {h['pagina']}).\n{h.get('descricao','')}"
        out.append(base_chunk(h["nome"], f"Novas Habilidades de Armas > {h['nome']}", h["pagina"],
                              texto, tipo="habilidade_arma", nome=h["nome"]))

    # --- listas de recuperação ---
    def lista(titulo, subsecao, pagina, itens, rotulo, categoria=None):
        nomes = ", ".join(i["nome"] for i in itens)
        return base_chunk(titulo, subsecao, pagina,
                          f"{rotulo} de {LIVRO} ({len(itens)}): {nomes}.",
                          tipo="equipamento_lista", categoria=categoria)

    listas = []
    if armas:
        listas.append(lista(f"Novas armas ({LIVRO})", "Novas Armas", armas[0]["pagina"],
                            armas, "Novas armas", "arma"))
    if munis:
        listas.append(lista(f"Novas munições especiais ({LIVRO})", "Munições Especiais",
                            munis[0]["pagina"], munis, "Novas munições especiais", "municao"))
    if arms:
        listas.append(lista(f"Novas armaduras e escudos ({LIVRO})", "Armaduras & Escudos",
                            arms[0]["pagina"], arms, "Novas armaduras e escudos"))
    por_sub = defaultdict(list)
    for g in gerais:
        por_sub[g.get("subcategoria", "")].append(g)
    for sub, lst in sorted(por_sub.items()):
        listas.append(lista(f"Novos itens gerais: {sub} ({LIVRO})", f"Itens Gerais > {sub}",
                            lst[0]["pagina"], lst, f"Novos itens gerais ({sub})", "item_geral"))
    out.extend(listas)

    # --- chunk de PENDÊNCIA ---
    pend = (
        f"Pendências do Arsenal (Cap. 3 de {LIVRO}) ainda NÃO integradas ao RAG: "
        "(1) Itens Superiores / Novas Melhorias (Tabela 3-5); "
        "(2) Capangas (tipos de capanga/mercenário para contratar); "
        "(3) Veículos (características + lista + os 5 veículos do catálogo de itens gerais, "
        "cuja descrição vive nesta seção); "
        "(4) Novas Magias Arcanas; (5) Novos Itens Mágicos; (6) Artefatos; "
        "(7) a subseção Bases (adiada por decisão do usuário). "
        "Já integrado e seguro: novas armas, munições especiais, armaduras & escudos, "
        "itens gerais (exceto veículos) e novas habilidades de arma. "
        "Follow-up técnico: incluir o equipamento de Heróis no filtro híbrido "
        "detectar_filtro_equipamento() de perguntar.py."
    )
    out.append(base_chunk(f"Pendências do Arsenal ({LIVRO})", "Pendências", 216, pend,
                          tipo="pendencia", nome="Pendências do Arsenal"))
    return out, dict(armas=len(armas), municoes=len(munis), armaduras_escudos=len(arms),
                     itens_gerais=len(gerais), habilidades_arma=len(habs), listas=len(listas))


def eh_arsenal(c):
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
        if eh_arsenal(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks arsenal anteriores (idempotência estreita)")

    novos, resumo = chunks_de(dados)
    print(f"[3/5] {len(novos)} chunks gerados: {resumo} + 1 pendência.")

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
    # recomputa fontes do zero (robusto contra drift)
    meta["fontes"] = dict(Counter(c.get("fonte", "nucleo") for c in todos_chunks))
    meta["herois_cap3_arsenal_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s. Backup {backup_dir.name}")


if __name__ == "__main__":
    integrar()
