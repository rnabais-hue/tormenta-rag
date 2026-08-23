# -*- coding: utf-8 -*-
"""Teste mínimo: confirma que o FastMCP instancia e registra as ferramentas,
sem precisar de um cliente MCP ao vivo. Exige o pacote `mcp` instalado.

Uso (a partir da raiz do projeto C:\\LLM-Local\\tormenta):
    python mcp_tormenta/test_registro.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mcp_tormenta.server as srv


async def _main():
    tools = await srv.mcp.list_tools()
    nomes = sorted(t.name for t in tools)
    print("Ferramentas registradas:", nomes)
    esperado = {"buscar_tormenta", "montar_contexto_tormenta"}
    faltando = esperado - set(nomes)
    assert not faltando, f"faltando ferramentas: {faltando}"
    print("OK: todas as ferramentas esperadas estão registradas.")


if __name__ == "__main__":
    asyncio.run(_main())
