# Família estruturada: Recompensas, Itens Mágicos & Artefatos (Capítulo 8)

> **Status: CONCLUÍDO E INTEGRADO** (Frente Antigravity).  
> Este documento é a documentação completa e autossuficiente da família estruturada de **Recompensas** (Encantos de Armas e Armaduras, Armas e Armaduras Específicas, Acessórios Mágicos, Artefatos Supremos, Poções, Pergaminhos e Tabelas de Tesouro por ND) de Tormenta20 (Edição Jogo do Ano).

---

## 1. Fonte no Livro

- **Capítulo 8: Recompensas** (páginas 330 a 355 do PDF / 324–349 na numeração impressa):
  - **Páginas 332–338**: Pontos de Experiência (XP), Avanço por Marcos, Tabela 8-1 (Riqueza e Tesouro por ND) e Regras de Controle de Riqueza.
  - **Páginas 339–340**: Regras de Uso de Itens Mágicos (Limite de até 4 itens vestidos/empunhados simultâneos), Fabricação e Destruição/RD de Itens Mágicos.
  - **Páginas 341–342**: Encantos de Armas (29 encantamentos: *Aborrecedora, Ameaçadora, Antagônica, Assassina, Congelante, Drenante, Eletrizante, Flamejante, Lancinante, Sagrada, Sanguinária, Tumular, Veloz, Vorpal*, etc.).
  - **Páginas 342–344**: Armas Específicas (*Arco do Poder, Azagaia do Relâmpago, Chicote de Presas, Espada da Justiça, Espada Solar, Lança da Montaria, Machado das Tempestades, Maça do Terror, Martelo do Trovão, Tridente do Povo do Mar*).
  - **Páginas 344–346**: Encantos de Armaduras e Escudos (24 encantamentos: *Abençoada, Animada, Bastião, Defensora, Fortificada, Guardiã, Impenetrável, Invulnerável, Protetora, Refletora, Retribuidora, Salteadora, Sombria*, etc.).
  - **Páginas 346–347**: Armaduras e Escudos Específicos (*Armadura da Donzela, Armadura do Dragão, Carapaça de Ferro, Cota da Rapidez, Escudo de Valkaria, Escudo Espelho, Manto de Teias, Placas do Titã*).
  - **Páginas 347–348**: Poções & Pergaminhos (regras e tabelas de preço por círculo de magia 1º ao 5º).
  - **Páginas 348–351**: Acessórios Mágicos (18 principais: *Anéis, Botas, Braçadeiras, Brincos, Broches, Capas, Cintos, Colares, Luvas, Mantos, Pingentes, Tapete Voador, Tiaras*).
  - **Páginas 352–355**: Artefatos Supremos (*A Espada-Deus / Holy Avenger, A Joia da Alma, O Baralho do Caos, O Olho de Sszzaas, Os Rubis da Virtude, O Cetro das Cores, O Crânio Negro*).

---

## 2. Extração Estruturada e Schema (`extrair_recompensas.py`)

