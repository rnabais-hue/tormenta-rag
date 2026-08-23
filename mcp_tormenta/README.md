# mcp_tormenta — Servidor MCP do RAG de Tormenta20

Expõe a **recuperação** (busca no índice FAISS local + embedder `BAAI/bge-m3`)
como ferramentas MCP. Assim, clientes MCP (Claude Code, Codex CLI, Antigravity...)
fazem a **geração** da resposta com um modelo mais forte, enquanto a **busca
permanece 100% local** — nenhum trecho do livro sai do seu computador para a
nuvem exceto os trechos que o próprio cliente decidir enviar ao LLM.

> **Índice não distribuído (direitos autorais).** O `index/` (FAISS + chunks) é
> construído **localmente** a partir do seu material via `ingestao.py`. Este
> pacote apenas **lê** o índice; não o inclui nem o reconstrói.

## Ferramentas expostas

| Ferramenta | Assinatura | Retorno |
|---|---|---|
| `buscar_tormenta` | `(pergunta: str, k: int = 5)` | top-k trechos: `rank, id, secao, pagina, score, tipo, match_filtro?, texto` (texto = chunk completo) + `fontes` leves |
| `montar_contexto_tormenta` | `(pergunta: str, k: int = 5)` | string de prompt pronta (`CONTEXTO:` numerado + `PERGUNTA:`), via `montar_prompt` |

A busca é **híbrida**: além da similaridade vetorial, há filtros por metadado
(raças, perícias, origens, deuses, atributos, equipamentos) e um **motor
determinístico** de pré-requisitos/elegibilidade de poderes. Tudo isso vem de
`perguntar.py` (reutilizado sem modificação).

## Instalação

Requer **apenas uma dependência extra** além do lab RAG existente: o SDK oficial
`mcp`. O resto (faiss-cpu, sentence-transformers, numpy, requests) já está
instalado no ambiente do laboratório.

> **Regra do projeto: NUNCA instalar nada sem aprovação explícita do usuário.**
> Rode o comando abaixo somente após aprovar:

```powershell
python -m pip install mcp
```

Confirme que ficou importável:

```powershell
python -c "import mcp; print('mcp OK')"
```

## Como rodar

O servidor precisa ser executado **a partir da raiz do projeto**
(`C:\LLM-Local\tormenta`), onde existem `perguntar.py` e `index/`. O próprio
`server.py` ajusta o `sys.path` para a raiz e define `HF_HOME` para o cache de
modelos, então ele funciona mesmo invocado com caminho absoluto.

```powershell
# a partir de C:\LLM-Local\tormenta
python mcp_tormenta\server.py
```

O índice e o embedder são carregados **uma vez** no startup (mensagem em
`stderr`) e mantidos em memória; o transporte é **stdio** (padrão do FastMCP).

## Configuração por cliente

Ajuste os caminhos se o seu Python ou a raiz do projeto forem diferentes.
Python do lab: `C:\Users\rnaba\AppData\Local\Programs\Python\Python312\python.exe`

### (a) Claude Code

Via CLI (`cwd` na raiz garante que `index/` seja encontrado):

```powershell
claude mcp add tormenta --scope local `
  --env HF_HOME=C:\LLM-Local\models `
  -- "C:\Users\rnaba\AppData\Local\Programs\Python\Python312\python.exe" "C:\LLM-Local\tormenta\mcp_tormenta\server.py"
```

Ou, via arquivo `.mcp.json` na raiz do projeto:

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

### (b) Codex CLI

No `config.toml` do Codex (`~/.codex/config.toml`):

```toml
[mcp_servers.tormenta]
command = "C:\\Users\\rnaba\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
args = ["C:\\LLM-Local\\tormenta\\mcp_tormenta\\server.py"]

[mcp_servers.tormenta.env]
HF_HOME = "C:\\LLM-Local\\models"
```

## Teste

Sanidade da recuperação (não exige `mcp`), a partir da raiz:

```powershell
python -c "import perguntar as p; i,c,m,meta=p.carregar(); print(len(p.buscar('como funciona a condição fatigado?', i,c,m,k=5)), 'hits')"
```

Registro das ferramentas no FastMCP (exige `mcp` instalado):

```powershell
python mcp_tormenta\test_registro.py
```

Ver `../docs/mcp.md` para a documentação completa.
