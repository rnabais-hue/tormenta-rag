# Família estruturada: Magia (Capítulo 4)

> **Status: CONCLUÍDO E INTEGRADO** (Frente Antigravity).  
> Este documento é a documentação completa e autossuficiente da família estruturada de Magias de Tormenta20 (Edição Jogo do Ano).

---

## 1. Fonte no Livro

- **Capítulo 4: Magia** (páginas 174–217 do PDF do livro):
  - **Páginas 174–179**: Regras gerais de magia (Classificação, Aprendendo Magias, Lançando Magias, Custo em PM, Características das Magias, Anulando Magias e Contramágica).
  - **Páginas 180–183**: Listas/Tabelas de Magias Arcanas e Divinas por círculo e escola.
  - **Páginas 184–217**: Seção *Descrição das Magias*, contendo todas as **198 magias** em ordem alfabética de A a Z.

---

## 2. Extração por Tipografia (`extrair_magias.py`)

A extração utiliza a biblioteca `PyMuPDF` (`get_text("dict")`), guiando-se estritamente pela **hierarquia tipográfica do layout original** em vez do sumário (TOC):

| Elemento | Tipografia / Tamanho | Função no Schema |
|---|---|---|
| **Título da Magia** | `Tormenta20-Regular` ~16.0 pt | Nome da magia (suporta quebra em 2 linhas) |
| **Subtítulo / Header** | `Tormenta20-Regular` ~9.0 pt | Tipo (*Arcana, Divina, Universal*), Círculo (*1º a 5º*) e Escola (*Abjuração, Adivinhação, Convocação, Encantamento, Evocação, Ilusão, Necromancia, Transmutação*) |
| **Rótulos de Stat Block** | `IowanOldStyle-Bold` ~8.5 pt | `Execução:`, `Alcance:`, `Alvo:` / `Área:` / `Efeito:`, `Duração:`, `Resistência:` |
| **Valores de Stat Block** | `IowanOldStyle-Roman` ~8.5 pt | Valores correspondentes de cada parâmetro |
| **Descrição Principal** | `IowanOldStyle-Roman` ~8.5 pt | Texto descritivo e efeito mecânico base |
| **Aprimoramentos & Truques** | `IowanOldStyle-Bold` ~8.5 pt (`Truque:`, `+N PM:`) | Lista de modificadores e upgrades de custo de mana |

