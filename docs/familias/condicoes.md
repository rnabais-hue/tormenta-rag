# Família estruturada: Condições (apêndice de regras / Cap. 5)

> **Status: EM CONSTRUÇÃO** (agente externo — Antigravity).
> Único arquivo de doc desta frente. Não editar o corpo do `README.md` (só uma linha
> de referência ao concluir) nem outros `docs/*`.

Documentar aqui, no padrão das demais famílias do `../../README.md` §11:

- **Fonte no livro**: lista de Condições (apêndice perto da pág. 400; possível
  referência no Cap. 5 — Jogando). Confirmar páginas na extração.
- **Extração** (`extrair_condicoes.py`): tipografia = schema (nome da condição em
  fonte/tamanho distintos; efeito em roman). Capturar `nome`, `efeito`, e — se houver —
  escalonamento (ex.: Fatigado → Exausto).
- **Schema** de cada registro `tipo="condicao"`.
- **Conferência** (`gerar_condicoes_html.py` → `dados/condicoes.html`).
- **Integração** (`integrar_condicoes.py`): substitui o texto corrido do apêndice por
  1 chunk/condição (+ opcional lista); reconstrói sem reembutir o resto; idempotente.
  Registrar contagem antes→depois.
- **Filtro híbrido** (opcional): `detectar_filtro_condicao()` — só se agregar.
- **Efeito medido**: "o que faz a condição fatigado" deve trazer o chunk da condição
  no topo (antes caía no texto corrido do apêndice).
