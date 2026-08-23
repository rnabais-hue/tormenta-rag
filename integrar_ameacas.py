# -*- coding: utf-8 -*-
r"""
Integra a família AMEAÇAS estruturada (dados/ameacas.json) ao índice FAISS.

Granularidade:
  - 1 chunk fino por CRIATURA (80 chunks) com stat block completo, ataques, habilidades, defesas e atributos.
  - 9 chunks-LISTA agregados por Grupo (Masmorras, Ermos, Puristas, Mortos-Vivos, Duyshidakk, Sszzaazitas, Trolls, Dragões, Tormenta).
  - 4 chunks-LISTA agregados por Faixa de ND (Iniciante, Veterano, Campeão, Lendário).
  - 3 chunks PROCEDURAIS de regras de ameaças (págs 288–291: Papéis de Combate; págs 323–327: Perigos Complexos; págs 328–329: Criação de NPCs).

Substitui estritamente os 97 chunks antigos de texto corrido do Capítulo 7: Ameaças (págs 286–329).
Reconstrói o índice SEM reembutir as outras famílias (só os 96 novos chunks, ~40-60s na CPU).

Idempotente (remove chunks de ameaças anteriores antes de reinserir).
Uso: python integrar_ameacas.py
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
AMEACAS_JSON = BASE / "dados" / "ameacas.json"
SEC_BASE = "Capítulo 7: Ameaças"


def chunk_criatura(c):
    """Gera chunk individual fino para uma criatura/monstro."""
    nome = c["nome"]
    grupo = c["grupo"]
    nd = c["nd"]
    tipo = c["tipo_criatura"]
    subtipo = f" ({c['subtipo']})" if c.get("subtipo") else ""
    tamanho = c["tamanho"]
    papel = f" ({c['papel']})" if c.get("papel") != "Normal" else ""
    pag = c.get("pagina", 292)

    linhas = [
        f"Ameaça: {nome} (Tormenta20, pág. {pag}).",
        f"Grupo: {grupo} | Nível de Desafio: ND {nd} | Tipo: {tipo}{subtipo} {tamanho}{papel}.",
        f"Defesa: {c['defesa']} | Fortitude: {c['fortitude']} | Reflexos: {c['reflexos']} | Vontade: {c['vontade']}.",
    ]

    if c.get("resistencias"):
        linhas.append(f"Resistências e Imunidades: {c['resistencias']}.")

    pm_str = f" | Pontos de Mana: {c['pm']}" if c.get("pm", 0) > 0 else ""
    linhas.append(f"Pontos de Vida: {c['pv']}{pm_str} | Deslocamento: {c['deslocamento']}.")
    linhas.append(f"Sentidos: Iniciativa {c['iniciativa']}, Percepção {c['percepcao']}, {c['sentidos']}.")

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
        "titulo": f"{nome} (ND {nd})",
        "secao": f"{SEC_BASE} > Bestiário > {grupo} > {nome}",
        "pagina": pag,
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
    """Gera chunk-lista para um grupo de criaturas."""
    crias_grupo = [c for c in criaturas if c.get("grupo") == grupo]
    linhas = [
        f"Lista de Criaturas e Ameaças: {grupo} (Tormenta20, Capítulo 7):",
        f"Total de {len(crias_grupo)} criaturas catalogadas neste grupo:",
        "",
    ]
    for c in crias_grupo:
        linhas.append(
            f"• {c['nome']} (ND {c['nd']}): {c['tipo_criatura']} {c['tamanho']}, Defesa {c['defesa']}, PV {c['pv']}. (pág. {c['pagina']})"
        )

    return {
        "titulo": f"Lista de Criaturas: {grupo}",
        "secao": f"{SEC_BASE} > Listas > Grupo {grupo}",
        "pagina": crias_grupo[0]["pagina"] if crias_grupo else 292,
        "texto": "\n".join(linhas),
        "tipo": "ameaca_lista",
        "categoria_filtro": "grupo",
        "grupo": grupo,
    }


def chunk_lista_nd(rotulo, nds, criaturas, pag):
    """Gera chunk-lista para uma faixa de Nível de Desafio."""
    crias_nd = [c for c in criaturas if c.get("nd") in nds]
    linhas = [
        f"Lista de Criaturas por Nível de Desafio: {rotulo} (Tormenta20, Tabela 7-1):",
        f"Total de {len(crias_nd)} criaturas nesta faixa de ND:",
        "",
    ]
    for c in crias_nd:
        linhas.append(
            f"• {c['nome']} (ND {c['nd']} - Grupo: {c['grupo']}): {c['tipo_criatura']} {c['tamanho']}, Def {c['defesa']}, PV {c['pv']}."
        )

    return {
        "titulo": f"Lista de Criaturas por ND: {rotulo}",
        "secao": f"{SEC_BASE} > Listas > ND {rotulo}",
        "pagina": pag,
        "texto": "\n".join(linhas),
        "tipo": "ameaca_lista",
        "categoria_filtro": "nd",
        "faixa_nd": rotulo,
    }


def chunk_regra(r):
    """Gera chunk para regras procedurais de ameaças e perigos."""
    return {
        "titulo": r.get("titulo", "Regra de Ameaças"),
        "secao": f"{SEC_BASE} > Regras > {r.get('titulo')}",
        "pagina": r.get("pagina", 289),
        "texto": f"{r.get('titulo')} (Tormenta20, pág. {r.get('pagina', 289)}).\n{r.get('texto', '')}",
        "tipo": "ameaca_regra",
    }


def gerar_chunks_ameacas():
    """Lê dados/ameacas.json e retorna a lista de 96 chunks estruturados."""
    data = json.loads(AMEACAS_JSON.read_text(encoding="utf-8"))
    criaturas = data.get("criaturas", [])
    regras = data.get("regras", [])

    novos = []
    # 1. Chunks individuais de criaturas (80)
    for c in criaturas:
        novos.append(chunk_criatura(c))

    # 2. Chunks-lista por grupo (9)
    grupos = [
        "Masmorras", "Ermos", "Puristas", "Reino dos Mortos",
        "Duyshidakk", "Sszzaazitas", "Trolls nobres", "Dragões", "Tormenta"
    ]
    for g in grupos:
        novos.append(chunk_lista_grupo(g, criaturas))

    # 3. Chunks-lista por faixa de ND (4)
    faixas = [
        ("Iniciante (ND 1/4 a ND 1)", ["1/4", "1/2", "1"], 291),
        ("Veterano (ND 2 a ND 4)", ["2", "3", "4"], 291),
        ("Campeão (ND 5 a ND 9)", ["5", "6", "7", "8", "9"], 291),
        ("Lendário (ND 10 a ND 20)", ["10", "11", "12", "13", "14", "15", "16", "20"], 291),
    ]
    for rot, nds, pag in faixas:
        novos.append(chunk_lista_nd(rot, nds, criaturas, pag))

    # 4. Chunks procedurais de regras (3)
    for r in regras:
        novos.append(chunk_regra(r))

    return novos


def eh_chunk_ameacas_antigo(c):
    """Identifica chunks antigos do Capítulo 7 a remover."""
    sec = c.get("secao", "")
    tipo = c.get("tipo", "")
    pag = c.get("pagina", 0)

    # Chunks estruturados anteriores (idempotência)
    if tipo in ["ameaca", "ameaca_lista", "ameaca_regra"]:
        return True
    if sec.startswith(SEC_BASE):
        return True
        
    # Chunks antigos de texto corrido do Cap 7 (págs 286–329)
    if 286 <= pag <= 329 and ("Capítulo 7" in sec or "Ameaças" in sec or "Criaturas" in sec or "Mestre" not in sec):
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
        if eh_chunk_ameacas_antigo(c):
            removidos_count += 1
        else:
            manter_indices.append(i)
            chunks_mantidos.append(c)

    print(f"      Removendo {removidos_count} chunks antigos do Capítulo 7: Ameaças")

    # 4. Gera novos chunks estruturados de ameaças
    novos_chunks = gerar_chunks_ameacas()
    print(f"[3/5] {len(novos_chunks)} chunks estruturados de ameaças gerados (80 criaturas, 13 listas, 3 regras).")
    print(f"      Reconstruindo vetores das outras famílias...")

    # 5. Reconstrói vetores mantidos
    if manter_indices:
        vecs_mantidos = np.empty((len(manter_indices), dim), dtype="float32")
        for pos_nova, pos_antiga in enumerate(manter_indices):
            vecs_mantidos[pos_nova] = idx_faiss.reconstruct(int(pos_antiga))
    else:
        vecs_mantidos = np.empty((0, dim), dtype="float32")

    # 6. Embutir apenas os 96 novos chunks
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
    meta["ameacas_estruturadas"] = 80
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = time.time() - t0
    print(f"[5/5] SUCESSO — Índice: {n_antes} -> {len(todos_chunks)} chunks (-{removidos_count} antigos, +{len(novos_chunks)} novos estruturados).")
    print(f"      Tempo total: {dt:.1f}s. Backup em {backup_dir.name}\\")


if __name__ == "__main__":
    integrar()
