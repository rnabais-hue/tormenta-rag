# -*- coding: utf-8 -*-
r"""
Integra a família MAGIA estruturada (dados/magias.json) ao índice FAISS.

Granularidade:
  - 1 chunk fino por MAGIA (198 chunks) com stat block verbalizado + descrição completa + aprimoramentos
  - 16 chunks-LISTA agregados (8 por escola, 5 por círculo, 3 por tipo) para consultas de listagem
  - 5 chunks PROCEDURAIS de regras de magia (págs 174–179: Classificação, Aprendizado, Lançamento/Custos, Características, Contramágica)

Substitui os 135 chunks antigos de texto corrido do Capítulo 4: Magia (págs 174–217).
Reconstrói o índice SEM reembutir as outras famílias (só os novos chunks, ~60-120s na CPU).

Idempotente (remove chunks de magia anteriores antes de reinserir).
Uso: python integrar_magias.py
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
MAGIAS_JSON = BASE / "dados" / "magias.json"
SEC_BASE = "Capítulo 4: Magia"


def chunk_magia(m):
    """Gera chunk individual fino para uma magia."""
    tipo_str = m.get("tipo", "arcana").capitalize()
    circ_str = f"{m.get('circulo', 1)}º Círculo"
    pm_str = f"Custo: {m.get('custo_pm', 1)} PM"
    
    txt_lines = [
        f"Magia: {m['nome']} (Tormenta20, pág. {m['pagina']}).",
        f"Tipo: {tipo_str} | Círculo: {circ_str} ({pm_str}) | Escola: {m.get('escola', '')}.",
    ]
    
    # Linha de stat block
    stats = []
    if m.get("execucao"):
        stats.append(f"Execução: {m['execucao']}")
    if m.get("alcance"):
        stats.append(f"Alcance: {m['alcance']}")
    if m.get("alvo"):
        alvo_rotulo = m.get("alvo_tipo") or "Alvo"
        stats.append(f"{alvo_rotulo}: {m['alvo']}")
    if m.get("duracao"):
        stats.append(f"Duração: {m['duracao']}")
    if m.get("resistencia"):
        stats.append(f"Resistência: {m['resistencia']}")
        
    if stats:
        txt_lines.append(" | ".join(stats) + ".")
        
    if m.get("descricao"):
        txt_lines.append(f"Descrição: {m['descricao']}")
        
    if m.get("aprimoramentos"):
        txt_lines.append("Aprimoramentos:")
        for a in m["aprimoramentos"]:
            txt_lines.append(f"• {a['custo']}: {a['efeito']}")

    return {
        "titulo": m["nome"],
        "secao": f"{SEC_BASE} > Descrição das Magias > {m.get('escola', 'Geral')} > {m['nome']}",
        "pagina": m["pagina"],
        "texto": "\n".join(txt_lines),
        "tipo": "magia",
        "nome": m["nome"],
        "magia_tipo": m.get("tipo"),
        "circulo": m.get("circulo"),
        "custo_pm": m.get("custo_pm"),
        "escola": m.get("escola"),
        "execucao": m.get("execucao"),
        "alcance": m.get("alcance"),
        "duracao": m.get("duracao"),
        "resistencia": m.get("resistencia"),
    }


def chunk_regra(r):
    """Gera chunk para regra procedural de magia."""
    return {
        "titulo": r["titulo"],
        "secao": f"{SEC_BASE} > Regras > {r['titulo']}",
        "pagina": r["pagina"],
        "texto": f"{r['titulo']} (Tormenta20, pág. {r['pagina']}).\n{r['texto']}",
        "tipo": "regra_magia",
        "resumo": r.get("resumo", ""),
    }


def gerar_listas_agregadas(magias):
    """Gera chunks de listas agregadas por escola, por círculo e por tipo."""
    chunks_listas = []
    
    # 1. Por Escola (8 escolas)
    escolas = sorted({m["escola"] for m in magias if m.get("escola")})
    for esc in escolas:
        sub = [m for m in magias if m.get("escola") == esc]
        sub = sorted(sub, key=lambda x: (x["circulo"], x["nome"]))
        linhas = [f"Lista de Magias da Escola de {esc} ({len(sub)} magias no livro Tormenta20):"]
        for m in sub:
            res_txt = f" (Resistência: {m['resistencia']})" if m.get("resistencia") else ""
            linhas.append(
                f"• {m['nome']} — {m['circulo']}º Círculo ({m['tipo'].capitalize()}, {m['custo_pm']} PM) "
                f"[Execução: {m['execucao']} | Alcance: {m['alcance']} | Duração: {m['duracao']}{res_txt}]: "
                f"{m['descricao'][:120]}…"
            )
        chunks_listas.append({
            "titulo": f"Lista de Magias de {esc}",
            "secao": f"{SEC_BASE} > Listas de Magias > Escola {esc}",
            "pagina": 180,
            "texto": "\n".join(linhas),
            "tipo": "magia_lista",
            "categoria_filtro": "escola",
            "escola": esc,
            "total_itens": len(sub),
        })

    # 2. Por Círculo (1º ao 5º)
    for circ in range(1, 6):
        sub = [m for m in magias if m.get("circulo") == circ]
        sub = sorted(sub, key=lambda x: (x["escola"], x["nome"]))
        linhas = [f"Lista de Magias de {circ}º Círculo ({len(sub)} magias, Custo Base: {sub[0]['custo_pm'] if sub else 1} PM):"]
        for m in sub:
            linhas.append(
                f"• {m['nome']} ({m['escola']}, {m['tipo'].capitalize()}): "
                f"{m['execucao']} | {m['alcance']} | {m['duracao']} | {m['descricao'][:100]}…"
            )
        chunks_listas.append({
            "titulo": f"Lista de Magias de {circ}º Círculo",
            "secao": f"{SEC_BASE} > Listas de Magias > {circ}º Círculo",
            "pagina": 180,
            "texto": "\n".join(linhas),
            "tipo": "magia_lista",
            "categoria_filtro": "circulo",
            "circulo": circ,
            "total_itens": len(sub),
        })

    # 3. Por Tipo (Arcana, Divina, Universal)
    for t_nome in ["arcana", "divina", "universal"]:
        sub = [m for m in magias if m.get("tipo") == t_nome]
        sub = sorted(sub, key=lambda x: (x["circulo"], x["nome"]))
        linhas = [f"Lista de Magias {t_nome.capitalize()}s ({len(sub)} magias em Tormenta20):"]
        for m in sub:
            linhas.append(f"• {m['nome']} ({m['circulo']}º Círculo, {m['escola']}): {m['descricao'][:90]}…")
        chunks_listas.append({
            "titulo": f"Lista de Magias {t_nome.capitalize()}s",
            "secao": f"{SEC_BASE} > Listas de Magias > {t_nome.capitalize()}s",
            "pagina": 180,
            "texto": "\n".join(linhas),
            "tipo": "magia_lista",
            "categoria_filtro": "tipo",
            "magia_tipo": t_nome,
            "total_itens": len(sub),
        })

    return chunks_listas


def montar_novos_chunks():
    data = json.loads(MAGIAS_JSON.read_text(encoding="utf-8"))
    magias = data.get("magias", [])
    regras = data.get("regras", [])
    
    novos = []
    for m in magias:
        novos.append(chunk_magia(m))
    for r in regras:
        novos.append(chunk_regra(r))
    novos.extend(gerar_listas_agregadas(magias))
    
    return novos, len(magias), len(regras)


def eh_chunk_capitulo4(c):
    """Identifica se o chunk pertence ao Capítulo 4: Magia (bruto antigo ou de integração prévia)."""
    sec = c.get("secao", "")
    tipo = c.get("tipo", "")
    
    # Chunks estruturados de magia
    if tipo in ["magia", "magia_lista", "regra_magia"]:
        return True
        
    # Chunks brutos originais do Capítulo 4 (págs 174 a 217)
    if sec.startswith("Capítulo 4: Magia") or sec.startswith("Capítulo 4") or re.match(r"^Cap[íi]tulo 4\b", sec):
        # Não remove outros capítulos
        return True
        
    return False


def main():
    t0 = time.time()
    
    # 1. Carrega dados do índice atual
    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    chunks_antigos = [
        json.loads(l)
        for l in (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    n_antigo = len(chunks_antigos)
    
    # 2. Backup de segurança
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = INDEX_DIR / f"backup-{ts}"
    backup_dir.mkdir(exist_ok=True)
    for f in ["meta.json", "chunks.jsonl", "tormenta.faiss"]:
        if (INDEX_DIR / f).exists():
            shutil.copy2(INDEX_DIR / f, backup_dir / f)
    print(f"[1/5] Backup do índice em backup-{ts}\\")
    
    # 3. Separa chunks que sobrevivem dos que serão substituídos
    indices_manter = []
    chunks_manter = []
    for i, c in enumerate(chunks_antigos):
        if not eh_chunk_capitulo4(c):
            indices_manter.append(i)
            chunks_manter.append(c)
            
    removidos = n_antigo - len(chunks_manter)
    print(f"[2/5] Índice atual: {n_antigo} chunks, dim {index.d}")
    print(f"      Removendo {removidos} chunks antigos do Capítulo 4: Magia")
    
    # 4. Gera novos chunks estruturados
    novos_chunks, n_magias, n_regras = montar_novos_chunks()
    print(f"[3/5] {len(novos_chunks)} chunks estruturados de magia gerados ({n_magias} magias, {n_regras} regras, {len(novos_chunks) - n_magias - n_regras} listas agregadas).")
    
    # 5. Reconstrói vetores dos chunks preservados
    if indices_manter:
        print("      Reconstruindo vetores das outras famílias...")
        vetores_manter = index.reconstruct_n(0, n_antigo)
        vetores_manter = vetores_manter[indices_manter]
    else:
        vetores_manter = np.empty((0, index.d), dtype="float32")
        
    # 6. Embutir apenas os novos chunks
    print(f"[4/5] Carregando embedder {meta['modelo_embed']} e embutindo {len(novos_chunks)} novos chunks...")
    t_emb = time.time()
    embedder = SentenceTransformer(meta["modelo_embed"])
    textos_novos = [c["texto"] for c in novos_chunks]
    vetores_novos = embedder.encode(
        textos_novos,
        batch_size=8,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")
    print(f"      {len(novos_chunks)} vetores embutidos em {time.time() - t_emb:.1f}s")
    
    # 7. Concatena e cria novo índice FAISS
    if len(vetores_manter) > 0:
        todos_vetores = np.vstack([vetores_manter, vetores_novos])
    else:
        todos_vetores = vetores_novos
        
    novo_index = faiss.IndexFlatIP(index.d)
    novo_index.add(todos_vetores)
    
    # 8. Reatribui IDs ordenados e salva
    todos_chunks = chunks_manter + novos_chunks
    for novo_id, c in enumerate(todos_chunks):
        c["id"] = novo_id
        
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))
    with open(INDEX_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in todos_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
            
    meta["n_chunks"] = len(todos_chunks)
    meta["magias_estruturadas"] = n_magias
    meta["atualizado_em"] = ts
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    
    print(f"[5/5] SUCESSO — Índice: {n_antigo} -> {len(todos_chunks)} chunks (-{removidos} antigos, +{len(novos_chunks)} novos estruturados).")
    print(f"      Tempo total: {time.time() - t0:.1f}s. Backup em backup-{ts}\\")


if __name__ == "__main__":
    main()
