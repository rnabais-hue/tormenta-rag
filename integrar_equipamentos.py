# -*- coding: utf-8 -*-
r"""
Integra a família EQUIPAMENTOS estruturada (dados/equipamentos.json) ao índice FAISS.

Granularidade:
  - 1 chunk fino por ARMA / MUNIÇÃO (~47 chunks) com stats de tabela + regras completas
  - 1 chunk fino por ARMADURA / ESCUDO (12 chunks) com defesa, penalidade, preço + regras
  - 1 chunk fino por ITEM GERAL (~121 chunks) com preço, espaços + efeito mecânico
  - 1 chunk fino por MELHORIA SUPERIOR (~29 chunks)
  - 1 chunk fino por MATERIAL ESPECIAL (6 chunks com regras e preços por tipo de item)
  - 4 chunks PROCEDURAIS (Riqueza/Moedas, Carga/Uso, Passos de Dano, Regras de Itens Superiores)
  - 16 chunks-LISTA por categoria para responder consultas de listagem com precisão.

Substitui os 64 chunks grossos de texto corrido do Capítulo 3 (págs 144–173).
Reconstrói o índice SEM reembutir as outras famílias (só os novos chunks, ~60s).

Idempotente (remove chunks de equipamento anteriores antes de reinserir).
Uso: python integrar_equipamentos.py
"""

import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
EQUIP_JSON = BASE / "dados" / "equipamentos.json"
SEC_BASE = "Capítulo 3: Equipamento"


def chunk_arma(a):
    is_mun = a.get("categoria") == "municao"
    txt_lines = [
        f"{'Munição' if is_mun else 'Arma'}: {a['nome']} (Tormenta20, pág. {a['pagina']}).",
        f"Proficiência: {a.get('proficiencia','')} | Empunhadura: {a.get('empunhadura','')} | Espaços: {a.get('espacos','1')} | Preço: {a.get('preco','—')}."
    ]
    if not is_mun:
        txt_lines.append(f"Dano: {a.get('dano','—')} | Crítico: {a.get('critico','—')} | Alcance: {a.get('alcance','—')} | Tipo de Dano: {a.get('tipo_dano','—')}.")
    if a.get("descricao"):
        txt_lines.append(f"Descrição e Regras: {a['descricao']}")

    return {
        "titulo": a["nome"],
        "secao": f"{SEC_BASE} > Armas > {a.get('proficiencia','Geral')} > {a['nome']}",
        "pagina": a["pagina"],
        "texto": "\n".join(txt_lines),
        "tipo": "equipamento",
        "categoria": a.get("categoria", "arma"),
        "nome": a["nome"],
        "proficiencia": a.get("proficiencia"),
        "empunhadura": a.get("empunhadura"),
        "preco": a.get("preco"),
        "dano": a.get("dano"),
        "critico": a.get("critico"),
        "alcance": a.get("alcance"),
        "tipo_dano": a.get("tipo_dano"),
        "espacos": a.get("espacos")
    }


def chunk_armadura(ar):
    txt_lines = [
        f"{ar.get('subcategoria','Armadura')}: {ar['nome']} (Tormenta20, pág. {ar['pagina']}).",
        f"Preço: {ar.get('preco','—')} | Bônus na Defesa: {ar.get('defesa','—')} | Penalidade de Armadura: {ar.get('penalidade','0')} | Espaços: {ar.get('espacos','2')}."
    ]
    if ar.get("descricao"):
        txt_lines.append(f"Descrição e Regras: {ar['descricao']}")

    return {
        "titulo": ar["nome"],
        "secao": f"{SEC_BASE} > Armaduras & Escudos > {ar.get('subcategoria','Geral')} > {ar['nome']}",
        "pagina": ar["pagina"],
        "texto": "\n".join(txt_lines),
        "tipo": "equipamento",
        "categoria": ar.get("categoria", "armadura"),
        "subcategoria": ar.get("subcategoria"),
        "nome": ar["nome"],
        "defesa": ar.get("defesa"),
        "penalidade": ar.get("penalidade"),
        "preco": ar.get("preco"),
        "espacos": ar.get("espacos")
    }


