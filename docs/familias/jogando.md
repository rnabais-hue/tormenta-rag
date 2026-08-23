# Família estruturada: Regras de Jogo, Combate & Parceiros (Capítulo 5 & Capítulo 6)

> **Status: CONCLUÍDO E INTEGRADO** (Frente Antigravity).  
> Este documento é a documentação completa e autossuficiente da família estruturada de Regras de Jogo (Combate, Ações, Manobras, Táticas, Ferimentos, Descanso e Parceiros) de Tormenta20 (Edição Jogo do Ano).

---

## 1. Fonte no Livro

- **Capítulo 5: Jogando** (páginas 218 a 245 do PDF / 212–239 na numeração impressa):
  - **Páginas 220–229**: Resolução de Testes (CDs 5 a 30), Sucesso/Falha automática (1 e 20), Escolher 10/20, Ajudar e Testes Estendidos.
  - **Páginas 230–235**: Habilidades Universais (*Faro, Imunidades, Percepção às Cegas, RD, Resistência a Energia, Visão na Penumbra/Escuro*), Áreas, Alcance e Regras de Acúmulo de Bônus.
  - **Páginas 236–238**: Estatísticas de Combate, Teste de Ataque, Tipos de Dano (*Físico, Elemental, Mágico*), Acertos Críticos e Iniciativa.
  - **Páginas 239–241**: A Rodada de Combate, Economia de Ações (*Padrão, Movimento, Completa, Livres e Reações*) e 7 Manobras de Combate (*Agarrar, Atropelar, Derrubar, Desarmar, Empurrar, Fintar, Quebrar*).
  - **Páginas 242–243**: Ferimentos, 0 PV, Sangrando, Teste de Estabilização (CD 15 Con), Morte, Dano Não Letal e Tabela de Condições de Descanso (*Ruim, Normal, Confortável, Luxuoso*).
  - **Páginas 244–245**: Situações Táticas Especiais (*Flanquear, Cobertura, Camuflagem, Terreno Difícil*), Tabela 5-3 (Modificadores) e Tabela 5-4 (Quebrando Objetos).
- **Capítulo 6: O Mestre** (páginas 266 a 268 do PDF):
  - **Páginas 266–268**: Sistema de Parceiros / Aliados (10 Tipos x 3 Tiers: Iniciante, Veterano, Mestre), limites por patamar e regras de Montarias.

---

## 2. Extração Estruturada e Schema (`extrair_regras_jogo.py`)

