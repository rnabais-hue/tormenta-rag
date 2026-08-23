# -*- coding: utf-8 -*-
r"""
Ingestão do livro de Tormenta20 para RAG.

Pipeline (roda uma vez, offline):
  PDF -> extrair texto por página (PyMuPDF)
      -> limpar (de-hifenizar soft-hyphens, reflow de linhas quebradas)
      -> chunking ancorado no ÍNDICE (TOC) do próprio livro
      -> embeddings multilíngues (BAAI/bge-m3, dim 1024, normalizados)
      -> índice FAISS (produto interno = cosseno) + metadados dos chunks

Saídas em index\:
  - tormenta.faiss   (índice vetorial)
  - chunks.jsonl     (um chunk por linha: id, titulo, secao, pagina, texto)
  - meta.json        (modelo, dimensão, contagens)

Regra do projeto: nada é instalado aqui; usa libs já presentes no Python base.
"""

import json
import re
import time
from pathlib import Path

import numpy as np
import pymupdf                      # PyMuPDF
import faiss
from sentence_transformers import SentenceTransformer

# ------------------------------------------------------------------ config ---
BASE = Path(__file__).parent
LIVRO_DIR = BASE / "livro"
INDEX_DIR = BASE / "index"
INDEX_DIR.mkdir(exist_ok=True)

MODELO_EMBED = "BAAI/bge-m3"        # multilíngue, dim 1024 (ver README)
MAX_CHARS = 2000                    # ~500-600 tokens por chunk
OVERLAP = 200                       # sobreposição ao dividir seções grandes
MIN_CHARS = 60                      # descarta fragmentos (títulos soltos etc.)


# ------------------------------------------------------------- limpeza texto -
def limpar(texto: str) -> str:
    """Corrige os problemas de layout vistos no diagnóstico do PDF."""
    # 1) de-hifenização: soft-hyphen (U+00AD) usado para quebrar palavra na
    #    linha -> junta os pedaços ("peri\xad\ngo" -> "perigo").
    texto = re.sub(r"­\s*\n\s*", "", texto)
    texto = texto.replace("­", "")
    # 2) reflow: linha que termina em letra minúscula/vírgula e a próxima começa
    #    minúscula era uma linha quebrada no meio da frase -> junta com espaço.
    texto = re.sub(
        r"(?<=[a-zà-ÿ,;])\n(?=[a-zà-ÿ])", " ", texto
    )
    # 3) normaliza espaços e limita linhas em branco.
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


# ------------------------------------------------------------- split grande --
def dividir(texto: str, max_chars=MAX_CHARS, overlap=OVERLAP):
    """Divide um texto longo em janelas ~max_chars, quebrando em espaço/quebra
    de linha e mantendo `overlap` de contexto entre janelas."""
    texto = texto.strip()
    if len(texto) <= max_chars:
        return [texto] if texto else []
    pedacos, i = [], 0
    while i < len(texto):
        fim = min(i + max_chars, len(texto))
        if fim < len(texto):
            # recua até um espaço/quebra para não cortar palavra no meio
            corte = texto.rfind(" ", i + max_chars - overlap, fim)
            quebra = texto.rfind("\n", i + max_chars - overlap, fim)
            corte = max(corte, quebra)
            if corte > i:
                fim = corte
        pedacos.append(texto[i:fim].strip())
        if fim >= len(texto):
            break
        i = max(fim - overlap, i + 1)
    return [p for p in pedacos if p]


# --------------------------------------------------------- montar as seções --
def _localizar_titulo(doc, titulo, inicio, fim):
    """Acha a página real (1-based) de um título quebrado no TOC, procurando o
    texto SÓ na janela [inicio, fim) — nunca no livro inteiro, senão a busca
    acha a palavra numa seção distante e envenena o cálculo. Tenta o título
    inteiro, depois sem o prefixo 'Capítulo N:', depois a última palavra."""
    cands = [titulo]
    if ":" in titulo:
        cands.append(titulo.split(":", 1)[1].strip())
    palavras = titulo.split()
    if palavras and len(palavras[-1]) >= 4:
        cands.append(palavras[-1])
    for pno in range(max(inicio - 1, 0), min(fim, doc.page_count)):
        page = doc[pno]
        for c in cands:
            if c and page.search_for(c):
                return pno + 1
    return None