def chunk_item_geral(g):
    txt_lines = [
        f"Item Geral ({g.get('subcategoria','Geral')}): {g['nome']} (Tormenta20, pág. {g['pagina']}).",
        f"Preço: {g.get('preco','—')} | Espaços: {g.get('espacos','—')}."
    ]
    if g.get("descricao"):
        txt_lines.append(f"Efeito e Regras: {g['descricao']}")

    return {
        "titulo": g["nome"],
        "secao": f"{SEC_BASE} > Itens Gerais > {g.get('subcategoria','Geral')} > {g['nome']}",
        "pagina": g["pagina"],
        "texto": "\n".join(txt_lines),
        "tipo": "equipamento",
        "categoria": "item_geral",
        "subcategoria": g.get("subcategoria"),
        "nome": g["nome"],
        "preco": g.get("preco"),
        "espacos": g.get("espacos")
    }


def chunk_melhoria(m):
    txt_lines = [
        f"Melhoria de Item Superior: {m['nome']} (Tormenta20, pág. {m['pagina']}).",
        f"Aplica-se a: {m.get('aplica_a','Geral')}."
    ]
    desc = m.get("descricao_completa") or m.get("efeito_resumido")
    if desc:
        txt_lines.append(f"Efeito Mecânico: {desc}")

    return {
        "titulo": m["nome"],
        "secao": f"{SEC_BASE} > Itens Superiores > Melhorias > {m['nome']}",
        "pagina": m["pagina"],
        "texto": "\n".join(txt_lines),
        "tipo": "melhoria_superior",
        "nome": m["nome"],
        "aplica_a": m.get("aplica_a")
    }


def chunk_material(mat):
    txt_lines = [
        f"Material Especial Superior: {mat['nome']} (Tormenta20, pág. {mat['pagina']}).",
        f"Descrição: {mat.get('descricao','')}",
        f"Em Armas: {mat.get('efeito_arma','—')} (Preço: {mat.get('precos',{}).get('arma','—')})",
        f"Em Armaduras e Escudos: {mat.get('efeito_armadura_escudo','—')} (Preço Leve/Escudo: {mat.get('precos',{}).get('armadura_leve','—')}, Pesada: {mat.get('precos',{}).get('armadura_pesada','—')})",
        f"Em Esotéricos: {mat.get('efeito_esoterico','—')} (Preço: {mat.get('precos',{}).get('esoterico','—')})"
    ]

    return {
        "titulo": mat["nome"],
        "secao": f"{SEC_BASE} > Itens Superiores > Materiais Especiais > {mat['nome']}",
        "pagina": mat["pagina"],
        "texto": "\n".join(txt_lines),
        "tipo": "material_especial",
        "nome": mat["nome"]
    }


def chunk_regra(r):
    return {
        "titulo": r["titulo"],
        "secao": f"{SEC_BASE} > Regras > {r['titulo']}",
        "pagina": r["pagina"],
        "texto": f"{r['titulo']} (Tormenta20, pág. {r['pagina']}).\n{r['texto']}",
        "tipo": "regra_equipamento",
        "titulo_regra": r["titulo"]
    }


