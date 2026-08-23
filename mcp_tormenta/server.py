# -*- coding: utf-8 -*-
r"""
Servidor MCP (stdio) para o RAG local de Tormenta20.

Expõe a RECUPERAÇÃO (busca no índice FAISS + embedder bge-m3) como ferramentas
MCP, para que clientes como Claude Code, Codex CLI ou Antigravity façam a
GERAÇÃO da resposta com um modelo mais forte, mantendo a busca 100% local.

O índice e o embedder são carregados UMA vez na primeira chamada e mantidos
em memória. O transporte MCP inicia imediatamente para não estourar o timeout
de clientes enquanto o modelo pesado é carregado.

Ferramentas expostas:
  - buscar_tormenta(pergunta, k=5)          -> top-k trechos recuperados
  - montar_contexto_tormenta(pergunta, k=5) -> string de prompt pronta

Como rodar (a partir da raiz do projeto, C:\LLM-Local\tormenta):
    python mcp_tormenta/server.py

Requisito extra: o pacote `mcp` (veja mcp_tormenta/requirements.txt). O resto
(faiss, sentence-transformers, numpy) já faz parte do lab.
"""

import os
import sys
from pathlib import Path

# --- localizar a RAIZ do projeto (onde vivem perguntar.py e index/) ----------
# Este arquivo fica em <raiz>/mcp_tormenta/server.py, então a raiz é o pai.
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# O embedder bge-m3 já está em cache em C:\LLM-Local\models (carrega offline).
# Garantimos HF_HOME caso o cliente MCP não o tenha propagado no ambiente.
os.environ.setdefault("HF_HOME", r"C:\LLM-Local\models")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Reutiliza a recuperação local SEM modificar perguntar.py.
from perguntar import (  # noqa: E402
    carregar,
    buscar,
    montar_prompt,
    fontes_de_hits,
)

try:
    from mcp.server.fastmcp import FastMCP  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover - depende de instalação
    raise SystemExit(
        "O pacote 'mcp' não está instalado. Rode (com aprovação do usuário):\n"
        "    python -m pip install mcp\n"
        "Veja mcp_tormenta/requirements.txt e mcp_tormenta/README.md."
    ) from exc


# --- estado carregado UMA vez no startup -------------------------------------
# carregar() lê o FAISS, os chunks e instancia o embedder bge-m3. É caro; por
# isso fica em memória pelo tempo de vida do processo do servidor.
_INDEX = None
_CHUNKS = None
_MODEL = None
_META = None


def _estado():
    """Carrega índice+chunks+embedder na primeira chamada e reusa depois."""
    global _INDEX, _CHUNKS, _MODEL, _META
    if _INDEX is None:
        print("[mcp_tormenta] carregando índice FAISS + embedder bge-m3...",
              file=sys.stderr, flush=True)
        _INDEX, _CHUNKS, _MODEL, _META = carregar()
        print(f"[mcp_tormenta] pronto: {_META.get('n_chunks')} chunks | "
              f"embedder {_META.get('modelo_embed')}",
              file=sys.stderr, flush=True)
    return _INDEX, _CHUNKS, _MODEL, _META


mcp = FastMCP("tormenta")


@mcp.tool()
def buscar_tormenta(pergunta: str, k: int = 5) -> dict:
    """Recupera os trechos mais relevantes do livro de Tormenta20 para a pergunta.

    Use esta ferramenta para obter o material-fonte (regras, poderes, raças,
    origens, deuses, equipamentos...) e então redigir a resposta CITANDO a
    fonte (seção/página). A busca é híbrida e inclui um motor determinístico de
    pré-requisitos/elegibilidade de poderes — apresente esse conteúdo fielmente.

    Args:
        pergunta: A pergunta do usuário em linguagem natural (português).
        k: Quantos trechos recuperar (padrão 5). Filtros híbridos podem retornar
           mais itens quando a pergunta é uma listagem (ex.: "quais deuses...").

    Returns:
        dict com:
          - pergunta: a pergunta recebida
          - k: o k solicitado
          - n: número de trechos retornados
          - trechos: lista de {rank, id, secao, pagina, score, tipo,
                     match_filtro?, texto} (texto = chunk completo)
          - fontes: lista leve (rank/secao/pagina/score/previa) p/ citação rápida
    """
    index, chunks, model, _ = _estado()
    hits = buscar(pergunta, index, chunks, model, k=k)
    trechos = []
    for n, h in enumerate(hits, 1):
        item = {
            "rank": n,
            "id": h.get("id"),
            "secao": h.get("secao"),
            "pagina": h.get("pagina"),
            "score": round(float(h.get("score", 0.0)), 4),
            "tipo": h.get("tipo"),
            "texto": h.get("texto", ""),
        }
        if h.get("match_filtro"):
            item["match_filtro"] = h["match_filtro"]
        trechos.append(item)
    return {
        "pergunta": pergunta,
        "k": k,
        "n": len(trechos),
        "trechos": trechos,
        "fontes": fontes_de_hits(hits),
    }


@mcp.tool()
def montar_contexto_tormenta(pergunta: str, k: int = 5) -> str:
    """Recupera os trechos e devolve um BLOCO de prompt pronto (contexto + pergunta).

    Conveniência para clientes que preferem um único texto em vez de trechos
    estruturados. Internamente chama a mesma busca de `buscar_tormenta` e formata
    via `montar_prompt` (contexto numerado como [Fonte N] com seção e página).

    Args:
        pergunta: A pergunta do usuário em linguagem natural (português).
        k: Quantos trechos recuperar (padrão 5).

    Returns:
        String no formato "CONTEXTO:\\n...[Fonte N]...\\n\\nPERGUNTA: ...".
        Se nada for recuperado, retorna um aviso curto.
    """
    index, chunks, model, _ = _estado()
    hits = buscar(pergunta, index, chunks, model, k=k)
    if not hits:
        return f"Nenhum trecho recuperado para: {pergunta}"
    return montar_prompt(pergunta, hits)


def main():
    # Inicia o protocolo imediatamente. O carregamento pesado acontece de forma
    # preguiçosa em _estado() na primeira chamada de ferramenta.
    mcp.run()  # transporte stdio (padrão do FastMCP)


if __name__ == "__main__":
    main()
