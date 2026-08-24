# Família estruturada: O Mundo de Arton (Capítulo 9)

> **Status: CONCLUÍDO E INTEGRADO** (Frente Antigravity).  
> Este documento é a documentação completa e autossuficiente da família estruturada do **Mundo de Arton** (Geografia, Reinos, Grandes Potências, Cidades Lendárias, Ermos, Ilhas e Linha do Tempo) de Tormenta20 (Edição Jogo do Ano).

---

## 1. Fonte no Livro

- **Capítulo 9: O Mundo de Arton** (páginas 364 a 397 do PDF / 358–391 na numeração impressa):
  - **Páginas 364–372**: Reinos do Reinado (*Deheon, Bielefeld, Wynlla, Namalkah, Ahlen, Zakharov, Pondsmânia*).
  - **Páginas 373–375**: Lugares Lendários (*A Academia Arcana, O Mercado nas Nuvens / Vectora*).
  - **Páginas 376–377**: Grandes Potências e Conflitos (*A Supremacia Purista, Conflagração do Aço, O Reino dos Mortos / Aslynn, Sambúrdia*).
  - **Páginas 378–389**: Além do Reinado (*Feudos de Trebuck, Sckharshantallas, Montanhas Sanguinárias, Montanhas Uivantes, Ermos Púrpuras, Império de Tauron, Smokestone, Tyrondir, Salistick, Svalas, Doherimm, Lenórienn*).
  - **Páginas 390–397**: Mares, Ilhas e Ameaças Globais (*Os Três Mares & Khubar, Galrasia / O Mundo Perdido, Lamnor & Duyshidakk, Tamu-ra / Império de Jade, Moreania, A Tormenta*).

---

## 2. Extração Estruturada e Schema (`extrair_mundo_arton.py`)

