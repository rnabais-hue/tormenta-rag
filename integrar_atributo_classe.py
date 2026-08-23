# -*- coding: utf-8 -*-
r"""
Integra o ATRIBUTO PRINCIPAL (dados/classes.json → campo `atributo_principal`,
gerado por extrair_atributos_classe.py) ao TEXTO do chunk de visão geral de cada
classe no índice. Assim a resposta a "qual o atributo do paladino?" passa a vir do
RAG (recuperação vetorial), não de um regex hard-coded.

Cirúrgico e seguro: re-embute SOMENTE os 14 chunks `tipo=classe, subtipo=visao_geral`
(mantém a posição/ordem e todos os outros vetores intactos — NÃO mexe em poderes,
então não dispara o caveat de ordem de re-run do §11). n_chunks não muda.

Além do FATO do livro (Tabela 1-3), o texto ensina a LEITURA: a importância de um
atributo vem de quantas habilidades/poderes da classe dependem dele — logo builds
alternativas são viáveis (ex.: Guerreiro de Destreza). O livro destaca o(s)
principal(is), sem torná-lo obrigatório.

Idempotente (regenera o texto do zero a cada run). Uso: python integrar_atributo_classe.py
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
CLASSES_JSON = BASE / "dados" / "classes.json"
ORDEM = ["Pontos de Vida", "Pontos de Mana", "Perícias", "Proficiências"]


def _linha_atributo(ap):
    """Verbaliza o campo atributo_principal para o texto do chunk."""
    if not ap:
        return None
    txt = ap["texto"]
    if ap.get("relacao") == "ou":
        nota = " (o livro aceita qualquer um destes como atributo principal; escolha conforme sua build)"
    elif ap.get("relacao") == "e":
        nota = " (a classe se apoia em ambos)"
    else:
        nota = ""
    return f"- Atributo principal (Tabela 1-3 do livro, pág. 32): {txt}{nota}."


_FRAMING = ("Observação: a importância de um atributo para uma classe vem de quantas "
            "de suas habilidades e poderes dependem dele. O livro destaca o(s) atributo(s) "
            "principal(is) acima, mas não são obrigatórios — builds alternativas são viáveis "
            "(por exemplo, um Guerreiro focado em Destreza em vez de Força).")


def texto_visao_geral(c):
    """Reconstrói o texto do chunk de visão geral, agora com o atributo principal."""
    linhas = [f"Classe: {c['nome']} (Tormenta20, pág. {c['pagina']})."]
    if c.get("resumo"):
        linhas.append(c["resumo"])
    linhas.append("Características de classe:")
    la = _linha_atributo(c.get("atributo_principal"))
    if la:
        linhas.append(la)
    chaves = [k for k in ORDEM if k in c["caracteristicas"]] + \
             [k for k in c["caracteristicas"] if k not in ORDEM]
    for k in chaves:
        linhas.append(f"- {k}: {c['caracteristicas'][k]}")
    linhas.append(_FRAMING)
    return "\n".join(linhas)


def main():
    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py antes.")
    classes = {c["nome"]: c for c in json.loads(CLASSES_JSON.read_text(encoding="utf-8"))}
    if not any("atributo_principal" in c for c in classes.values()):
        raise SystemExit("classes.json não tem atributo_principal. Rode extrair_atributos_classe.py antes.")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = INDEX_DIR / f"backup-{stamp}"
    bkp.mkdir(parents=True)
    for nome in ("tormenta.faiss", "chunks.jsonl", "meta.json"):
        shutil.copy2(INDEX_DIR / nome, bkp / nome)
    print(f"[1/4] Backup do indice em {bkp.name}\\")

    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    chunks = [json.loads(l) for l in
              (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert index.ntotal == len(chunks), "indice e chunks.jsonl desalinhados!"
    dim = meta["dim"]
    vetores = index.reconstruct_n(0, index.ntotal).astype("float32")
    print(f"[2/4] Indice: {len(chunks)} chunks, dim {dim}")

    alvos = [i for i, c in enumerate(chunks)
             if c.get("tipo") == "classe" and c.get("subtipo") == "visao_geral"]
    for i in alvos:
        c = chunks[i]
        cj = classes.get(c["classe"])
        if not cj:
            continue
        c["texto"] = texto_visao_geral(cj)
        c["atributo_principal"] = cj.get("atributo_principal")
    print(f"[3/4] Atualizando {len(alvos)} chunks de visao geral (re-embutindo so eles)")

    model = SentenceTransformer(meta["modelo_embed"])
    t = time.time()
    emb = model.encode([chunks[i]["texto"] for i in alvos], normalize_embeddings=True,
                       batch_size=8, show_progress_bar=False).astype("float32")
    for k, i in enumerate(alvos):
        vetores[i] = emb[k]
    print(f"      {len(alvos)} vetores em {time.time() - t:.0f}s")

    novo_index = faiss.IndexFlatIP(dim)
    novo_index.add(vetores)
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))
    with open(INDEX_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    meta["atualizado_em"] = stamp
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[4/4] OK - {len(alvos)} chunks de classe agora citam o atributo principal. "
          f"n_chunks inalterado ({len(chunks)}). Backup em {bkp.name}\\")


if __name__ == "__main__":
    main()
