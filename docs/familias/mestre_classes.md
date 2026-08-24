# Famílias estruturadas: Fichas das 14 Classes (Capítulo 1) & O Mestre (Capítulo 6)

> **Status: CONCLUÍDO E INTEGRADO** (Frente Antigravity — Fechamento 100% de Tormenta20).  
> Este documento é a documentação completa e autossuficiente das famílias estruturadas de **Fichas e Progressão das 14 Classes** (Capítulo 1) e **O Mestre** (Ambientes, Masmorras, Perigos Complexos, Armadilhas, Doenças, Venenos de Aventura, Perseguições e Estrutura de Campanhas) de Tormenta20 (Edição Jogo do Ano).

---

## 1. Fonte no Livro

### 1.1. Capítulo 1: Fichas & Tabelas de Progressão das 14 Classes (págs. 36–88)
- As 14 classes oficiais de Tormenta20:
  1. **Arcanista** (Bruxo / Feiticeiro / Mago) — pág. 36
  2. **Bárbaro** (Fúria Selvagem) — pág. 40
  3. **Bardo** (Arte e Inspiração) — pág. 44
  4. **Bucaneiro** (Audácia e Panache) — pág. 48
  5. **Caçador** (Marca da Presa e Rastreador) — pág. 52
  6. **Cavaleiro** (Honra e Baluarte) — pág. 56
  7. **Clérigo** (Devoto Fiel e Magias Divinas) — pág. 60
  8. **Druida** (Forma Selvagem e Natureza) — pág. 64
  9. **Guerreiro** (Ataque Especial e Durão) — pág. 68
  10. **Inventor** (Engenhosidade, Engenhocas e Fabricação) — pág. 72
  11. **Ladino** (Ataque Furtivo e Especialista) — pág. 76
  12. **Lutador** (Briga Desarmada e Casca Grossa) — pág. 80
  13. **Nobre** (Autoconfiança, Comandar e Orgulho) — pág. 84
  14. **Paladino** (Golpe Divino, Cura pelas Mãos e Aura Sagrada) — pág. 88

### 1.2. Capítulo 6: O Mestre (págs. 246–287)
- **Estrutura de Campanhas e Sessões (págs. 246–265)**: Fases da aventura (Introdução, Motivação, Vitória Parcial, Clímax), Estilos de Campanha, Concessão de XP e Marcos Narrativos.
- **Ambientes Hostis & Masmorras (págs. 269–277)**: Portas e Iluminação de masmorras, Dano de Queda (1d6 por 1,5m até 20d6, amortecimento com Acrobacia CD 15), Fumaça e Sufocamento/Afogamento (Prender respiração: Con x 2 rodadas), Fogo e Clima Extremo (Frio Extremo e Calor Extremo).
- **Perigos Complexos & Armadilhas (págs. 278–281)**: Iniciativa de Perigo, Desarme com perícias acumuladas, Armadilhas mecânicas/mágicas com CD de percepção e ladinagem.
- **Doenças & Venenos de Aventura (págs. 282–285)**: Febre do Esgoto, Lepra, Peste Vermelha, Tétano com CD de Fortitude, Incubação e Dano diário; Venenos e Peçonhas.
- **Regras de Perseguição & NPCs (págs. 280–287)**: Testes de Atletismo/Pilotagem opostos em zonas de fuga/captura.

---

## 2. Extração Estruturada e Schema (`extrair_mestre_classes.py`)

