# Família estruturada: Ameaças / Bestiário (Capítulo 7)

> **Status: CONCLUÍDO E INTEGRADO** (Frente Antigravity).  
> Este documento é a documentação completa e autossuficiente da família estruturada de Ameaças (Bestiário e NPCs) de Tormenta20 (Edição Jogo do Ano).

---

## 1. Fonte no Livro

- **Capítulo 7: Ameaças** (páginas 286 a 329 do PDF do livro / páginas 280–323 na numeração impressa):
  - **Páginas 288–291**: Regras de Ameaças, anatomia do stat block, papéis de combate (*Solo, Lacaio, Bando, Normal*) e Tabela 7-1: Criaturas por Nível de Desafio.
  - **Páginas 292–322**: Bestiário canônico com todas as **80 criaturas/monstros** divididas em 9 grupos ecológicos e temáticos.
  - **Páginas 323–327**: Regras de Perigos Simples, Perigos Ambientais (*Fogo, Frio, Queda, Sufocamento*) e Perigos Complexos.
  - **Páginas 328–329**: Criação de NPCs e Tabela 7-2: Estatísticas de NPC por Patamar (*Iniciante, Veterano, Campeão, Lendário*).

---

## 2. Extração por Tipografia e Schema (`extrair_ameacas.py`)

A extração utiliza `PyMuPDF` (`get_text("dict")` e mapeamento posicional da Tabela 7-1), extraindo o stat block fiel de cada criatura:

| Elemento | Tipografia / Padrão | Função no Schema |
|---|---|---|
| **Nome da Criatura** | `Tormenta20-Regular` ~21 pt | Nome canônico da criatura |
| **Nível de Desafio** | `Tormenta20-Regular` ~16 pt | `nd` (1/4, 1/2, 1, 2, ..., 20) |
| **Tipo & Tamanho** | `SourceSansPro-It` ~9 pt | `tipo_criatura`, `subtipo`, `tamanho`, `papel` (*Solo, Lacaio, Bando*) |
| **Iniciativa & Percepção** | `SourceSansPro-Bold` 9 pt | `iniciativa`, `percepcao`, `sentidos` (*visão no escuro, faro, etc.*) |
| **Defesa & Resistências** | `SourceSansPro-Bold` 9 pt | `defesa`, `fortitude`, `reflexos`, `vontade`, `resistencias` |
| **PV & PM** | `SourceSansPro-Bold` 9 pt | `pv`, `pm` |
| **Deslocamento** | `SourceSansPro-Bold` 9 pt | `deslocamento` (terrestre, voo, natação, escavação) |
| **Ataques** | `SourceSansPro-Bold` 9 pt | `corpo_a_corpo`, `distancia` |
| **Habilidades Especiais** | `SourceSansPro-Bold` 9 pt | `habilidades` (*nome, ação padrão/livre/completa, CD, efeito*) |
| **Atributos** | `SourceSansPro-Bold` 9 pt | `atributos` (`for`, `des`, `con`, `int`, `sab`, `car`) |
| **Perícias & Equipamento** | `SourceSansPro-Bold` 9 pt | `pericias`, `equipamento` |
| **Tesouro** | `SourceSansPro-Bold` 9 pt | `tesouro` (*Nenhum, Metade, Padrão, Dobro, matérias-primas*) |

