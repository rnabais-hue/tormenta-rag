# -*- coding: utf-8 -*-
r"""Integração ESTRUTURADA do Capítulo 1 (14 Fichas de Classes) e Capítulo 6 (O Mestre) ao índice FAISS.

Substitui os 243 chunks antigos de texto corrido dos Capítulos 1 e 6 por 22 chunks estruturados de alta densidade:
  - 14 Fichas Completas de Classes (PV, PM, proficiências, perícias, habilidades e progressão 1º–20º).
  - 1 Lista Consolidada das 14 Classes.
  - 6 Módulos de Regras do Mestre (Queda, Afogamento, Fogo/Clima, Armadilhas/Perigos, Doenças/Venenos, Campanhas).
  - 1 Resumo Consolidado de Ambientes e Perigos.

Reconstrói em memória os vetores das outras famílias (zero re-embutimento do restante).
"""
import io
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
DADOS_JSON = BASE / "dados" / "mestre_classes.json"
INDEX_DIR = BASE / "index"
FAISS_PATH = INDEX_DIR / "tormenta.faiss"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
META_PATH = INDEX_DIR / "meta.json"

MODELO_EMBED = "BAAI/bge-m3"
os.environ["HF_HOME"] = r"C:\LLM-Local\models"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


def gerar_chunks_estruturados():
    banco = json.loads(DADOS_JSON.read_text(encoding="utf-8"))
    novos = []

    # 1. As 14 Fichas de Classes
    for c in banco["classes"]:
        habs = "\n  - ".join(c["habilidades_principais"])
        texto = (
            f"FICHA COMPLETA DA CLASSE: {c['nome'].upper()} ({c['caminhos']})\n"
            f"• Pontos de Vida (PV): Inicial {c['pv_inicial']} | Por nível: {c['pv_por_nivel']}\n"
            f"• Pontos de Mana (PM): Inicial {c['pm_inicial']} | Por nível: {c['pm_por_nivel']}\n"
            f"• Proficiências: {c['proficiencias']}\n"
            f"• Perícias Básicas: {c['pericias_basicas']}\n"
            f"• Habilidades Automáticas de Classe:\n  - {habs}\n"
            f"• Tabela de Progressão Nível a Nível (1º ao 20º):\n  {c['progressao_tabela']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 1: Construção de Personagem, pág. {c['pagina']})"
        )
        novos.append({
            "id": f"classe_{c['id']}",
            "tipo": "classe_ficha",
            "categoria": "classe",
            "nome_classe": c["nome"],
            "titulo": f"Ficha de Classe: {c['nome']}",
            "secao": f"Capítulo 1: Construção de Personagem > Classes > {c['nome']}",
            "pagina": c["pagina"],
            "texto": texto,
        })

    # 2. Lista Consolidada das 14 Classes
    txt_lista_classes = (
        "LISTA CONSOLIDADA: AS 14 CLASSES DE TORMENTA20\n\n"
    )
    for c in banco["classes"]:
        txt_lista_classes += (
            f"• {c['nome'].upper()} ({c['caminhos']}): PV {c['pv_inicial']} (+{c['pv_por_nivel']}) | PM {c['pm_inicial']} (+{c['pm_por_nivel']}) | Prof: {c['proficiencias']}\n"
        )
    novos.append({
        "id": "classes_lista_todas",
        "tipo": "classe_lista",
        "categoria": "classe",
        "titulo": "Lista de Todas as 14 Classes de Tormenta20",
        "secao": "Capítulo 1: Construção de Personagem > Classes",
        "pagina": 36,
        "texto": txt_lista_classes.strip(),
    })

    # 3. Regras do Mestre (Individuais)
    for m in banco["mestre_regras"]:
        novos.append({
            "id": f"mestre_{m['id']}",
            "tipo": "mestre_regra",
            "categoria_mestre": m["categoria"],
            "nome_regra": m["nome"],
            "titulo": m["nome"],
            "secao": f"Capítulo 6: O Mestre > {m['categoria'].title()} > {m['nome']}",
            "pagina": m["pagina"],
            "texto": m["texto"],
        })

    # 4. Resumo Consolidado de Ambientes e Perigos
    txt_ambientes = (
        "RESUMO CONSOLIDADO: AMBIENTES, PERIGOS, QUEDA E CLIMA DE TORMENTA20\n"
        "Regras fundamentais de exploração do Capítulo 6 (O Mestre):\n\n"
    )
    for m in banco["mestre_regras"]:
        txt_ambientes += f"• {m['nome'].upper()}:\n{m['texto']}\n\n"
    novos.append({
        "id": "mestre_resumo_ambientes_perigos",
        "tipo": "mestre_lista",
        "categoria_mestre": "resumo_geral",
        "titulo": "Resumo de Ambientes, Perigos e Regras do Mestre",
        "secao": "Capítulo 6: O Mestre > Regras de Exploração",
        "pagina": 270,
        "texto": txt_ambientes.strip(),
    })

    return novos


