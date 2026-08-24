# -*- coding: utf-8 -*-
r"""
Integra a família AMEAÇAS DE ARTON estruturada (dados/ameacas_arton.json) ao índice FAISS.

Granularidade:
  - 1 chunk fino por CRIATURA (324 chunks) com stat block completo, ataques, habilidades, defesas e atributos.
  - 29 chunks-LISTA agregados por Grupo (todos os 29 grupos do Bestiário).
  - 4 chunks-LISTA agregados por Faixa de ND (Iniciante, Veterano, Campeão, Lendário).

Integração ADITIVA com carimbo de procedência `fonte="ameacas-arton"`.
Idempotente (remove chunks de ameacas-arton anteriores antes de reinserir).
Reconstrói o índice SEM reembutir as outras famílias (só os novos chunks, ~30-40s na CPU).

Uso: python integrar_ameacas_arton.py
"""

import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
AMEACAS_ARTON_JSON = BASE / "dados" / "ameacas_arton.json"
SEC_BASE = "Ameaças de Arton > Capítulo 1: O Bestiário"
FONTE_ID = "ameacas-arton"


def chunk_criatura(c):
    """Gera chunk individual fino para uma criatura de Ameaças de Arton."""
    nome = c["nome"]
    grupo = c["grupo"]
    nd = c["nd"]
    tipo = c["tipo_criatura"]
    subtipo = f" ({c['subtipo']})" if c.get("subtipo") else ""
    tamanho = c["tamanho"]
    papel = f" ({c['papel']})" if c.get("papel") != "Normal" else ""
    pag = c.get("pagina", 32)

    linhas = [
        f"Ameaça: {nome} (Ameaças de Arton, pág. {pag}).",
        f"Grupo: {grupo} | Nível de Desafio: ND {nd} | Tipo: {tipo}{subtipo} {tamanho}{papel}.",
        f"Defesa: {c['defesa']} | Fortitude: {c['fortitude']} | Reflexos: {c['reflexos']} | Vontade: {c['vontade']}.",
    ]

    if c.get("resistencias"):
        linhas.append(f"Resistências e Imunidades: {c['resistencias']}.")

    pm_str = f" | Pontos de Mana: {c['pm']}" if c.get("pm") and str(c.get("pm")) != "0" else ""
    linhas.append(f"Pontos de Vida: {c['pv']}{pm_str} | Deslocamento: {c['deslocamento']}.")
    
    sentidos_str = f", {c['sentidos']}" if c.get("sentidos") else ""
    linhas.append(f"Sentidos: Iniciativa {c['iniciativa']}, Percepção {c['percepcao']}{sentidos_str}.")

    if c.get("corpo_a_corpo"):
        linhas.append(f"Ataque Corpo a Corpo: {c['corpo_a_corpo']}")
    if c.get("distancia"):
        linhas.append(f"Ataque à Distância: {c['distancia']}")

    if c.get("habilidades"):
        linhas.append("Habilidades Especiais:")
        for h in c["habilidades"]:
            linhas.append(f"• {h['nome']}: {h['descricao']}")

    atrs = c.get("atributos", {})
    if atrs:
        linhas.append(
            f"Atributos: FOR {atrs.get('for', '-')} | DES {atrs.get('des', '-')} | CON {atrs.get('con', '-')} | "
            f"INT {atrs.get('int', '-')} | SAB {atrs.get('sab', '-')} | CAR {atrs.get('car', '-')}"
        )

    if c.get("pericias"):
        linhas.append(f"Perícias: {c['pericias']}.")
    if c.get("equipamento"):
        linhas.append(f"Equipamento: {c['equipamento']}.")
    if c.get("tesouro"):
        linhas.append(f"Tesouro: {c['tesouro']}.")

    return {
        "titulo": f"{nome} (ND {nd}) - Ameaças de Arton",
        "secao": f"{SEC_BASE} > {grupo} > {nome}",
        "pagina": pag,
        "fonte": FONTE_ID,
        "texto": "\n".join(linhas),
        "tipo": "ameaca",
        "nome": nome,
        "grupo": grupo,
        "nd": nd,
        "tipo_criatura": tipo,
        "tamanho": tamanho,
        "papel": c.get("papel", "Normal"),
    }