def gerar_chunks_lista(dados):
    """Gera chunks de visão agregada (listas por categoria) para consultas de listagem."""
    listas = []
    
    # 1. Armas por Proficiência
    for prof in ["Simples", "Marcial", "Exótica", "Fogo"]:
        armas_prof = [a for a in dados.get("armas", []) if a.get("proficiencia") == prof and a.get("categoria") == "arma"]
        if armas_prof:
            itens_str = ", ".join(f"{a['nome']} (Dano {a.get('dano','—')}, Crítico {a.get('critico','—')}, {a.get('preco','—')})" for a in armas_prof)
            listas.append({
                "titulo": f"Lista de Armas {prof}s",
                "secao": f"{SEC_BASE} > Armas > Lista {prof}s",
                "pagina": 150,
                "texto": f"Lista de Armas {prof}s em Tormenta20 (Tabela 3-3, pág. 150-151):\n{itens_str}.",
                "tipo": "equipamento_lista",
                "categoria": "arma",
                "proficiencia": prof
            })

    # 2. Armaduras & Escudos por Subcategoria
    for subcat in ["Armaduras Leves", "Armaduras Pesadas", "Escudos"]:
        armad_sub = [ar for ar in dados.get("armaduras_escudos", []) if ar.get("subcategoria") == subcat]
        if armad_sub:
            itens_str = ", ".join(f"{ar['nome']} (Defesa {ar.get('defesa','—')}, Penalidade {ar.get('penalidade','0')}, {ar.get('preco','—')})" for ar in armad_sub)
            listas.append({
                "titulo": f"Lista de {subcat}",
                "secao": f"{SEC_BASE} > Armaduras & Escudos > Lista {subcat}",
                "pagina": 159,
                "texto": f"Lista de {subcat} em Tormenta20 (Tabela 3-5, pág. 159):\n{itens_str}.",
                "tipo": "equipamento_lista",
                "categoria": "armadura",
                "subcategoria": subcat
            })

    # 3. Itens Gerais por Subcategoria
    subcats_gerais = set(g.get("subcategoria") for g in dados.get("itens_gerais", []) if g.get("subcategoria"))
    for sc in sorted(subcats_gerais):
        g_sub = [g for g in dados.get("itens_gerais", []) if g.get("subcategoria") == sc]
        if g_sub:
            itens_str = ", ".join(f"{g['nome']} ({g.get('preco','—')})" for g in g_sub)
            listas.append({
                "titulo": f"Lista de Itens: {sc}",
                "secao": f"{SEC_BASE} > Itens Gerais > Lista {sc}",
                "pagina": 162,
                "texto": f"Lista de Itens Gerais — {sc} em Tormenta20 (Tabela 3-6, pág. 162-163):\n{itens_str}.",
                "tipo": "equipamento_lista",
                "categoria": "item_geral",
                "subcategoria": sc
            })

    # 4. Lista de Melhorias e Materiais
    melhorias = dados.get("melhorias_superiores", [])
    if melhorias:
        m_str = ", ".join(f"{m['nome']} ({m.get('aplica_a','Geral')})" for m in melhorias)
        listas.append({
            "titulo": "Lista de Melhorias Superiores",
            "secao": f"{SEC_BASE} > Itens Superiores > Lista Melhorias",
            "pagina": 171,
            "texto": f"Lista de Melhorias para Itens Superiores em Tormenta20 (Tabela 3-8, pág. 171):\n{m_str}.",
            "tipo": "equipamento_lista",
            "categoria": "melhoria_superior"
        })

    materiais = dados.get("materiais_especiais", [])
    if materiais:
        mat_str = ", ".join(mat["nome"] for mat in materiais)
        listas.append({
            "titulo": "Lista de Materiais Especiais",
            "secao": f"{SEC_BASE} > Itens Superiores > Lista Materiais Especiais",
            "pagina": 172,
            "texto": f"Lista de Materiais Especiais em Tormenta20 (Tabela 3-9, pág. 172-173):\n{mat_str}.",
            "tipo": "equipamento_lista",
            "categoria": "material_especial"
        })

    return listas


