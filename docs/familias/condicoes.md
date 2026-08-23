# Família estruturada: Condições (Apêndice)

> **Status: CONCLUÍDO E INTEGRADO** (Frente Antigravity).  
> Este documento é a documentação completa e autossuficiente da família estruturada de Condições de Tormenta20 (Edição Jogo do Ano).

---

## 1. Fonte no Livro

- **Apêndice: Lista de Condições** (páginas 400 e 401 do PDF do livro / páginas 394–395 na numeração impressa):
  - Bloco introdutório de regras gerais de condições (acúmulo, duração de cena e tipos de efeito).
  - Todas as **35 condições de jogo** em ordem alfabética de A a Z.

---

## 2. Extração por Tipografia (`extrair_condicoes.py`)

A extração utiliza `PyMuPDF` (`get_text("dict")`), guiando-se estritamente pela **hierarquia tipográfica do layout original**:

| Elemento | Tipografia / Tamanho | Função no Schema |
|---|---|---|
| **Cabeçalho da Condição** | `IowanOldStyle-Bold` ~9.5 pt | Nome da condição (ex.: `Abalado.`, `Fatigado.`, `Caído.`) |
| **Descrição / Efeito Mecânico** | `IowanOldStyle-Roman` ~9.5 pt | Efeito mecânico completo e regras de resolução |
| **Tipo de Efeito** | `IowanOldStyle-Italic` ~9.5 pt | Categoria de efeito ao final da descrição (*Medo, Mental, Movimento, Metabolismo, Sentidos, Cansaço, Veneno, Metamorfose*) |
| **Progressão / Escalamento** | Padrão textual na regra | Detectado via regex (*"Se ficar X novamente, em vez disso fica Y"*) |
| **Regras Gerais** | `IowanOldStyle-Roman` ~9.5 pt | Bloco introdutório no topo da pág. 400 |