def montar_secoes(doc):
    """Usa o TOC do livro como esqueleto: cada entrada vira uma seção cujo texto
    vai da sua página inicial até a página inicial da PRÓXIMA entrada — particiona
    sem duplicar. Anexa um breadcrumb de títulos.

    Robustez (o PDF foi montado de vários arquivos):
      - remove raízes de montagem cujo título termina em '.pdf';
      - repara marcadores com página fora de ordem (ex.: 'Capítulo 8: Recompensas'
        apontando p/ pág. 1) relocalizando o título por busca de texto — senão o
        chunking 'engoliria' um intervalo enorme de páginas erradas."""
    toc = [e for e in doc.get_toc() if not e[1].strip().lower().endswith(".pdf")]
    print(f"  TOC com {len(toc)} entradas (após remover raízes .pdf)")

    # texto limpo de cada página, uma vez só
    paginas = [limpar(doc[p].get_text("text")) for p in range(doc.page_count)]

    # reparo: força páginas não-decrescentes (marcadores quebrados p/ trás).
    # Só vale a pena relocalizar por busca quando o salto para trás é GRANDE
    # (marcador furado de verdade, como 'Recompensas'); jitters de ±1 página
    # numa lista são inofensivos e só clampam para frente.
    corrigido, running, reparadas = [], 0, 0
    for i, (nivel, titulo, pagina) in enumerate(toc):
        titulo = titulo.strip()
        p = pagina
        if p < running:  # salto para trás = destino de marcador furado
            prox = toc[i + 1][2] if i + 1 < len(toc) else doc.page_count
            hi = max(prox, running + 1)
            real = _localizar_titulo(doc, titulo, running, hi) if running - p > 5 else None
            p = real if real else running
            reparadas += 1
        running = max(running, p)
        corrigido.append((nivel, titulo, p))
    if reparadas:
        print(f"  {reparadas} entradas com página fora de ordem reparadas")

    secoes, pilha = [], []  # pilha = [(nivel, titulo)] para o breadcrumb
    for i, (nivel, titulo, pagina) in enumerate(corrigido):
        ini = max(pagina - 1, 0)
        fim = (corrigido[i + 1][2] - 1) if i + 1 < len(corrigido) else doc.page_count
        if fim <= ini:
            fim = ini + 1  # seções que começam na mesma página: garante >=1 pág

        while pilha and pilha[-1][0] >= nivel:
            pilha.pop()
        breadcrumb = " > ".join(t for _, t in pilha)
        breadcrumb = f"{breadcrumb} > {titulo}" if breadcrumb else titulo
        pilha.append((nivel, titulo))

        texto = "\n".join(paginas[ini:fim]).strip()
        secoes.append(
            {"titulo": titulo, "secao": breadcrumb, "pagina": ini + 1, "texto": texto}
        )
    return secoes


# ------------------------------------------------------------------- main ----
def main():
    pdfs = list(LIVRO_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"Nenhum PDF em {LIVRO_DIR}")
    pdf = pdfs[0]
    print(f"[1/5] Abrindo {pdf.name}")
    doc = pymupdf.open(pdf)
    print(f"      {doc.page_count} páginas")

    print("[2/5] Extraindo + limpando + chunking pelo TOC")
    secoes = montar_secoes(doc)

    chunks = []
    for s in secoes:
        for pedaco in dividir(s["texto"]):
            if len(pedaco) >= MIN_CHARS:
                chunks.append(
                    {
                        "id": len(chunks),
                        "titulo": s["titulo"],
                        "secao": s["secao"],
                        "pagina": s["pagina"],
                        "texto": pedaco,
                    }
                )
    print(f"      {len(chunks)} chunks gerados (de {len(secoes)} seções)")

    print(f"[3/5] Carregando embedder {MODELO_EMBED}")
    t = time.time()
    model = SentenceTransformer(MODELO_EMBED)
    print(f"      carregado em {time.time() - t:.0f}s")

    print("[4/5] Gerando embeddings (CPU — pode levar alguns minutos)")
    t = time.time()
    emb = model.encode(
        [c["texto"] for c in chunks],
        batch_size=16,
        normalize_embeddings=True,   # cosseno via produto interno
        show_progress_bar=True,
    ).astype("float32")
    dim = emb.shape[1]
    print(f"      {emb.shape[0]} vetores dim {dim} em {time.time() - t:.0f}s")

    print("[5/5] Montando índice FAISS e salvando")
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    faiss.write_index(index, str(INDEX_DIR / "tormenta.faiss"))

    with open(INDEX_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    with open(INDEX_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "modelo_embed": MODELO_EMBED,
                "dim": dim,
                "n_chunks": len(chunks),
                "n_secoes": len(secoes),
                "pdf": pdf.name,
                "max_chars": MAX_CHARS,
                "overlap": OVERLAP,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"OK -> índice em {INDEX_DIR}")


if __name__ == "__main__":
    main()