A extração estruturada é salva em [`dados/mundo_arton.json`](file:///c:/LLM-Local/tormenta/dados/mundo_arton.json).

### 2.1. Reinos do Reinado de Arton
| Reino | Título Descritivo | Capital / Sede | Regente / Líder | Divindades Principais |
|---|---|---|---|---|
| **Deheon** | O Reino Capital e Coração do Reinado | Valkaria | Rainha-Imperatriz Shivara Sharpblade | Valkaria, Khalmyr, Tanna-Toh |
| **Bielefeld** | O Reino dos Cavaleiros | Norm | Lorde Wolfram & Ordem da Luz | Khalmyr, Thyatis, Lin-Wu |
| **Wynlla** | O Reino da Magia | Sophand | Conselho dos Magos | Wynna, Tanna-Toh |
| **Namalkah** | O Reino dos Cavalos | Hippiontar | Khan das Estepes | Hippion, Thyatis, Allihanna |
| **Ahlen** | O Reino da Intriga | Thartann | Rei Thormy & Casa de Thartann | Hyninn, Sszzaas, Valkaria |
| **Zakharov** | O Reino das Armas | Rhond | Mestre Supremo dos Armeiros | Arsenal, Keenn, Khalmyr |
| **Pondsmânia** | O Reino das Fadas | Cidade Normal dos Humanos | Rainha das Fadas | Wynna, Allihanna, Nimb |

### 2.2. Grandes Potências e Nações Beligerantes
- **A Supremacia Purista**: Sede em Kannilar. Liderada pelo General Herman Von Krauser. Nação militarista e xenófoba humana em guerra aberta contra o Reinado na *Conflagração do Aço*.
- **O Império de Tauron**: Sede em Tiberus (em reconstrução) e Nova Malpetrim. Nação dos minotauros em crise política pós-queda do Deus Maior Tauron.
- **Continente Bestial (Lamnor & Duyshidakk)**: Sede em Urkk'thran e Rarnaakk. Liderada por Thwor Ironfist. Civilização dos povos goblinoides que conquistou o sul e as ruínas de Lenórienn.

### 2.3. Lugares Lendários
- **A Academia Arcana**: Maior escola de magia do multiverso, situada em um semiplano acessível por portais, governada pelo Mestre Supremo Talude.
- **Vectora (O Mercado nas Nuvens)**: Montanha invertida voadora governada pelo Arquimago Vectorius, o maior entreposto comercial de Arton.

### 2.4. Além do Reinado, Ermos, Mares e Ilhas
- **Salistick**: O Reino Sem Deuses, governado pelo Conselho de Médicos, centro da ciência médica e farmacologia de Arton.
- **Doherimm**: O Reino Subterrâneo dos Anões sob o Monte Paladon.
- **Sckharshantallas**: O Reino do Dragão Vermelho Ancião Sckhar.
- **As Montanhas Uivantes**: Região de frio polar e única fonte de Gelo Eterno.
- **Galrasia (O Mundo Perdido)**: Ilha isolada dominada por dinossauros pré-históricos e selva primordial.
- **Tamu-ra (O Império de Jade)**: Ilha oriental renascida após ser purificada da Tormenta, devotada a Lin-Wu.
- **Moreania**: Arquipélago habitado pelo povo moreau, fiéis aos Deuses Herdeiros (doze animais).
- **A Tormenta**: Tempestade rubra aberrante lefeu de Aharadak.

### 2.5. Linha do Tempo e Marcos Históricos de Arton
- **Ano 0**: Fundação do Reinado de Arton por refugiados de Lamnor liderados por Deheon.
- **Ano 1300+**: Guerra Infinita e Queda do reino élfico de Lenórienn para a Aliança Negra.
- **Ano 1400**: Primeira Invasão da Tormenta em Tamu-ra.
- **Ano 1405**: A Libertação de Valkaria por heróis lendários no Labirinto.
- **Ano 1410**: Guerras Táuricas (invasão dos minotauros ao Reinado).
- **Ano 1414**: Guerra Artoniana, Queda de Tauron e Ascensão de Thwor e Aharadak.
- **Ano 1420 (Atual)**: A Conflagração do Aço (Supremacia Purista vs Reinado).

---

## 3. Visualizador Offline (`gerar_mundo_arton_html.py`)

A ferramenta [`dados/mundo_arton.html`](file:///c:/LLM-Local/tormenta/dados/mundo_arton.html) (35.8 KB) permite conferência offline:
- **Busca em tempo real**: Filtra instantaneamente por nomes de reinos, capitais, regentes, divindades, cidades e ganchos.
- **Chips de Categoria**: *Todas as Regiões, Reinos do Reinado, Grandes Potências, Além do Reinado, Ermos & Montanhas, Ilhas & Mares, Lugares Lendários*.
- **Cards Geopolíticos**: Brasões, capitais, regentes, deuses adorados, cultura, pontos de interesse e ganchos de aventura para mestres e jogadores.
- **Linha do Tempo Integrada**: Cronologia histórica oficial de Arton.
- **Alternador de Tema**: Claro e escuro.

---

## 4. Integração ao Índice FAISS (`integrar_mundo_arton.py`)

- **Substituição Cirúrgica**: Remove os 113 chunks antigos de texto corrido do Capítulo 9 e insere **34 chunks estruturados** de alta densidade.
- **Economia de Chunks e Precisão**: Total de chunks no índice ajustado de 1.734 para **1.655 chunks**.
- **Reconstrução Rápida**: Reconstitui os vetores em memória sem reembutir o restante do livro (~113s em CPU).
- **Backup Automático**: Salvo em `index/backup-<timestamp>/`.

---

## 5. Filtro Híbrido em `perguntar.py`

O filtro `detectar_filtro_mundo_arton()` intercepta perguntas específicas de lore, geografia e reinos:
- Reinos (*"qual a capital de Deheon"*, *"quem governa Bielefeld"*, *"como é o reino de Zakharov"*)
- Cidades e Lugares Lendários (*"como funciona a cidade de Vectora"*, *"onde fica a Academia Arcana"*)
- Potências (*"o que é a Supremacia Purista"*, *"quem lidera a Aliança Negra"*, *"império de Tauron"*)
- Regiões Exóticas (*"por que Salistick é o reino sem deuses"*, *"reino dos anões Doherimm"*, *"Galrasia"*, *"Tamu-ra"*)
- Listas e História (*"quais os reinos do Reinado"*, *"linha do tempo de Arton"*)

As fontes recuperadas sobem automaticamente para o topo do ranking no pipeline RAG.

---

## 6. Efeito Medido e Validação

| Pergunta | Chunk no Rank 1 | Score | Mecanismo |
|---|---|---|---|
| *"Qual a capital de Deheon e quem é a Rainha-Imperatriz?"* | `Deheon (O Reino Capital e Coração do Reinado)` | 0.620 | Filtro Híbrido Reino |
| *"Como funciona a cidade voadora de Vectora?"* | `Vectora (O Mercado nas Nuvens)` | 0.641 | Filtro Híbrido Local |
| *"O que é a Supremacia Purista e quem a governa?"* | `A Supremacia Purista` | 0.638 | Filtro Híbrido Potência |
| *"Quais são os principais reinos que compõem o Reinado?"* | `Lista de Reinos do Reinado de Arton` | 0.524 | Filtro Híbrido Lista |
| *"Como é o Reino dos Anões de Doherimm?"* | `Doherimm (O Reino Subterrâneo dos Anões)` | 0.624 | Filtro Híbrido Reino |
| *"Por que Salistick é conhecido como o reino sem deuses?"* | `Salistick (O Reino Sem Deuses e a Terra da Medicina)` | 0.620 | Filtro Híbrido Reino |
