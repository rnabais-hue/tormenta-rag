# Servidor MCP — recuperação do RAG como ferramenta

Objetivo: expor a **recuperação** (embedder `BAAI/bge-m3` + FAISS + filtros
híbridos do `perguntar.py`) como um servidor **MCP** (stdio), para que clientes
como **Claude Code, Codex e Antigravity** façam a geração com um modelo mais
forte, mantendo a **busca local**. Reforça o desacoplamento recuperação × geração.

A frente do MCP **não edita `perguntar.py`** (só importa `carregar`/`buscar`/
`montar_prompt`/`fontes_de_hits`), nem o índice, nem os `dados/`.

## Estrutura do pacote `mcp_tormenta/`

```
mcp_tormenta/
├── __init__.py          # marca o pacote
├── server.py            # servidor MCP (FastMCP, transporte stdio)
├── requirements.txt     # só a dependência extra: mcp
├── test_registro.py     # teste: FastMCP instancia e registra as ferramentas
└── README.md            # instalação, execução e configuração por cliente
```

`server.py` fica em `<raiz>/mcp_tormenta/`; ele insere a **raiz do projeto**
(`C:\LLM-Local\tormenta`) no `sys.path` e define `HF_HOME=C:\LLM-Local\models`,
então importa de `perguntar` sem modificar nada. O índice (`index/`) e o embedder
são carregados **uma única vez** no startup e mantidos em memória.

## Ferramentas expostas

| Ferramenta | Assinatura | Retorno |
|---|---|---|
| `buscar_tormenta` | `(pergunta: str, k: int = 5)` | `dict` com `pergunta, k, n, trechos[], fontes[]`. Cada trecho: `rank, id, secao, pagina, score, tipo, match_filtro?, texto` (texto = chunk **completo**, para o cliente citar a fonte). |
| `montar_contexto_tormenta` | `(pergunta: str, k: int = 5)` | `str`: bloco de prompt pronto (`CONTEXTO:` numerado como `[Fonte N]` com seção/página + `PERGUNTA:`), via `montar_prompt`. Para clientes que preferem um único texto. |

A busca é **híbrida**: similaridade vetorial + filtros por metadado (raças,
perícias, origens, deuses, atributos, equipamentos) + um **motor determinístico**
de pré-requisitos e elegibilidade de poderes. Quando um filtro/motor dispara,
`k` pode ser excedido (listagens) e os itens vêm com `match_filtro`.

## Dependências

Apenas **`mcp`** (SDK oficial; inclui `mcp.server.fastmcp.FastMCP`). O restante
— `faiss-cpu`, `sentence-transformers`, `numpy`, `requests` — já pertence ao lab.

> **Regra do projeto: NUNCA instalar sem aprovação explícita.** Após aprovar:
> `python -m pip install mcp`

> **Índice construído localmente (direitos autorais).** O `index/` (FAISS +
> chunks) é gerado por `ingestao.py` a partir do seu material; **não é
> distribuído** com este pacote. O servidor apenas **lê** o índice.

## Como rodar

A partir da raiz (`C:\LLM-Local\tormenta`), onde vivem `perguntar.py` e `index/`:

```powershell
python mcp_tormenta\server.py
```

Startup imprime em `stderr` o número de chunks e o embedder; transporte = stdio.

## Configuração por cliente

Python do lab: `C:\Users\rnaba\AppData\Local\Programs\Python\Python312\python.exe`

### Claude Code — CLI

```powershell
claude mcp add tormenta --scope local `
  --env HF_HOME=C:\LLM-Local\models `
  -- "C:\Users\rnaba\AppData\Local\Programs\Python\Python312\python.exe" "C:\LLM-Local\tormenta\mcp_tormenta\server.py"
```

### Claude Code — `.mcp.json`

```json
{
  "mcpServers": {
    "tormenta": {
      "command": "C:\\Users\\rnaba\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\LLM-Local\\tormenta\\mcp_tormenta\\server.py"],
      "env": { "HF_HOME": "C:\\LLM-Local\\models" }
    }
  }
}
```

### Codex CLI — `config.toml`

```toml
[mcp_servers.tormenta]
command = "C:\\Users\\rnaba\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
args = ["C:\\LLM-Local\\tormenta\\mcp_tormenta\\server.py"]

[mcp_servers.tormenta.env]
HF_HOME = "C:\\LLM-Local\\models"
```

## Como testar

1. **Recuperação** (não exige `mcp`), a partir da raiz:

   ```powershell
   python -c "import perguntar as p; i,c,m,meta=p.carregar(); print(len(p.buscar('como funciona a condição fatigado?', i,c,m,k=5)), 'hits')"
   ```

   Esperado: `5 hits` (top-1 = "Apêndice: Lista de Condições", pág. 400).

2. **Registro das ferramentas** no FastMCP (exige `mcp` instalado):

   ```powershell
   python mcp_tormenta\test_registro.py
   ```

   Esperado: `['buscar_tormenta', 'montar_contexto_tormenta']`.

3. **Cliente ao vivo**: configure conforme acima e peça ao cliente para chamar
   `buscar_tormenta` com uma pergunta de regras; ele deve receber os trechos e
   redigir a resposta citando seção/página.