Rode com:
```powershell
python extrair_magias.py
```
Gera [`dados/magias.json`](file:///c:/LLM-Local/tormenta/dados/magias.json) com **198 magias tipadas** e **5 blocos procedurais de regras**.

### Distribuição no Livro
- **Por Círculo**:
  - 1º Círculo: 54 magias (Custo base: 1 PM)
  - 2º Círculo: 48 magias (Custo base: 3 PM)
  - 3º Círculo: 40 magias (Custo base: 6 PM)
  - 4º Círculo: 30 magias (Custo base: 10 PM)
  - 5º Círculo: 26 magias (Custo base: 15 PM)
- **Por Tipo**:
  - Arcana: 95 magias
  - Divina: 74 magias
  - Universal: 29 magias
- **Por Escola**:
  - Evocação: 33 magias
  - Abjuração: 27 magias
  - Convocação: 26 magias
  - Transmutação: 26 magias
  - Encantamento: 24 magias
  - Necromancia: 23 magias
  - Adivinhação: 23 magias
  - Ilusão: 16 magias

---

## 3. Schema de Dados

Cada magia em [`dados/magias.json`](file:///c:/LLM-Local/tormenta/dados/magias.json) segue o schema estruturado:

```json
{
  "id": "magia_bola_de_fogo",
  "tipo_entidade": "magia",
  "nome": "Bola de Fogo",
  "tipo": "arcana",
  "circulo": 2,
  "custo_pm": 3,
  "escola": "Evocação",
  "execucao": "padrão",
  "alcance": "médio",
  "alvo_tipo": "Área",
  "alvo": "esfera com 6m de raio",
  "duracao": "instantânea",
  "resistencia": "Reflexos reduz à metade",
  "descricao": "Esta famosa magia de ataque cria uma poderosa explosão, causando 6d6 pontos de dano de fogo em todas as criaturas e objetos livres na área.",
  "aprimoramentos": [
    {
      "custo": "+2 PM",
      "efeito": "aumenta o dano em +2d6."
    },
    {
      "custo": "+2 PM",
      "efeito": "muda a área para efeito de esfera flamejante com tamanho Médio e a duração para cena..."
    },
    {
      "custo": "+3 PM",
      "efeito": "muda a duração para um dia ou até ser descarregada..."
    }
  ],
  "pagina": 188
}
```

As regras procedurais de magia seguem o schema:
```json
{
  "id": "regra_magia_lancamento_custos",
  "tipo_entidade": "regra_magia",
  "titulo": "Lançando Magias (Custos em PM, Limite de Gasto e Aprimoramentos)",
  "pagina": 176,
  "resumo": "Regras de conjuração, gasto de Pontos de Mana (PM)...",
  "texto": "..."
}
```

---

## 4. Conferência Visual (`gerar_magias_html.py`)

A ferramenta [`dados/magias.html`](file:///c:/LLM-Local/tormenta/dados/magias.html) permite inspecionar, auditar e testar visualmente todas as 198 magias e 5 regras sem depender de internet:
- **Busca em tempo real**: Filtra por nome, escola, palavras na descrição ou nos aprimoramentos.
- **Filtros combinados**: Por Círculo (1º–5º), Tipo (Arcana/Divina/Universal) e Escola (8 escolas).
- **Badges de Stat Block**: Exibição imediata de Ação, Alcance, Alvo, Duração, Resistência e custo em PM.
- **Modo Escuro / Claro**: Alternador integrado com persistência via `localStorage`.

Rode para atualizar:
```powershell
python gerar_magias_html.py
```

---

## 5. Integração ao Índice FAISS (`integrar_magias.py`)

O script [`integrar_magias.py`](file:///c:/LLM-Local/tormenta/integrar_magias.py) realiza a substituição cirúrgica no índice FAISS:
1. Faz backup automático do estado anterior do índice em `index/backup-<timestamp>/`.
2. Carrega `meta.json`, `chunks.jsonl` e `tormenta.faiss`.
3. **Reconstrói os vetores** das outras famílias existentes (`index.reconstruct_n`), preservando raças, classes, perícias, origens, deuses, atributos, poderes e equipamentos.
4. **Remove estritamente os 135 chunks antigos de texto corrido** do Capítulo 4 (págs 174–217).
5. **Insere 219 novos chunks estruturados finos**:
   - **198 chunks específicos de magia**: 1 por magia com stat block verbalizado, descrição e aprimoramentos.
   - **16 chunks de listas agregadas**: 8 por escola, 5 por círculo e 3 por tipo (para consultas de visão ampla).
   - **5 chunks de regras procedurais**: Classificação, Aprendizado, Lançamento/PM, Parâmetros e Contramágica.
6. Embuti **somente os 219 novos chunks** com `BAAI/bge-m3` e recria o `IndexFlatIP`.
7. Atualiza `chunks.jsonl` e `meta.json` (`magias_estruturadas: 198`).
8. É **idempotente**: rodar novamente remove os chunks estruturados de magia anteriores e reintegra sem duplicar.

Rode com:
```powershell
python integrar_magias.py
```

---

## 6. Filtro Híbrido em `perguntar.py`

A função `detectar_filtro_magia()` identifica consultas de listagem categórica:
- Círculo: *"quais as magias de 3º círculo"*, *"magias de 1º círculo"*
- Escola: *"magias da escola de evocação"*, *"magias de abjuração"*
- Tipo: *"magias arcanas"*, *"magias divinas"*, *"magias universais"*
- Combinações: *"magias arcanas de 2º círculo"*, *"magias de 3º círculo de transmutação"*

O hook em `buscar()` ativa o filtro e traz os chunks específicos e listas correspondentes no topo. O log em `consultar()` registra `filtro_magia` em `logs/consultas.jsonl`.

---

## 7. Efeito Medido e Validação

| Pergunta | Chunk no Rank 1 | Score | Mecanismo |
|---|---|---|---|
| *"O que faz a magia Bola de Fogo?"* | `Magia: Bola de Fogo` | > 0.65 | Busca Vetorial Direta |
| *"Como funciona a magia Curar Ferimentos?"* | `Magia: Curar Ferimentos` | > 0.65 | Busca Vetorial Direta |
| *"Qual a duração e efeito da magia Velocidade?"* | `Magia: Velocidade` | > 0.60 | Busca Vetorial Direta |
| *"Quais são as magias de 2º círculo de evocação?"* | `Lista de Magias de 2º Círculo` + `Lista Evocação` | > 0.60 | Filtro Híbrido Combinado |
| *"Quais são as magias da escola de abjuração?"* | `Lista de Magias de Abjuração` | > 0.57 | Filtro Híbrido Escola |
| *"Quais são os custos em PM por círculo de magia?"* | `Lançando Magias (Custos em PM, Limite de Gasto)` | > 0.66 | Busca Vetorial Procedural |
