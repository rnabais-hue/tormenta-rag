# Documentação modular — RAG Tormenta20

O `../README.md` na raiz continua sendo a **fonte-de-verdade** e o índice geral do
projeto. Para permitir trabalho **paralelo** sem conflito de merge, cada componente
ou família nova ganha seu **próprio arquivo** aqui em `docs/`, e o README da raiz
apenas o referencia.

Regra de ouro do paralelismo: **cada frente escreve só no seu arquivo de doc.**

## Índice
- [`familias/magia.md`](familias/magia.md) — Capítulo de Magia (extração + integração + filtro). **Em construção.**
- [`mcp.md`](mcp.md) — Servidor MCP (expõe a recuperação do RAG a clientes como Claude Code / Codex / Antigravity). **Em construção.**

## Convenção para novos arquivos
Ao fechar uma família/componente, documente aqui no padrão das seções do README
raiz (o quê, como funciona a tipografia/lógica, como rodar, efeito medido, limites)
e adicione uma linha de referência no README da raiz.