Rode com:
```powershell
python extrair_condicoes.py
```
Gera [`dados/condicoes.json`](file:///c:/LLM-Local/tormenta/dados/condicoes.json) com **35 condições tipadas** e **1 bloco procedural de regra geral**.

### Distribuição por Tipo de Efeito
- **Mental (8)**: Alquebrado, Atordoado, Confuso, Enfeitiçado, Esmorecido, Fascinado, Frustrado, Pasmo.
- **Movimento (6)**: Agarrado, Enredado, Imóvel, Lento, Paralisado, Sobrecarregado.
- **Sentidos (3)**: Cego, Ofuscado, Surdo.
- **Metabolismo (3)**: Doente, Enjoado, Sangrando.
- **Cansaço (2)**: Exausto, Fatigado.
- **Medo (2)**: Abalado, Apavorado.
- **Veneno (1)**: Envenenado.
- **Metamorfose (1)**: Petrificado.
- **Gerais / Físicas (9)**: Caído, Debilitado, Desprevenido, Em Chamas, Fraco, Inconsciente, Indefeso, Surpreendido, Vulnerável.

### Condições que Escalam (6 progressões)
1. **Abalado** $\rightarrow$ Apavorado
2. **Fatigado** $\rightarrow$ Exausto
3. **Fraco** $\rightarrow$ Debilitado
4. **Frustrado** $\rightarrow$ Esmorecido
5. **Debilitado** $\rightarrow$ Inconsciente
6. **Exausto** $\rightarrow$ Inconsciente

---

## 3. Schema de Dados

Cada condição em [`dados/condicoes.json`](file:///c:/LLM-Local/tormenta/dados/condicoes.json) segue o schema:

```json
{
  "id": "condicao_fatigado",
  "tipo_entidade": "condicao",
  "nome": "Fatigado",
  "tipo_efeito": "Cansaço",
  "piora_para": "Exausto",
  "descricao": "O personagem fica fraco e vulnerável. Se ficar fatigado novamente, em vez disso fica exausto.",
  "pagina": 401
}
```

A regra geral de condições segue o schema:
```json
{
  "id": "regra_condicoes_acumulo_duracao",
  "tipo_entidade": "regra_condicao",
  "titulo": "Regras Gerais de Condições (Acúmulo, Duração e Tipos de Efeito)",
  "pagina": 400,
  "resumo": "Condições com mesmos efeitos não se acumulam. Duração padrão é até o fim da cena. Tipos de efeito definem imunidades e interações.",
  "texto": "Regras Gerais de Condições:\n• Acúmulo: Condições com os mesmos efeitos não se acumulam; aplique apenas os mais severos...\n• Duração Padrão: A menos que especificado o contrário, condições terminam no fim da cena...\n• Tipos de Efeitos: Algumas condições possuem um tipo de efeito associado (Cansaço, Medo, Mental, Metabolismo, Metamorfose, Movimento, Sentidos, Veneno)..."
}
```

---

## 4. Conferência Visual (`gerar_condicoes_html.py`)

A ferramenta [`dados/condicoes.html`](file:///c:/LLM-Local/tormenta/dados/condicoes.html) permite visualizar, pesquisar e validar todas as 35 condições e regras gerais offline:
- **Busca em tempo real**: Filtra por nome da condição, efeito mecânico, palavras-chave ou escalamento.
- **Filtros por Tipo de Efeito**: Chips interativos (*Mental, Movimento, Sentidos, Metabolismo, Cansaço, Medo, Veneno, Metamorfose, Gerais*).
- **Filtro de Escalamento**: Exibe apenas as condições que pioram se aplicadas novamente.
- **Badges estilizados**: Cores temáticas para cada tipo de efeito e destaque para "Piora para: ...".
- **Alternador de Tema**: Suporte a modo claro e escuro.

Rode para atualizar:
```powershell
python gerar_condicoes_html.py
```

---

## 5. Integração ao Índice FAISS (`integrar_condicoes.py`)

O script [`integrar_condicoes.py`](file:///c:/LLM-Local/tormenta/integrar_condicoes.py) realiza a substituição cirúrgica no índice FAISS:
1. Faz backup automático do estado anterior do índice em `index/backup-<timestamp>/`.
2. Carrega `meta.json`, `chunks.jsonl` e `tormenta.faiss`.
3. **Reconstrói os vetores** das demais famílias (`index.reconstruct_n`), preservando raças, classes, perícias, origens, deuses, atributos, poderes, equipamentos e magias.
4. **Remove estritamente os 4 chunks antigos de texto corrido** do Apêndice: Lista de Condições (págs 400–401).
5. **Insere 37 novos chunks estruturados finos**:
   - **35 chunks específicos de condição**: 1 por condição com nome, tipo de efeito, escalamento e efeito mecânico completo.
   - **1 chunk de regra geral**: acúmulo de condições, duração padrão de cena e imunidades por tipos de efeitos.
   - **1 chunk-lista agregada**: visão ampla de todas as 35 condições agrupadas por tipo de efeito.
6. Embuti **somente os 37 novos chunks** com `BAAI/bge-m3` (~19s em CPU) e recria o `IndexFlatIP`.
7. Atualiza `chunks.jsonl` e `meta.json` (`condicoes_estruturadas: 35`).
8. É **idempotente**: rodar novamente remove os chunks estruturados de condição anteriores e reintegra sem duplicar.

Rode com:
```powershell
python integrar_condicoes.py
```

---

## 6. Filtro Híbrido em `perguntar.py`

A função `detectar_filtro_condicao()` identifica consultas de listagem e agrupamento de condições:
- Tipo de Efeito: *"quais são as condições de movimento"*, *"condições mentais"*, *"condições de sentidos"*
- Escalamento: *"quais condições escalam no jogo"*, *"condições que pioram"*
- Lista Geral: *"quais são as condições do jogo"*, *"lista de condições"*

O hook em `buscar()` prioriza as condições e listas correspondentes no topo do ranking. O log em `consultar()` registra `filtro_condicao` em `logs/consultas.jsonl`.

---

## 7. Efeito Medido e Validação

| Pergunta | Chunk no Rank 1 | Score | Mecanismo |
|---|---|---|---|
| *"O que faz a condição fatigado?"* | `Fatigado` | 0.599 | Busca Vetorial Direta |
| *"O que é estar caído?"* | `Caído` | 0.478 | Busca Vetorial Direta |
| *"Como funciona a condição cego?"* | `Cego` | 0.616 | Busca Vetorial Direta |
| *"O que acontece se o personagem estiver agarrado?"* | `Agarrado` | 0.652 | Busca Vetorial Direta |
| *"Quais são as condições de movimento?"* | `Lento` / `Imóvel` / `Paralisado` | > 0.51 | Filtro Híbrido Tipo |
| *"Quais condições escalam no jogo?"* | `Abalado` / `Exausto` / `Fraco` | > 0.44 | Filtro Híbrido Escalamento |
| *"Como funciona o acúmulo de condições?"* | `Regras Gerais de Condições (Acúmulo, Duração)` | 0.649 | Busca Vetorial Procedural |