A extração estruturada é salva em [`dados/recompensas.json`](file:///c:/LLM-Local/tormenta/dados/recompensas.json).

### 2.1. Regras Fundamentais de Itens Mágicos
- **Limite de 4 Itens**: Um personagem só pode obter benefícios de até 4 itens mágicos vestidos ou empunhados simultaneamente.
- **Fabricação**: Exige a habilidade Fabricar Item Mágico (ou Inventor/Arcanista), matéria-prima igual a 1/3 do preço em T$ e investimento em PM permanentes.
- **Destruição**: Itens mágicos possuem RD e PV substancialmente ampliados (+5 de RD por encanto).

### 2.2. Tabela de Preços de Poções e Pergaminhos
| Círculo de Magia | Preço da Poção | Preço do Pergaminho |
|---|---|---|
| **1º Círculo** | T$ 30 | T$ 15 |
| **2º Círculo** | T$ 150 | T$ 75 |
| **3º Círculo** | T$ 450 | T$ 225 |
| **4º Círculo** | T$ 1.050 | T$ 525 |
| **5º Círculo** | T$ 2.250 | T$ 1.125 |

### 2.3. Principais Encantos de Armas e Armaduras
- **Flamejante (+1 encanto)**: +1d6 de dano de fogo e ilumina como tocha.
- **Ameaçadora (+1 encanto)**: Dobra a margem de ameaça da arma.
- **Drenante (+2 encantos)**: Em acerto crítico, recupera PV iguais a metade do dano total causado.
- **Vorpal (+3 encantos)**: Ao rolar 20 natural no ataque cortante, decapita a criatura instantaneamente.
- **Animada (+2 encantos, apenas escudos)**: Escudo flutua sozinho e protege sem ocupar as mãos.
- **Fortificada (+2 encantos)**: 75% de chance de anular críticos e ataques furtivos sofridos.
- **Invulnerável (+3 encantos)**: Concede Redução de Dano (RD) 10 contra dano físico.

### 2.4. Os 7 Artefatos Supremos de Arton
- **A Espada-Deus (Holy Avenger)**: Espada bastarda vorpal sagrada de Khalmyr; causa dano de essência absoluto e concede milagres divinos.
- **A Joia da Alma**: Diamante com centelha de Deus Maior caído; absorve almas e fornece PM ilimitados para rituais.
- **O Baralho do Caos**: Baralho de marfim de Nimb que altera a realidade (desejos, mortes ou transformações).
- **O Olho de Sszzaas**: Joia de esmeralda que confere onisciência sobre segredos e controle mental de regentes.
- **Os Rubis da Virtude**: Vinte gemas que concentram a ambição cósmica de Valkaria e permitem ascensão divina.
- **O Cetro das Cores**: Cetro primordial de Wynna; conjura qualquer magia sem custo de PM e anula feitiços inimigos.
- **O Crânio Negro**: Relíquia necromântica que ergue exércitos de mortos-vivos e drena a vida de regiões inteiras.

---

## 3. Visualizador Offline (`gerar_recompensas_html.py`)

A ferramenta [`dados/recompensas.html`](file:///c:/LLM-Local/tormenta/dados/recompensas.html) (38.3 KB) permite conferência offline:
- **Busca em tempo real**: Filtra instantaneamente por nomes de encantos, armas, armaduras, acessórios, artefatos, preços ou efeitos.
- **Chips de Categoria**: *Todos os Itens, Encantos de Armas, Armas Específicas, Encantos de Armaduras, Armaduras Específicas, Acessórios Mágicos, Artefatos Supremos, Regras de Tesouro*.
- **Cards com Preço e Espaço**: Layout com badges de categoria, detalhes de custo/espaço e condições de destruição de artefatos.
- **Alternador de Tema**: Claro e escuro.

---

## 4. Integração ao Índice FAISS (`integrar_recompensas.py`)

- **Substituição Cirúrgica**: Remove os 54 chunks antigos de texto corrido do Capítulo 8 e insere **104 chunks estruturados** de alta densidade.
- **Economia de Chunks e Precisão**: Total de chunks no índice ajustado de 1.655 para **1.705 chunks**.
- **Reconstrução Rápida**: Reconstitui os vetores em memória sem reembutir o restante do livro (~62s em CPU).
- **Backup Automático**: Salvo em `index/backup-<timestamp>/`.

---

## 5. Filtro Híbrido em `perguntar.py`

O filtro `detectar_filtro_recompensa()` intercepta perguntas específicas de itens mágicos e tesouros:
- Encantos de armas (*"o que faz o encanto flamejante"*, *"arma vorpal"*, *"arma ameaçadora"*)
- Encantos de armaduras (*"armadura fortificada"*, *"escudo animado"*, *"armadura invulnerável"*)
- Itens específicos (*"arco do poder"*, *"armadura do dragão"*, *"escudo de valkaria"*)
- Acessórios mágicos (*"anel de regeneração"*, *"botas aladas"*, *"tiara do intelecto"*)
- Artefatos (*"como funciona a Holy Avenger"*, *"o que faz o Baralho do Caos"*, *"Rubis da Virtude"*)
- Regras & Tabelas (*"quantos itens mágicos posso usar"*, *"tabela de tesouro por ND"*, *"preço de poções"*)

As fontes recuperadas sobem automaticamente para o topo do ranking no pipeline RAG.

---

## 6. Efeito Medido e Validação

| Pergunta | Chunk no Rank 1 | Score | Mecanismo |
|---|---|---|---|
| *"O que faz o encanto de arma Flamejante e quanto custa?"* | `Encanto de Arma: Flamejante` | 0.677 | Filtro Híbrido Encanto |
| *"Como funciona a Espada-Deus Holy Avenger e quais seus poderes?"* | `Artefato: A Espada-Deus (Holy Avenger)` | 0.613 | Filtro Híbrido Artefato |
| *"Quais são os encantos mágicos para armaduras e escudos?"* | `Lista de Encantos de Armaduras e Escudos` | 0.703 | Filtro Híbrido Lista |
| *"O que faz o acessório Anel de Regeneração?"* | `Acessório Mágico: Anel de Regeneração` | 0.659 | Filtro Híbrido Acessório |
| *"Quantos itens mágicos um personagem pode usar simultaneamente em Tormenta20?"* | `Regras de Uso e Sintonia de Itens Mágicos` | 0.675 | Filtro Híbrido Regra |
| *"Como funciona a Tabela de Tesouro por ND?"* | `Tabela 8-1: Riqueza e Tesouros por Nível de Desafio (ND)` | 0.630 | Filtro Híbrido Regra |
