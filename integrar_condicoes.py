# -*- coding: utf-8 -*-
r"""
Integra a família CONDIÇÕES estruturada (dados/condicoes.json) ao índice FAISS.

Granularidade:
  - 1 chunk fino por CONDIÇÃO (35 chunks) com nome, tipo de efeito, escalamento e efeito mecânico completo.
  - 1 chunk-LISTA agregado com todas as 35 condições agrupadas por tipo de efeito.
  - 1 chunk PROCEDURAL de regra geral de condições (págs 400–401: acúmulo, duração de cena e tipos de efeitos).

Substitui estritamente os chunks antigos de texto corrido do Apêndice: Lista de Condições (págs 400–401).
Reconstrói o índice SEM reembutir as outras famílias (só os 37 novos chunks, ~15-30s na CPU).

Idempotente (remove chunks de condição anteriores antes de reinserir).
Uso: python integrar_condicoes.py
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
CONDICOES_JSON = BASE / "dados" / "condicoes.json"
SEC_BASE = "Apêndice: Lista de Condições"


def chunk_condicao(c):
    """Gera chunk individual fino para uma condição."""
    nome = c["nome"]
    tipo_efeito = c.get("tipo_efeito", "Geral")
    piora = c.get("piora_para", "")
    desc = c.get("descricao", "")
    pag = c.get("pagina", 400)

    header_parts = [f"Tipo de Efeito: {tipo_efeito}"]
    if piora:
        header_parts.append(f"Piora Para: {piora}")

    txt = (
        f"Condição: {nome} (Tormenta20, pág. {pag}).\n"
        f"{' | '.join(header_parts)}.\n"
        f"Efeito Mecânico: {desc}"
    )

    return {
        "titulo": nome,
        "secao": f"{SEC_BASE} > {nome}",
        "pagina": pag,
        "texto": txt,
        "tipo": "condicao",
        "nome": nome,
        "tipo_efeito": tipo_efeito,
        "piora_para": piora,
    }


def chunk_regra_geral(regra):
    """Gera chunk para a regra geral de condições."""
    return {
        "titulo": regra.get("titulo", "Regras Gerais de Condições (Acúmulo, Duração e Tipos de Efeito)"),
        "secao": f"{SEC_BASE} > Regras Gerais",
        "pagina": regra.get("pagina", 400),
        "texto": f"{regra.get('titulo', 'Regras Gerais de Condições')} (Tormenta20, pág. {regra.get('pagina', 400)}).\n{regra.get('texto', '')}",
        "tipo": "condicao_regra",
    }


def chunk_lista_todas(condicoes):
    """Gera chunk-lista com visão ampla de todas as 35 condições agrupadas por tipo de efeito."""
    grupos = {}
    for c in condicoes:
        t = c.get("tipo_efeito", "Geral")
        grupos.setdefault(t, []).append(c)

    linhas = [
        "Lista de Todas as 35 Condições de Tormenta20 (Edição Jogo do Ano, págs. 400–401):",
        "• Condições com os mesmos efeitos não se acumulam; condições duram até o fim da cena a menos que especificado.",
        "",
    ]

    for tipo, lista in sorted(grupos.items()):
        nomes = []
        for c in lista:
            if c.get("piora_para"):
                nomes.append(f"{c['nome']} (escalamento: piora para {c['piora_para']})")
            else:
                nomes.append(c["nome"])
        linhas.append(f"• Tipo {tipo} ({len(lista)}): {', '.join(nomes)}.")

    return {
        "titulo": "Lista de Todas as Condições de Tormenta20",
        "secao": f"{SEC_BASE} > Lista Completa",
        "pagina": 400,
        "texto": "\n".join(linhas),
        "tipo": "condicao_lista",
        "categoria_filtro": "todas",
    }


def gerar_chunks_condicoes():
    """Lê dados/condicoes.json e retorna a lista de 37 chunks estruturados."""
    data = json.loads(CONDICOES_JSON.read_text(encoding="utf-8"))
    condicoes = data.get("condicoes", [])
    regra_geral = data.get("regra_geral", {})

    novos = []
    # 1. Chunks individuais (35)
    for c in condicoes:
        novos.append(chunk_condicao(c))

    # 2. Chunk de regra geral (1)
    if regra_geral:
        novos.append(chunk_regra_geral(regra_geral))

    # 3. Chunk lista agregada (1)
    novos.append(chunk_lista_todas(condicoes))

    return novos


def eh_chunk_condicoes_antigo(c):
    """Identifica chunks antigos do Apêndice: Lista de Condições a remover."""
    sec = c.get("secao", "")
    tipo = c.get("tipo", "")
    
    # Chunks estruturados anteriores de condição (idempotência)
    if tipo in ["condicao", "condicao_lista", "condicao_regra"]:
        return True
    if sec.startswith("Apêndice: Lista de Condições"):
        return True
        
    # Chunks antigos de texto corrido da ingestão base
    if sec == "Apêndice: Lista de Condições" or "Lista de Condições" in sec:
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
        if eh_chunk_condicoes_antigo(c):
            removidos_count += 1
        else:
            manter_indices.append(i)
            chunks_mantidos.append(c)

    print(f"      Removendo {removidos_count} chunks antigos do Apêndice: Lista de Condições")

    # 4. Gera novos chunks de condições
    novos_chunks = gerar_chunks_condicoes()
    print(f"[3/5] {len(novos_chunks)} chunks estruturados de condições gerados (35 condições, 1 regra, 1 lista agregada).")
    print(f"      Reconstruindo vetores das outras famílias...")

    # 5. Reconstrói vetores mantidos
    if manter_indices:
        vecs_mantidos = np.empty((len(manter_indices), dim), dtype="float32")
        for pos_nova, pos_antiga in enumerate(manter_indices):
            vecs_mantidos[pos_nova] = idx_faiss.reconstruct(int(pos_antiga))
    else:
        vecs_mantidos = np.empty((0, dim), dtype="float32")

    # 6. Embutir apenas os 37 novos chunks
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
    meta["condicoes_estruturadas"] = 35
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = time.time() - t0
    print(f"[5/5] SUCESSO — Índice: {n_antes} -> {len(todos_chunks)} chunks (-{removidos_count} antigos, +{len(novos_chunks)} novos estruturados).")
    print(f"      Tempo total: {dt:.1f}s. Backup em {backup_dir.name}\\")


if __name__ == "__main__":
    integrar()
