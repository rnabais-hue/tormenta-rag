# Família estruturada: Magia (Capítulo 4)

> **Status: EM CONSTRUÇÃO** (agente externo — Antigravity).
> Este é o único arquivo de documentação que a frente de Magia deve editar.
> Não editar o `README.md` da raiz nem outros `docs/*` — apenas adicionar, ao final,
> uma linha de referência no README raiz quando concluir.

Documentar aqui, no padrão das demais famílias do `../../README.md` §11:

- **Fonte no livro**: Capítulo de Magia (páginas a confirmar na extração).
- **Extração** (`extrair_magias.py`): tipografia = schema (nome da magia, escola,
  círculo, execução, alcance, alvo/área, duração, resistência, custo em PM,
  aprimoramentos). Como cada campo é identificado por fonte/tamanho.
- **Schema** de cada registro `tipo="magia"`.
- **Conferência** (`gerar_magias_html.py` → `dados/magias.html`).
- **Integração** (`integrar_magias.py`): substitui os chunks de texto corrido do
  capítulo por 1 chunk/magia (+ listas por escola/círculo, se fizer sentido);
  reconstrói o índice sem reembutir o resto; idempotente. Registrar contagem de
  chunks antes→depois.
- **Filtro híbrido** (opcional): `detectar_filtro_magia()` em `perguntar.py`
  (ex.: "magias de 3º círculo", "magias da escola de Evocação", "magias que curam").
- **Efeito medido** e **limites conhecidos**.