def integrar():
    t0 = time.perf_counter()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = INDEX_DIR / f"backup-{ts}"
    shutil.copytree(INDEX_DIR, backup_dir, ignore=shutil.ignore_patterns("backup-*"))
    print(f"[1/5] Backup do índice em {backup_dir.name}\\")

    # Lê índice e chunks atuais
    index = faiss.read_index(str(FAISS_PATH))
    chunks_atuais = [
        json.loads(line)
        for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    meta = json.loads(META_PATH.read_text(encoding="utf-8")) if META_PATH.exists() else {}
    print(f"[2/5] Índice atual: {len(chunks_atuais)} chunks, dim {index.d}")

    # Remove chunks antigos do Cap. 1 (classes e texto corrido) e Cap. 6 (mestre texto corrido)
    manter_indices = []
    chunks_mantidos = []
    removidos_cap1 = 0
    removidos_cap6 = 0

    for i, c in enumerate(chunks_atuais):
        sec = c.get("secao", "")
        p = c.get("pagina", 0)
        tp = c.get("tipo", "")
        
        eh_cap1_antigo = (p <= 88 and tp in ["", None, "texto_corrido", "classe", "classe_ficha", "classe_lista"])
        eh_cap6_antigo = (246 <= p <= 287 and tp in ["", None, "texto_corrido", "mestre_regra", "mestre_lista"])
        
        if eh_cap1_antigo:
            removidos_cap1 += 1
        elif eh_cap6_antigo:
            removidos_cap6 += 1
        else:
            manter_indices.append(i)
            chunks_mantidos.append(c)

    print(f"      Removendo {removidos_cap1} chunks antigos do Capítulo 1 (Classes e Texto)")
    print(f"      Removendo {removidos_cap6} chunks antigos do Capítulo 6 (O Mestre)")

    novos_chunks = gerar_chunks_estruturados()
    print(f"[3/5] {len(novos_chunks)} chunks estruturados de Classes e Mestre gerados.")
    print("      Reconstruindo vetores das outras famílias...")

    # Reconstrói vetores mantidos
    vecs_mantidos = np.empty((len(manter_indices), index.d), dtype="float32")
    for new_idx, old_idx in enumerate(manter_indices):
        vecs_mantidos[new_idx] = index.reconstruct(int(old_idx))

    # Embuti apenas os novos chunks
    print(f"[4/5] Carregando embedder {MODELO_EMBED} e embutindo {len(novos_chunks)} novos chunks...")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    model = SentenceTransformer(MODELO_EMBED, local_files_only=True)
    novos_textos = [c["texto"] for c in novos_chunks]
    novos_vecs = model.encode(
        novos_textos,
        batch_size=8,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).astype("float32")

    # Combina
    todos_vecs = np.vstack([vecs_mantidos, novos_vecs])
    todos_chunks = chunks_mantidos + novos_chunks

    # Reconstrói índice FAISS
    novo_index = faiss.IndexFlatIP(index.d)
    novo_index.add(todos_vecs)
    faiss.write_index(novo_index, str(FAISS_PATH))

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in todos_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    meta["n_chunks"] = len(todos_chunks)
    meta["classes_estruturadas"] = 15
    meta["mestre_estruturado"] = 7
    meta["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = time.perf_counter() - t0
    print(
        f"[5/5] SUCESSO — Índice: {len(chunks_atuais)} -> {len(todos_chunks)} chunks "
        f"(-{removidos_cap1 + removidos_cap6} antigos, +{len(novos_chunks)} novos estruturados)."
    )
    print(f"      Tempo total: {dt:.1f}s. Backup em {backup_dir.name}\\")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    integrar()


if __name__ == "__main__":
    main()
