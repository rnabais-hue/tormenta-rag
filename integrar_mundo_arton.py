# -*- coding: utf-8 -*-
r"""Integração ESTRUTURADA do Capítulo 9: O Mundo de Arton (págs 364–397) ao índice FAISS.

Substitui os 113 chunks antigos de texto corrido do Capítulo 9 por 34 chunks estruturados de alta densidade:
  - 30 chunks individuais de reinos, potências, ilhas, ermos e locais lendários.
  - 1 lista consolidada dos Reinos do Reinado.
  - 1 lista consolidada das Grandes Potências.
  - 1 lista consolidada das Terras Além do Reinado.
  - 1 consolidado da Linha do Tempo e Marcos Históricos de Arton.

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
DADOS_JSON = BASE / "dados" / "mundo_arton.json"
INDEX_DIR = BASE / "index"
FAISS_PATH = INDEX_DIR / "tormenta.faiss"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
META_PATH = INDEX_DIR / "meta.json"

MODELO_EMBED = "BAAI/bge-m3"
os.environ.setdefault("HF_HOME", r"C:\LLM-Local\models")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def gerar_chunks_estruturados():
    banco = json.loads(DADOS_JSON.read_text(encoding="utf-8"))
    novos = []

    # 1. Chunks individuais por Reino / Região
    for r in banco["regioes"]:
        divs = ", ".join(r["divindades_principais"])
        locais = " • ".join(r["locais_destaque"])
        texto = (
            f"REINO / REGIÃO DE ARTON: {r['nome'].upper()} ({r['titulo_descritivo']})\n"
            f"• Categoria: {r['tipo_regiao']}\n"
            f"• Capital / Sede: {r['capital']}\n"
            f"• Regente / Líder: {r['regente_lider']}\n"
            f"• Divindades Principais: {divs}\n"
            f"• Pontos de Interesse: {locais}\n"
            f"• Cultura e Sociedade: {r['cultura_sociedade']}\n"
            f"• Ganchos de Aventura: {r['ganchos_aventura']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 9: O Mundo de Arton, pág. {r['pagina']})"
        )
        novos.append({
            "id": f"regra_reino_{r['id']}",
            "tipo": "mundo_arton",
            "categoria_regiao": r["tipo_regiao"],
            "nome_reino": r["nome"],
            "capital": r["capital"],
            "regente": r["regente_lider"],
            "titulo": f"{r['nome']} ({r['titulo_descritivo']})",
            "secao": f"Capítulo 9: O Mundo de Arton > {r['tipo_regiao']} > {r['nome']}",
            "pagina": r["pagina"],
            "texto": texto,
        })

    # 2. Lista Consolidada dos Reinos do Reinado
    reinos_reinado = [r for r in banco["regioes"] if r["tipo_regiao"] == "Reino do Reinado"]
    txt_reinado = (
        "LISTA CONSOLIDADA: OS REINOS DO REINADO DE ARTON\n"
        "O Reinado é a maior confederação civilizada de Arton, liderada pela Rainha-Imperatriz Shivara Sharpblade em Valkaria:\n\n"
    )
    for r in reinos_reinado:
        txt_reinado += (
            f"• {r['nome'].upper()} ({r['titulo_descritivo']}): Capital {r['capital']} | Regente: {r['regente_lider']} | Deuses: {', '.join(r['divindades_principais'])}\n"
            f"  Resumo: {r['cultura_sociedade'][:180]}...\n\n"
        )
    novos.append({
        "id": "mundo_arton_lista_reinos_reinado",
        "tipo": "mundo_arton_lista",
        "categoria_regiao": "Reino do Reinado",
        "titulo": "Lista de Reinos do Reinado de Arton",
        "secao": "Capítulo 9: O Mundo de Arton > O Reinado",
        "pagina": 364,
        "texto": txt_reinado.strip(),
    })

    # 3. Lista Consolidada das Grandes Potências
    potencias = [r for r in banco["regioes"] if r["tipo_regiao"] == "Grande Potência"]
    txt_potencias = (
        "LISTA CONSOLIDADA: AS GRANDES POTÊNCIAS E NAÇÕES RIVAIS DE ARTON\n\n"
    )
    for p in potencias:
        txt_potencias += (
            f"• {p['nome'].upper()}: Sede {p['capital']} | Líder: {p['regente_lider']} | Deuses: {', '.join(p['divindades_principais'])}\n"
            f"  Descrição: {p['cultura_sociedade']}\n\n"
        )
    novos.append({
        "id": "mundo_arton_lista_potencias",
        "tipo": "mundo_arton_lista",
        "categoria_regiao": "Grande Potência",
        "titulo": "Lista de Grandes Potências e Nações Beligerantes de Arton",
        "secao": "Capítulo 9: O Mundo de Arton > Grandes Potências",
        "pagina": 376,
        "texto": txt_potencias.strip(),
    })

    # 4. Lista Consolidada de Terras Além do Reinado
    alem = [r for r in banco["regioes"] if r["tipo_regiao"] in ["Além do Reinado", "Ermos e Montanhas", "Ilhas e Mares"]]
    txt_alem = (
        "LISTA CONSOLIDADA: TERRAS ALÉM DO REINADO, ERMOS E ILHAS DE ARTON\n\n"
    )
    for a in alem:
        txt_alem += f"• {a['nome'].upper()} ({a['tipo_regiao']}): Capital {a['capital']} | Líder: {a['regente_lider']} | {a['cultura_sociedade'][:140]}...\n"
    novos.append({
        "id": "mundo_arton_lista_alem_reinado",
        "tipo": "mundo_arton_lista",
        "categoria_regiao": "Além do Reinado",
        "titulo": "Lista de Regiões Além do Reinado, Ermos e Ilhas de Arton",
        "secao": "Capítulo 9: O Mundo de Arton > Além do Reinado",
        "pagina": 376,
        "texto": txt_alem.strip(),
    })

    # 5. Linha do Tempo e Marcos Históricos
    timeline_linhas = "\n".join([f"• Ano {m['ano']}: {m['evento']}" for m in banco["linha_do_tempo"]])
    txt_timeline = (
        "LINHA DO TEMPO E MARCOS HISTÓRICOS DE ARTON (CRONOLOGIA OFICIAL)\n\n"
        f"{timeline_linhas}\n\n"
        "(Fonte: Tormenta20 Jogo do Ano, Cap. 9: O Mundo de Arton, págs. 364–397)"
    )
    novos.append({
        "id": "mundo_arton_linha_do_tempo",
        "tipo": "mundo_arton_historia",
        "titulo": "Linha do Tempo e História do Mundo de Arton",
        "secao": "Capítulo 9: O Mundo de Arton > Linha do Tempo",
        "pagina": 364,
        "texto": txt_timeline,
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

    # Remove chunks antigos do Cap. 9: O Mundo de Arton (págs 364 a 397)
    manter_indices = []
    chunks_mantidos = []
    antigos_cap9 = 0
    for i, c in enumerate(chunks_atuais):
        sec = c.get("secao", "")
        p = c.get("pagina", 0)
        tp = c.get("tipo", "")
        # Chunks do Cap. 9
        eh_cap9_antigo = (
            (364 <= p <= 397 or "Capítulo 9" in sec or "Mundo de Arton" in sec)
            and tp in ["", None, "texto_corrido", "mundo_arton", "mundo_arton_lista", "mundo_arton_historia"]
        )
        if eh_cap9_antigo:
            antigos_cap9 += 1
        else:
            manter_indices.append(i)
            chunks_mantidos.append(c)

    print(f"      Removendo {antigos_cap9} chunks antigos do Capítulo 9: O Mundo de Arton")

    novos_chunks = gerar_chunks_estruturados()
    print(f"[3/5] {len(novos_chunks)} chunks estruturados do Mundo de Arton gerados.")
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
    meta["mundo_arton_estruturado"] = len(novos_chunks)
    meta["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = time.perf_counter() - t0
    print(
        f"[5/5] SUCESSO — Índice: {len(chunks_atuais)} -> {len(todos_chunks)} chunks "
        f"(-{antigos_cap9} antigos, +{len(novos_chunks)} novos estruturados)."
    )
    print(f"      Tempo total: {dt:.1f}s. Backup em {backup_dir.name}\\")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    integrar()


if __name__ == "__main__":
    main()