def main():
    if not EQUIP_JSON.exists():
        raise SystemExit(f"Não achei {EQUIP_JSON}. Rode extrair_equipamentos.py antes.")
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py antes.")

    dados = json.loads(EQUIP_JSON.read_text(encoding="utf-8"))

    # Funcao de filtro de chunks antigos do capitulo 3
    def eh_chunk_cap3(c):
        sec = c.get("secao", "")
        tipo = c.get("tipo", "")
        # Remove chunks brutos da ingestão do capítulo 3
        if sec.startswith("Capítulo 3: Equipamento") or sec.startswith("Captulo 3: Equipamento"):
            return True
        # Remove chunks estruturados de equipamento se for re-run
        if tipo in ["equipamento", "melhoria_superior", "material_especial", "regra_equipamento", "equipamento_lista"]:
            return True
        return False

    # 1. Backup
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = INDEX_DIR / f"backup-{stamp}"
    bkp.mkdir(parents=True)
    for nome in ("tormenta.faiss", "chunks.jsonl", "meta.json"):
        shutil.copy2(INDEX_DIR / nome, bkp / nome)
    print(f"[1/5] Backup do índice em {bkp.name}\\")

    # 2. Carrega índice atual
    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    chunks = [json.loads(l) for l in (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert index.ntotal == len(chunks), "índice e chunks.jsonl desalinhados!"
    dim = meta["dim"]
    vetores = index.reconstruct_n(0, index.ntotal)
    print(f"[2/5] Índice atual: {len(chunks)} chunks, dim {dim}")

    # 3. Filtra mantidos
    manter = [(c, vetores[i]) for i, c in enumerate(chunks) if not eh_chunk_cap3(c)]
    removidos = len(chunks) - len(manter)
    print(f"      Removendo {removidos} chunks antigos do Capítulo 3: Equipamento")

    # 4. Gera novos chunks estruturados
    novos = []
    # Armas & Munições
    for a in dados.get("armas", []):
        novos.append(chunk_arma(a))
    # Armaduras & Escudos
    for ar in dados.get("armaduras_escudos", []):
        novos.append(chunk_armadura(ar))
    # Itens Gerais
    for g in dados.get("itens_gerais", []):
        novos.append(chunk_item_geral(g))
    # Melhorias
    for m in dados.get("melhorias_superiores", []):
        novos.append(chunk_melhoria(m))
    # Materiais
    for mat in dados.get("materiais_especiais", []):
        novos.append(chunk_material(mat))
    # Regras Procedurais
    for r in dados.get("regras_procedurais", []):
        novos.append(chunk_regra(r))
    # Chunks-Lista
    listas = gerar_chunks_lista(dados)
    novos.extend(listas)

    print(f"[3/5] {len(novos)} chunks estruturados de equipamento gerados "
          f"({len(dados.get('armas',[]))} armas, {len(dados.get('armaduras_escudos',[]))} armaduras, "
          f"{len(dados.get('itens_gerais',[]))} itens gerais, {len(dados.get('melhorias_superiores',[]))} melhorias, "
          f"{len(dados.get('materiais_especiais',[]))} materiais, {len(dados.get('regras_procedurais',[]))} regras, "
          f"{len(listas)} listas agregadas).")

    # 5. Embutir apenas os novos chunks
    print(f"[4/5] Carregando embedder {meta['modelo_embed']} e embutindo...")
    t0 = time.time()
    model = SentenceTransformer(meta["modelo_embed"])
    emb = model.encode([c["texto"] for c in novos], normalize_embeddings=True,
                       batch_size=8, show_progress_bar=False).astype("float32")
    print(f"      {len(novos)} vetores embutidos em {time.time() - t0:.1f}s")

    # 6. Reconstruir índice
    vecs_manter = np.array([v for _, v in manter], dtype="float32") if manter else np.empty((0, dim), "float32")
    todos_vecs = np.vstack([vecs_manter, emb]).astype("float32")
    todos_chunks = [c for c, _ in manter] + novos
    for i, c in enumerate(todos_chunks):
        c["id"] = i

    novo_index = faiss.IndexFlatIP(dim)
    novo_index.add(todos_vecs)
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))
    
    with open(INDEX_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in todos_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
            
    meta["n_chunks"] = len(todos_chunks)
    meta["equipamentos_estruturados"] = len(novos)
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO - Índice: {len(chunks)} -> {len(todos_chunks)} chunks "
          f"(-{removidos} antigos, +{len(novos)} novos estruturados). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
