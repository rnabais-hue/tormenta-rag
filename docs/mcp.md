# Servidor MCP — recuperação do RAG como ferramenta

> **Status: EM CONSTRUÇÃO** (agente do MCP, nesta sessão).
> Único arquivo de doc desta frente. A frente do MCP **não edita `perguntar.py`**
> (só importa `carregar`/`buscar`), nem o índice, nem os `dados/`.

Objetivo: expor a **recuperação** (embedder bge-m3 + FAISS + filtros do
`perguntar.py`) como um servidor **MCP** (stdio), para que clientes como
**Claude Code, Codex e Antigravity** façam a geração com um modelo mais forte,
mantendo a busca local. Reforça o desacoplamento recuperação × geração.

A ser preenchido pela frente do MCP:
- Estrutura do pacote separável `mcp_tormenta/`.
- Ferramentas expostas (ex.: `buscar_tormenta(pergunta, k)` → top-k chunks com
  fonte: seção/página/texto/score).
- Dependências próprias e nota de que o **índice é construído localmente** (não
  distribuído — direitos autorais).
- Snippets de configuração por cliente (Claude Code, Codex).
- Como testar.
