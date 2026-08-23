# Família estruturada: Bestiário (Capítulo 7)

> **Status: EM CONSTRUÇÃO** (agente externo — Antigravity).
> Único arquivo de doc desta frente. Não editar o corpo do `README.md` (só uma linha
> de referência ao concluir), nem `perguntar.py` além do filtro próprio, nem outras
> famílias/`mcp_tormenta/`.

Documentar aqui, no padrão das demais famílias do `../../README.md` §11:

- **Fonte no livro**: Capítulo 7 (Bestiário / Ameaças) — confirmar páginas na extração.
- **Extração** (`extrair_bestiario.py`): tipografia = schema. Cada criatura é um
  **stat block**: nome, ND (nível de desafio), tipo/tamanho, atributos, PV/PM, Defesa,
  deslocamento, perícias, resistências, ataques, habilidades, e a descrição. Muitos
  campos numéricos rotulados — identificar por fonte/negrito.
- **Schema** de cada registro `tipo="criatura"` (campos tipados + `habilidades[]`,
  `ataques[]`).
- **Conferência** (`gerar_bestiario_html.py` → `dados/bestiario.html`): filtrar por
  ND / tipo / tamanho.
- **Integração** (`integrar_bestiario.py`): substitui o texto corrido do capítulo por
  1 chunk/criatura (+ opcional listas por ND/tipo); reconstrói sem reembutir o resto;
  idempotente. Registrar contagem antes→depois.
- **Filtro híbrido** (opcional): `detectar_filtro_bestiario()` — ex.: "criaturas de ND 5",
  "monstros do tipo espírito", só se agregar valor.
- **Efeito medido** e **limites conhecidos**.