A extração estruturada é salva em [`dados/regras_jogo.json`](file:///c:/LLM-Local/tormenta/dados/regras_jogo.json).

### 2.1. Manobras de Combate (7 Manobras)
| Manobra | Ação | Teste Exigido | Efeito |
|---|---|---|---|
| **Agarrar** | Padrão | Luta oposto | Alvo e atacante ficam Agarrados (desprevenido e imóvel, –2 no ataque). Manter gasta ação padrão por rodada. |
| **Atropelar** | Padrão (em mov.) | Luta/Atletismo oposto a Luta/Reflexos | Passa pelo espaço do inimigo e deixa-o Caído. |
| **Derrubar** | Padrão | Luta oposto | Alvo fica Caído (–5 Defesa corpo a corpo, +5 à distância, –5 no ataque). |
| **Desarmar** | Padrão | Luta oposto | Derruba o item empunhado pelo oponente no mesmo quadrado. |
| **Empurrar** | Padrão | Luta oposto | Empurra o oponente 1,5m (+1,5m para cada 5 pontos de diferença no teste). |
| **Fintar** | Padrão | Enganação oposto a Reflexos | Alvo fica Desprevenido contra o próximo ataque até o final do próximo turno. |
| **Quebrar** | Padrão | Ataque vs Def/Luta do item | Causa dano no item empunhado (subtrai a RD do material). |

### 2.2. Sistema de Parceiros (10 Tipos x 3 Tiers)
| Parceiro | Nível Iniciante | Nível Veterano | Nível Mestre |
|---|---|---|---|
| **Ajudante** | +2 em duas perícias | +2 em três perícias | +4 em três perícias |
| **Atirador** | +1d6 no dano à distância 1x/rodada | +1d10 no dano à distância | +2d8 no dano à distância |
| **Combatente** | +2 em testes de ataque | +3 em testes de ataque | +4 em ataque e +1 na margem de ameaça |
| **Conjurador** | 1x/rodada causa 1d6 de dano elemental | Causa 2d6 de dano elemental | Causa 3d6 e –1 PM em magias de 1º e 2º círculos |
| **Curandeiro** | 1x/rodada cura 1d8+1 PV adjacente | Cura 2d8+2 PV e remove condição leve | Cura 3d8+3 PV e recupera 1d8 PV para si mesmo |
| **Destruidor** | Dano de magias aumenta +1 dado | Dano de magias +1 dado e +1 na CD | Dano de magias +2 dados e +2 na CD |
| **Fortão** | +1d8 no dano corpo a corpo 1x/rodada | +1d12 no dano corpo a corpo | +2d10 no dano e manobra Derrubar livre após acertar |
| **Guardião** | +2 na Defesa | +3 na Defesa | +4 na Defesa e Redução de Dano (RD) 5 |
| **Perseguidor** | +2 em Percepção e Sobrevivência | Habilidade Sentidos Aguçados | Percepção às Cegas em alcance curto |
| **Vigilante** | +2 em Percepção e Iniciativa | Habilidade Esquiva Sobrenatural | Não é surpreendido e +5 em Iniciativa |

### 2.3. Tabela de Condições de Descanso (8 horas)
- **Ruim** (relento, lama, frio, armadura pesada): Nenhum PV e nenhum PM recuperado.
- **Normal** (acampamento padrão com saco de dormir e fogueira): Recupera **1x nível** em PV e PM.
- **Confortável** (boa estalagem, cama quente, refeição nutritiva): Recupera **2x nível** em PV e PM.
- **Luxuoso** (mansão nobre, banho quente, comida farta): Recupera **3x nível** em PV e PM.

---

## 3. Visualizador Offline (`gerar_regras_jogo_html.py`)

A ferramenta [`dados/regras_jogo.html`](file:///c:/LLM-Local/tormenta/dados/regras_jogo.html) (29 KB) permite navegar offline:
- **Busca em tempo real**: Filtra instantaneamente por nomes de manobras, tipos de ação, modificadores, CDs, fórmulas de dano ou benefícios de parceiros.
- **Chips de Categoria**: *Todas, Manobras de Combate, Ações de Combate, Modificadores Táticos, Ferimentos & Descanso, Parceiros / Aliados, Habilidades Universais, Tipos de Dano*.
- **Cards com Fórmulas e Tabelas**: Layout de referência rápida com caixas de fórmulas em destaque e tabelas comparativas.
- **Alternador de Tema**: Claro e escuro.

---

## 4. Integração ao Índice FAISS (`integrar_regras_jogo.py`)

- **Substituição Cirúrgica**: Remove os 93 chunks antigos de texto corrido do Capítulo 5 e insere **48 chunks estruturados** de alta densidade.
- **Economia de Chunks e Precisão**: Total de chunks no índice ajustado para **1.734 chunks**.
- **Reconstrução Rápida**: Reconstitui os vetores em memória sem reembutir o restante do livro (~32s em CPU).
- **Backup Automático**: Salvo em `index/backup-<timestamp>/`.

---

## 5. Filtro Híbrido em `perguntar.py`

O filtro `detectar_filtro_regra_jogo()` intercepta perguntas específicas de combate e regras:
- Manobras (*"como funciona a manobra agarrar"*, *"quais são as manobras de combate"*)
- Ações (*"quais são as ações padrão"*, *"ações completas"*)
- Táticas (*"como funciona flanquear"*, *"regras de cobertura"*, *"camuflagem"*)
- Ferimentos & Descanso (*"como funciona o descanso luxuoso"*, *"o que acontece com 0 PV"*, *"teste de estabilização"*)
- Parceiros (*"quais os tipos de parceiros"*, *"parceiro guardião"*, *"parceiro curandeiro"*)

As fontes recuperadas sobem automaticamente para o topo do ranking no pipeline RAG.

---

## 6. Efeito Medido e Validação

| Pergunta | Chunk no Rank 1 | Score | Mecanismo |
|---|---|---|---|
| *"Como funciona a manobra agarrar e qual teste é exigido?"* | `Manobra de Combate: Agarrar` | 0.670 | Filtro Híbrido Manobra |
| *"Quais são os tipos de ações em combate em Tormenta20?"* | `A Rodada de Combate e Economia de Ações` | 0.584 | Filtro Híbrido Ações |
| *"Como funciona a recuperação de PV e PM no descanso luxuoso?"* | `Descanso e Recuperação de PV e PM` | 0.675 | Filtro Híbrido Descanso |
| *"Quais os benefícios de um parceiro Guardião mestre?"* | `Parceiro: Guardião` | 0.624 | Filtro Híbrido Parceiro |
| *"Qual o bônus de ataque por flanquear e como funciona a cobertura?"* | `Modificador Tático: Flanquear` | 0.673 | Filtro Híbrido Tática |
| *"Como funciona o teste de estabilização quando um personagem chega a 0 PV?"* | `Pontos de Vida Zero, Sangrando e Estabilização` | 0.710 | Filtro Híbrido Ferimento |