def chunk_lista_grupo(grupo, criaturas):
    """Gera chunk-lista para um grupo de criaturas de Ameaças de Arton."""
    crias_grupo = [c for c in criaturas if c.get("grupo") == grupo]
    if not crias_grupo:
        return None

    linhas = [
        f"Lista de Criaturas e Ameaças: {grupo} (Ameaças de Arton, Capítulo 1):",
        f"Total de {len(crias_grupo)} criaturas catalogadas neste grupo:",
        "",
    ]
    for c in crias_grupo:
        linhas.append(
            f"• {c['nome']} (ND {c['nd']}): {c['tipo_criatura']} {c['tamanho']}, Defesa {c['defesa']}, PV {c['pv']}. (pág. {c['pagina']})"
        )

    return {
        "titulo": f"Lista de Criaturas: {grupo} (Ameaças de Arton)",
        "secao": f"{SEC_BASE} > Listas > Grupo {grupo}",
        "pagina": crias_grupo[0]["pagina"],
        "fonte": FONTE_ID,
        "texto": "\n".join(linhas),
        "tipo": "ameaca_lista",
        "categoria_filtro": "grupo",
        "grupo": grupo,
    }


def chunk_lista_nd(rotulo, nds, criaturas, pag):
    """Gera chunk-lista para uma faixa de Nível de Desafio de Ameaças de Arton."""
    crias_nd = [c for c in criaturas if str(c.get("nd")) in nds]
    if not crias_nd:
        return None

    linhas = [
        f"Lista de Criaturas por Nível de Desafio: {rotulo} (Ameaças de Arton):",
        f"Total de {len(crias_nd)} criaturas nesta faixa de ND:",
        "",
    ]
    for c in crias_nd:
        linhas.append(
            f"• {c['nome']} (ND {c['nd']} - Grupo: {c['grupo']}): {c['tipo_criatura']} {c['tamanho']}, Def {c['defesa']}, PV {c['pv']}."
        )

    return {
        "titulo": f"Lista de Criaturas por ND: {rotulo} (Ameaças de Arton)",
        "secao": f"{SEC_BASE} > Listas > ND {rotulo}",
        "pagina": pag,
        "fonte": FONTE_ID,
        "texto": "\n".join(linhas),
        "tipo": "ameaca_lista",
        "categoria_filtro": "nd",
        "faixa_nd": rotulo,
    }


def gerar_chunks_ameacas_arton():
    """Lê dados/ameacas_arton.json e retorna a lista de chunks estruturados."""
    data = json.loads(AMEACAS_ARTON_JSON.read_text(encoding="utf-8"))
    criaturas = data.get("criaturas", [])

    novos = []
    # 1. Chunks individuais de criaturas
    for c in criaturas:
        novos.append(chunk_criatura(c))

    # 2. Chunks-lista por grupo (distintos de Ameaças de Arton)
    grupos = sorted(list({c.get("grupo") for c in criaturas if c.get("grupo")}))
    for g in grupos:
        ck = chunk_lista_grupo(g, criaturas)
        if ck:
            novos.append(ck)

    # 3. Chunks-lista por faixa de ND
    faixas = [
        ("Iniciante (ND 1/4 a ND 1)", ["1/4", "1/2", "1"], 32),
        ("Veterano (ND 2 a ND 4)", ["2", "3", "4"], 32),
        ("Campeão (ND 5 a ND 9)", ["5", "6", "7", "8", "9"], 32),
        ("Lendário (ND 10 a ND 20)", ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "S", "S+"], 32),
    ]
    for rot, nds, pag in faixas:
        ck = chunk_lista_nd(rot, nds, criaturas, pag)
        if ck:
            novos.append(ck)

    return novos


def eh_chunk_ameacas_arton_antigo(c):
    """Identifica chunks de Ameaças de Arton a remover para garantir idempotência."""
    fonte = c.get("fonte", "")
    sec = c.get("secao", "")
    if fonte == FONTE_ID:
        return True
    if sec.startswith(SEC_BASE) or sec.startswith("Ameaças de Arton"):
        return True
    return False