A extração estruturada é salva em [`dados/mestre_classes.json`](file:///c:/LLM-Local/tormenta/dados/mestre_classes.json).

### 2.1. Resumo Comparativo das 14 Classes
| Classe | PV Inicial | PV/Nível | PM Inicial | PM/Nível | Proficiências | Perícias Básicas |
|---|---|---|---|---|---|---|
| **Arcanista** | 8 + Con | 2 + Con | 6 | 6 | Nenhuma | Misticismo, Vontade + 2 |
| **Bárbaro** | 24 + Con | 6 + Con | 3 | 3 | Marciais, Escudos | Fortitude, Luta + 4 |
| **Bardo** | 12 + Con | 3 + Con | 4 | 4 | Marciais | Atuação, Reflexos + 6 |
| **Bucaneiro** | 16 + Con | 4 + Con | 3 | 3 | Marciais | Reflexos + 4 |
| **Caçador** | 16 + Con | 4 + Con | 4 | 4 | Marciais, Escudos | Sobrevivência, Luta/Pontaria + 4 |
| **Cavaleiro** | 20 + Con | 5 + Con | 3 | 3 | Marciais, Pesadas, Escudos | Fortitude, Luta + 2 |
| **Clérigo** | 16 + Con | 4 + Con | 5 | 5 | Marciais, Pesadas, Escudos | Religião, Vontade + 2 |
| **Druida** | 16 + Con | 4 + Con | 4 | 4 | Marciais, Escudos (sem metal) | Sobrevivência, Vontade + 4 |
| **Guerreiro** | 20 + Con | 5 + Con | 3 | 3 | Marciais, Pesadas, Escudos | Fortitude, Luta/Pontaria + 2 |
| **Inventor** | 12 + Con | 3 + Con | 4 | 4 | Simples | Ofício, Vontade + 4 |
| **Ladino** | 12 + Con | 3 + Con | 4 | 4 | Marciais Leves | Ladinagem, Reflexos + 8 |
| **Lutador** | 20 + Con | 5 + Con | 3 | 3 | Nenhuma (desarmado) | Fortitude, Luta + 4 |
| **Nobre** | 16 + Con | 4 + Con | 4 | 4 | Marciais, Pesadas, Escudos | Diplomacia/Intimidação, Nobreza + 4 |
| **Paladino** | 20 + Con | 5 + Con | 3 | 3 | Marciais, Pesadas, Escudos | Luta, Vontade + 2 |

### 2.2. Regras Críticas de Ambiente e Perigos
- **Queda**: 1d6 por 1,5m (máx 20d6). Reação: Acrobacia CD 15 reduz 3m (2d6). Queda na água profunda: ignora 6m com Atletismo CD 15. Deixa o alvo Caído.
- **Sufocamento/Afogamento**: Prende respiração por `Con x 2` rodadas (cai pela metade em esforço). Ao esgotar: teste de Con CD 15 (+1 por teste). Falha deixa Inconsciente a 0 PV; próxima rodada sem ar = Morte.
- **Fogo**: 1d6 fogo/rodada. Apagar com ação padrão e Reflexos CD 15 (+5 rolando no chão).
- **Febre do Esgoto**: Mordida/esgoto. Incubação: 1d3 dias. Fortitude CD 15. Dano: 1d4 Destreza e Força por dia.

---

## 3. Visualizador Offline (`gerar_mestre_classes_html.py`)

A ferramenta [`dados/mestre_classes.html`](file:///c:/LLM-Local/tormenta/dados/mestre_classes.html) (25.6 KB) permite conferência offline:
- **Busca em tempo real**: Filtra instantaneamente por nomes de classes, perícias, proficiências, ambientes, regras de queda, afogamento, armadilhas, doenças e campanhas.
- **Chips de Categoria**: *Todos os Registros, 14 Classes de T20, Ambientes & Queda, Perigos & Armadilhas, Doenças & Venenos, Campanhas & Perseguições*.
- **Cards com Estatísticas e Tabelas**: Layout com badges de categoria e detalhamento completo de progressão e regras.
- **Alternador de Tema**: Claro e escuro.

---

## 4. Integração ao Índice FAISS (`integrar_mestre_classes.py`)

- **Substituição Cirúrgica**: Remove os 243 chunks antigos de texto corrido/classes dos Capítulos 1 e 6 e insere **22 chunks estruturados** de alta densidade.
- **Economia de Chunks e Precisão**: Total de chunks no índice otimizado para **1.484 chunks**.
- **Reconstrução Rápida**: Reconstitui os vetores em memória sem reembutir o restante do livro (~39s em CPU).
- **Backup Automático**: Salvo em `index/backup-<timestamp>/`.

---

## 5. Filtro Híbrido em `perguntar.py`

Os filtros `detectar_filtro_classe_progressao()` e `detectar_filtro_mestre()` interceptam buscas sobre:
- Fichas de classes (*"quantos PV ganha o guerreiro"*, *"quais as proficiências do clérigo"*, *"progressão do paladino"*)
- Lista de classes (*"quais são as classes de tormenta20"*, *"todas as classes"*)
- Queda e Ambientes (*"como funciona o dano de queda"*, *"regras de sufocamento"*, *"regras de fogo"*)
- Perigos e Armadilhas (*"como conduzir um perigo complexo"*, *"como desarmar armadilhas"*)
- Doenças e Venenos (*"como funciona a febre do esgoto"*, *"peste vermelha"*)
- Campanhas e Perseguições (*"como funcionam perseguições"*, *"fases da aventura"*)

---

## 6. Efeito Medido e Validação

| Pergunta | Chunk no Rank 1 | Score | Mecanismo |
|---|---|---|---|
| *"Quantos PV e PM o Guerreiro ganha por nivel e quais suas proficiencias?"* | `Ficha de Classe: Guerreiro` | 0.632 | Filtro Híbrido Classe |
| *"Como funciona a progressao e habilidades do Paladino do 1o ao 20o nivel?"* | `Ficha de Classe: Paladino` | 0.661 | Filtro Híbrido Classe |
| *"Como funciona o dano de queda e qual o dano maximo em Tormenta20?"* | `Regras de Ambiente: Queda e Impacto` | 0.624 | Filtro Híbrido Mestre |
| *"Como funcionam as regras de sufocamento e afogamento?"* | `Regras de Ambiente: Fumaça, Sufocamento e Afogamento` | 0.638 | Filtro Híbrido Mestre |
| *"Como funciona a doenca Febre do Esgoto e qual o teste de resistencia?"* | `Doenças e Venenos de Aventura` | 0.568 | Filtro Híbrido Mestre |
| *"Como conduzir um Perigo Complexo em Tormenta20?"* | `Sistema de Perigos Complexos e Armadilhas` | 0.553 | Filtro Híbrido Mestre |
