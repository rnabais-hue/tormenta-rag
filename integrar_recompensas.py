# -*- coding: utf-8 -*-
r"""Integração ESTRUTURADA do Capítulo 8: Recompensas (págs 330–355) ao índice FAISS.

Substitui os 54 chunks antigos de texto corrido do Capítulo 8 por ~105 chunks estruturados de alta densidade:
  - Regras gerais de uso, fabricação, destruição e Tabela 8-1 (Tesouros por ND).
  - 29 Encantos de Armas + 1 Lista Consolidada.
  - 10 Armas Mágicas Específicas.
  - 24 Encantos de Armaduras/Escudos + 1 Lista Consolidada.
  - 8 Armaduras e Escudos Específicos.
  - 18 Acessórios Mágicos + 1 Lista Consolidada.
  - 7 Artefatos Supremos + 1 Lista Consolidada.

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
DADOS_JSON = BASE / "dados" / "recompensas.json"
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

    # 1. Regras Gerais & Tabelas
    for r in banco["regras_gerais"]:
        novos.append({
            "id": f"recompensa_{r['id']}",
            "tipo": "recompensa_regra",
            "categoria_recompensa": "regras_gerais",
            "nome_recompensa": r["nome"],
            "titulo": r["nome"],
            "secao": f"Capítulo 8: Recompensas > Regras Gerais > {r['nome']}",
            "pagina": r["pagina"],
            "texto": r["texto"],
        })

    # 2. Encantos de Armas (Individuais)
    for e in banco["encantos_armas"]:
        texto = (
            f"ENCANTO DE ARMA MÁGICA: {e['nome'].upper()}\n"
            f"• Preço / Bônus Equivalente: {e['preco_bonus']}\n"
            f"• Efeito: {e['efeito']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 8: Recompensas, pág. {e['pagina']})"
        )
        novos.append({
            "id": f"encanto_arma_{e['nome'].lower()}",
            "tipo": "encanto_arma",
            "categoria_recompensa": "encanto_arma",
            "nome_recompensa": e["nome"],
            "preco_bonus": e["preco_bonus"],
            "titulo": f"Encanto de Arma: {e['nome']}",
            "secao": f"Capítulo 8: Recompensas > Encantos de Armas > {e['nome']}",
            "pagina": e["pagina"],
            "texto": texto,
        })

    # 3. Lista Consolidada de Encantos de Armas
    txt_lista_armas = (
        "LISTA CONSOLIDADA: TODOS OS ENCANTOS DE ARMAS DE TORMENTA20\n"
        "Encantamentos mágicos disponíveis para armas corporais e de disparo:\n\n"
    )
    for e in banco["encantos_armas"]:
        txt_lista_armas += f"• {e['nome'].upper()} ({e['preco_bonus']}): {e['efeito']}\n"
    novos.append({
        "id": "recompensas_lista_encantos_armas",
        "tipo": "recompensa_lista",
        "categoria_recompensa": "encanto_arma",
        "titulo": "Lista de Encantos de Armas",
        "secao": "Capítulo 8: Recompensas > Encantos de Armas",
        "pagina": 341,
        "texto": txt_lista_armas.strip(),
    })

    # 4. Armas Específicas
    for a in banco["armas_especificas"]:
        texto = (
            f"ARMA MÁGICA ESPECÍFICA: {a['nome'].upper()}\n"
            f"• Tipo de Arma: {a['tipo']}\n"
            f"• Preço de Mercado: {a['preco']}\n"
            f"• Efeitos e Poderes: {a['efeito']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 8: Recompensas, pág. {a['pagina']})"
        )
        novos.append({
            "id": f"arma_especifica_{a['nome'].lower().replace(' ', '_')}",
            "tipo": "arma_especifica",
            "categoria_recompensa": "arma_especifica",
            "nome_recompensa": a["nome"],
            "tipo_item": a["tipo"],
            "preco": a["preco"],
            "titulo": f"Arma Específica: {a['nome']}",
            "secao": f"Capítulo 8: Recompensas > Armas Específicas > {a['nome']}",
            "pagina": a["pagina"],
            "texto": texto,
        })

    # 5. Encantos de Armaduras & Escudos (Individuais)
    for e in banco["encantos_armaduras"]:
        texto = (
            f"ENCANTO DE ARMADURA / ESCUDO: {e['nome'].upper()}\n"
            f"• Preço / Bônus Equivalente: {e['preco_bonus']}\n"
            f"• Efeito: {e['efeito']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 8: Recompensas, pág. {e['pagina']})"
        )
        novos.append({
            "id": f"encanto_armadura_{e['nome'].lower()}",
            "tipo": "encanto_armadura",
            "categoria_recompensa": "encanto_armadura",
            "nome_recompensa": e["nome"],
            "preco_bonus": e["preco_bonus"],
            "titulo": f"Encanto de Armadura: {e['nome']}",
            "secao": f"Capítulo 8: Recompensas > Encantos de Armaduras e Escudos > {e['nome']}",
            "pagina": e["pagina"],
            "texto": texto,
        })

    # 6. Lista Consolidada de Encantos de Armaduras
    txt_lista_armaduras = (
        "LISTA CONSOLIDADA: TODOS OS ENCANTOS DE ARMADURAS E ESCUDOS DE TORMENTA20\n"
        "Encantamentos mágicos de proteção para armaduras e escudos:\n\n"
    )
    for e in banco["encantos_armaduras"]:
        txt_lista_armaduras += f"• {e['nome'].upper()} ({e['preco_bonus']}): {e['efeito']}\n"
    novos.append({
        "id": "recompensas_lista_encantos_armaduras",
        "tipo": "recompensa_lista",
        "categoria_recompensa": "encanto_armadura",
        "titulo": "Lista de Encantos de Armaduras e Escudos",
        "secao": "Capítulo 8: Recompensas > Encantos de Armaduras e Escudos",
        "pagina": 344,
        "texto": txt_lista_armaduras.strip(),
    })

    # 7. Armaduras Específicas
    for a in banco["armaduras_especificas"]:
        texto = (
            f"ARMADURA / ESCUDO ESPECÍFICO: {a['nome'].upper()}\n"
            f"• Tipo: {a['tipo']}\n"
            f"• Preço de Mercado: {a['preco']}\n"
            f"• Efeitos e Poderes: {a['efeito']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 8: Recompensas, pág. {a['pagina']})"
        )
        novos.append({
            "id": f"armadura_especifica_{a['nome'].lower().replace(' ', '_')}",
            "tipo": "armadura_especifica",
            "categoria_recompensa": "armadura_especifica",
            "nome_recompensa": a["nome"],
            "tipo_item": a["tipo"],
            "preco": a["preco"],
            "titulo": f"Armadura Específica: {a['nome']}",
            "secao": f"Capítulo 8: Recompensas > Armaduras Específicas > {a['nome']}",
            "pagina": a["pagina"],
            "texto": texto,
        })

    # 8. Acessórios Mágicos (Individuais)
    for ac in banco["acessorios"]:
        texto = (
            f"ACESSÓRIO MÁGICO: {ac['nome'].upper()}\n"
            f"• Espaço Ocupado: {ac['espaco']}\n"
            f"• Preço de Mercado: {ac['preco']}\n"
            f"• Efeito: {ac['efeito']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 8: Recompensas, pág. {ac['pagina']})"
        )
        novos.append({
            "id": f"acessorio_{ac['nome'].lower().replace(' ', '_')}",
            "tipo": "acessorio",
            "categoria_recompensa": "acessorio",
            "nome_recompensa": ac["nome"],
            "espaco": ac["espaco"],
            "preco": ac["preco"],
            "titulo": f"Acessório Mágico: {ac['nome']}",
            "secao": f"Capítulo 8: Recompensas > Acessórios > {ac['nome']}",
            "pagina": ac["pagina"],
            "texto": texto,
        })

    # 9. Lista Consolidada de Acessórios
    txt_lista_acessorios = (
        "LISTA CONSOLIDADA: TODOS OS ACESSÓRIOS MÁGICOS DE TORMENTA20\n"
        "Itens mágicos vestidos em espaços de corpo (anéis, mantos, botas, cintos, tiaras, etc.):\n\n"
    )
    for ac in banco["acessorios"]:
        txt_lista_acessorios += f"• {ac['nome'].upper()} ({ac['espaco']} | {ac['preco']}): {ac['efeito']}\n"
    novos.append({
        "id": "recompensas_lista_acessorios",
        "tipo": "recompensa_lista",
        "categoria_recompensa": "acessorio",
        "titulo": "Lista de Acessórios Mágicos",
        "secao": "Capítulo 8: Recompensas > Acessórios",
        "pagina": 348,
        "texto": txt_lista_acessorios.strip(),
    })

    # 10. Artefatos Supremos (Individuais)
    for art in banco["artefatos"]:
        texto = (
            f"ARTEFATO SUPREMO: {art['nome'].upper()}\n"
            f"• Categoria: {art['tipo']}\n"
            f"• Poderes Épicos: {art['descricao_poderes']}\n"
            f"• Como Destruir: {art['destruicao']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 8: Recompensas, pág. {art['pagina']})"
        )
        novos.append({
            "id": f"artefato_{art['id']}",
            "tipo": "artefato",
            "categoria_recompensa": "artefato",
            "nome_recompensa": art["nome"],
            "tipo_item": art["tipo"],
            "titulo": f"Artefato: {art['nome']}",
            "secao": f"Capítulo 8: Recompensas > Artefatos > {art['nome']}",
            "pagina": art["pagina"],
            "texto": texto,
        })

    # 11. Lista Consolidada de Artefatos
    txt_lista_artefatos = (
        "LISTA CONSOLIDADA: OS ARTEFATOS LENDÁRIOS DE ARTON\n\n"
    )
    for art in banco["artefatos"]:
        txt_lista_artefatos += f"• {art['nome'].upper()}: {art['descricao_poderes'][:180]}...\n"
    novos.append({
        "id": "recompensas_lista_artefatos",
        "tipo": "recompensa_lista",
        "categoria_recompensa": "artefato",
        "titulo": "Lista de Artefatos Lendários de Arton",
        "secao": "Capítulo 8: Recompensas > Artefatos",
        "pagina": 352,
        "texto": txt_lista_artefatos.strip(),
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

    # Remove chunks antigos do Cap. 8: Recompensas (págs 330 a 355)
    manter_indices = []
    chunks_mantidos = []
    antigos_cap8 = 0
    for i, c in enumerate(chunks_atuais):
        sec = c.get("secao", "")
        p = c.get("pagina", 0)
        tp = c.get("tipo", "")
        eh_cap8_antigo = (
            (330 <= p <= 355 or "Capítulo 8" in sec or "Recompensas" in sec)
            and tp in ["", None, "texto_corrido", "recompensa_regra", "encanto_arma", "arma_especifica", "encanto_armadura", "armadura_especifica", "acessorio", "artefato", "recompensa_lista"]
        )
        if eh_cap8_antigo:
            antigos_cap8 += 1
        else:
            manter_indices.append(i)
            chunks_mantidos.append(c)

    print(f"      Removendo {antigos_cap8} chunks antigos do Capítulo 8: Recompensas")

    novos_chunks = gerar_chunks_estruturados()
    print(f"[3/5] {len(novos_chunks)} chunks estruturados de Recompensas gerados.")
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
    meta["recompensas_estruturadas"] = len(novos_chunks)
    meta["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = time.perf_counter() - t0
    print(
        f"[5/5] SUCESSO — Índice: {len(chunks_atuais)} -> {len(todos_chunks)} chunks "
        f"(-{antigos_cap8} antigos, +{len(novos_chunks)} novos estruturados)."
    )
    print(f"      Tempo total: {dt:.1f}s. Backup em {backup_dir.name}\\")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    integrar()


if __name__ == "__main__":
    main()