def integrar():
    t0 = time.time()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = INDEX_DIR / f"backup-{ts}"

    # 1. Backup
    print(f"[1/5] Backup do índice em {backup_dir.name}\\")
    backup_dir.mkdir(exist_ok=True)
    for fn in ["chunks.jsonl", "meta.json", "tormenta.faiss"]:
        p = INDEX_DIR / fn
        if p.exists():
            shutil.copy2(p, backup_dir / fn)

    # 2. Carrega índice atual
    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    chunks_linhas = (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    chunks_atuais = [json.loads(l) for l in chunks_linhas if l.strip()]
    idx_faiss = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))

    n_antes = len(chunks_atuais)
    dim = idx_faiss.d
    print(f"[2/5] Índice atual: {n_antes} chunks, dim {dim}")

    # 3. Filtra chunks mantidos vs removidos
    manter_indices = []
    chunks_mantidos = []
    removidos_count = 0

    for i, c in enumerate(chunks_atuais):
        if eh_chunk_ameacas_arton_antigo(c):
            removidos_count += 1
        else:
            manter_indices.append(i)
            chunks_mantidos.append(c)

    if removidos_count > 0:
        print(f"      Removendo {removidos_count} chunks anteriores de Ameaças de Arton (idempotência)")

    # 4. Gera novos chunks estruturados de Ameaças de Arton
    novos_chunks = gerar_chunks_ameacas_arton()
    crias_count = sum(1 for c in novos_chunks if c["tipo"] == "ameaca")
    listas_count = sum(1 for c in novos_chunks if c["tipo"] == "ameaca_lista")
    print(f"[3/5] {len(novos_chunks)} chunks estruturados de Ameaças de Arton gerados ({crias_count} criaturas, {listas_count} listas).")
    print(f"      Reconstruindo vetores mantidos...")

    # 5. Reconstrói vetores mantidos
    if manter_indices:
        vecs_mantidos = np.empty((len(manter_indices), dim), dtype="float32")
        for pos_nova, pos_antiga in enumerate(manter_indices):
            vecs_mantidos[pos_nova] = idx_faiss.reconstruct(int(pos_antiga))
    else:
        vecs_mantidos = np.empty((0, dim), dtype="float32")

    # 6. Embutir apenas os novos chunks
    print(f"[4/5] Carregando embedder BAAI/bge-m3 e embutindo {len(novos_chunks)} novos chunks...")
    t_emb0 = time.time()
    model = SentenceTransformer("BAAI/bge-m3")
    textos_novos = [c["texto"] for c in novos_chunks]
    vecs_novos = model.encode(
        textos_novos,
        batch_size=8,
        show_progress_bar=False,
        normalize_embeddings=True,
    ).astype("float32")
    t_emb = time.time() - t_emb0
    print(f"      {len(novos_chunks)} vetores embutidos em {t_emb:.1f}s")

    # 7. Concatena vetores e cria novo IndexFlatIP
    if len(vecs_mantidos) > 0:
        todos_vecs = np.vstack([vecs_mantidos, vecs_novos])
    else:
        todos_vecs = vecs_novos

    novo_index = faiss.IndexFlatIP(dim)
    novo_index.add(todos_vecs)

    # 8. Atualiza chunks.jsonl
    todos_chunks = chunks_mantidos + novos_chunks
    for i, c in enumerate(todos_chunks):
        c["id"] = i

    linhas_out = [json.dumps(c, ensure_ascii=False) for c in todos_chunks]
    (INDEX_DIR / "chunks.jsonl").write_text("\n".join(linhas_out) + "\n", encoding="utf-8")
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))

    # 9. Atualiza meta.json
    meta["n_chunks"] = len(todos_chunks)
    meta["ameacas_arton_estruturadas"] = crias_count
    # Contabilidade de procedência por FONTE (conta CHUNKS, não criaturas):
    # mantém o dict `fontes` coerente com n_chunks quando um livro é (re)integrado.
    meta.setdefault("fontes", {})[FONTE_ID] = len(novos_chunks)
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = time.time() - t0
    print(f"[5/5] SUCESSO — Índice: {n_antes} -> {len(todos_chunks)} chunks (+{len(novos_chunks)} novos estruturados de Ameaças de Arton).")
    print(f"      Tempo total: {dt:.1f}s. Backup em {backup_dir.name}\\")


if __name__ == "__main__":
    integrar()