Rode com:
```powershell
python extrair_ameacas.py
```
Gera [`dados/ameacas.json`](file:///c:/LLM-Local/tormenta/dados/ameacas.json) com **80 criaturas tipadas** e **3 blocos procedurais de regras**.

### Distribuição por Grupo (80 Criaturas)
1. **Masmorras (11)**: Glop (1/4), Rato Gigante (1/4), Orc Combatente (1/2), Orc Chefe (2), Orc Mutante (5), Aranha Gigante (2), Gárgula (2), Guerreiro de Chifres (3), Mantícora (6), Centopeia-dragão (7), Golem de Ferro (10).
2. **Ermos (18)**: Bandido (1/4), Chefe Bandido (1), Guarda de Cidade (1/2), Sargento da Guarda (1), Lobo (1/2), Centauro Combatente (1), Centauro Xamã (3), Gnoll Saqueador (1), Gnoll Filibusteiro (2), Gorlogg (1), Trog (1), Lobo-das-cavernas (2), Cão do Inferno (3), Grifo (3), Basilisco (4), Ogro (4), Urso-Coruja (4), Serpe (5).
3. **Supremacia Purista (7)**: Recruta Purista (1/2), Soldado Purista (1), Sargento-mor (3), Capelão de Guerra (4), Capitão-baluarte (5), Cavaleiro do Leopardo (9), Colosso Supremo (14).
4. **Reino dos Mortos (8)**: Zumbi (1/4), Turba Zumbi (2), Esqueleto (2), Esqueleto de Elite (4), Falange (8), Aparição (5), Necromante (7), Vampiro (12).
5. **Duyshidakk / Aliança Negra (8)**: Goblin Salteador (1/4), Hobgoblin Soldado (2), Goblin Engenhoqueiro (3), Arauto de Thwor (4), Hobgoblin Mago de Batalha (5), Engenho de Guerra Goblin (6), Devorador de Medos (8), Sombra de Thwor (9).
6. **Culto de Sszzaas (9)**: Cascavel (1/4), Jiboia (1/2), Naja (1), Sucuri (3), Nagah Guardião (3), Nagah Mística (6), Cultista de Sszzaas (7), Hidra (11), Lagash (13).
7. **Trolls Nobres / Finntroll (5)**: Finntroll Caçador (2), Finntroll Feitor (6), Ganchador (5), Troll (5), Troll das Cavernas (9).
8. **Dragões (7)**: Enxame Kobold (2), Dragão Filhote (3), Dragão Jovem (7), Dragão Adulto (11), Dragão Venerável (15), Dragão-rei (20), Tirano do Terceiro (10).
9. **Ameaças da Tormenta / Lefeu (7)**: Maníaco Lefou (2), Uktril (3), Geraktril (6), Reishid (8), Otyugh (5), Thuwarokk (16), Sacerdote de Aharadak (10).

---

## 3. Schema de Dados

Cada criatura em [`dados/ameacas.json`](file:///c:/LLM-Local/tormenta/dados/ameacas.json) segue o schema:

```json
{
  "id": "ameaca_dragao_adulto",
  "tipo_entidade": "ameaca",
  "nome": "Dragão Adulto",
  "grupo": "Dragões",
  "nd": "11",
  "tipo_criatura": "Monstro",
  "subtipo": "",
  "tamanho": "Enorme",
  "papel": "Solo",
  "iniciativa": "+14",
  "percepcao": "+14",
  "sentidos": "faro, visão no escuro",
  "defesa": 34,
  "fortitude": "+24",
  "reflexos": "+18",
  "vontade": "+16",
  "resistencias": "imunidade a paralisia e sono, redução de dano 10, redução de fogo 20",
  "pv": 450,
  "pm": 15,
  "deslocamento": "12m (8q), voo 24m (16q)",
  "corpo_a_corpo": "Mordida +25 (2d6+14, 19) e duas garras +25 (1d10+14, 19) e cauda +25 (1d8+14, 19)",
  "distancia": "",
  "habilidades": [
    {
      "nome": "Sopro (Padrão)",
      "descricao": "Cone de 9m, dano 10d12 fogo (Ref CD 28 reduz à metade). Recarga (1d4 rodadas)."
    }
  ],
  "atributos": {
    "for": "8", "des": "2", "con": "6", "int": "2", "sab": "2", "car": "2"
  },
  "pericias": "Misticismo +14, Intimidação +14",
  "equipamento": "",
  "tesouro": "Dobro e 2 peças de couro de dragão",
  "pagina": 317
}
```

---

## 4. Conferência Visual (`gerar_ameacas_html.py`)

A ferramenta [`dados/ameacas.html`](file:///c:/LLM-Local/tormenta/dados/ameacas.html) (402 KB) permite visualizar, pesquisar e filtrar todas as 80 fichas de criaturas offline:
- **Busca em tempo real**: Filtra por nome da criatura, grupo, ND, ataque, habilidade, defesa ou perícia.
- **Filtros por Grupo**: Chips interativos (*Masmorras, Ermos, Puristas, Mortos-Vivos, Duyshidakk, Sszzaazitas, Trolls, Dragões, Tormenta*).
- **Filtros por Faixa de ND**: *Iniciante (1/4 a 1)*, *Veterano (2 a 4)*, *Campeão (5 a 9)*, *Lendário (10 a 20)*.
- **Cards de Stat Block completos**: Layout fiel com badges de ND, grid de Defesa/PV/PM/Resistências, ataques formatados, atributos e habilidades.
- **Alternador de Tema**: Suporte a modo claro e escuro.

Rode para atualizar:
```powershell
python gerar_ameacas_html.py
```

---

## 5. Integração ao Índice FAISS (`integrar_ameacas.py`)

O script [`integrar_ameacas.py`](file:///c:/LLM-Local/tormenta/integrar_ameacas.py) substitui o Capítulo 7 no índice vetorial:
1. Faz backup automático em `index/backup-<timestamp>/`.
2. Reconstrói vetores em memória (`index.reconstruct_n`) para todas as famílias anteriores sem reembuti-las.
3. Remove os 96 chunks antigos de texto corrido do Capítulo 7 (págs. 286–329).
4. Insere **96 novos chunks estruturados**:
   - **80 chunks individuais de monstros**: 1 por criatura com stat block verbalizado completo.
   - **9 chunks-lista por Grupo**: listagens completas com ND, Defesa e PV de cada criatura do grupo.
   - **4 chunks-lista por Faixa de ND**: listagens de Iniciante, Veterano, Campeão e Lendário.
   - **3 chunks procedurais de regras**: Papéis de Ameaças (*Solo, Lacaio, Bando*), Perigos Complexos e Tabela de NPCs.
5. Embuti somente os 96 novos chunks com `BAAI/bge-m3` e salva `tormenta.faiss`, `chunks.jsonl` e `meta.json` (`ameacas_estruturadas: 80`).
6. Total de chunks no índice: **1.779 chunks**.

Rode com:
```powershell
python integrar_ameacas.py
```

---

## 6. Filtro Híbrido em `perguntar.py`

A função `detectar_filtro_ameaca()` detecta consultas de listagem e agrupamento:
- Por ND: *"monstros de ND 5"*, *"criaturas com ND 1/2"*
- Por Faixa: *"monstros iniciantes"*, *"ameaças lendárias"*
- Por Grupo: *"ameaças da Tormenta"*, *"monstros de masmorra"*, *"tropas puristas"*

O hook em `buscar()` prioriza as criaturas e listas no topo do ranking. O log em `consultar()` registra `filtro_ameaca` em `logs/consultas.jsonl`.

---

## 7. Efeito Medido e Validação

| Pergunta | Chunk no Rank 1 | Score | Mecanismo |
|---|---|---|---|
| *"Qual a defesa e PV do Dragão Adulto?"* | `Dragão Adulto (ND 11)` | 0.593 | Busca Vetorial Direta |
| *"O que faz o ataque de garras do Guerreiro de Chifres?"* | `Guerreiro de Chifres (ND 3)` | 0.625 | Busca Vetorial Direta |
| *"Quais criaturas são do grupo da Tormenta?"* | `Lista de Criaturas: Tormenta` + Uktril/Geraktril | 0.603 | Filtro Híbrido Grupo |
| *"Quais monstros têm ND 5?"* | `Ganchador (ND 5)` / `Troll (ND 5)` / `Otyugh (ND 5)` | > 0.48 | Filtro Híbrido ND |
| *"Como funcionam os Perigos Complexos?"* | `Regras de Perigos, Armadilhas e Perigos Complexos` | 0.574 | Busca Vetorial Procedural |
| *"Quais as características de uma criatura Solo?"* | `Regras de Ameaças e Papéis de Combate (Solo, Lacaio e Bando)` | 0.581 | Busca Vetorial Procedural |
