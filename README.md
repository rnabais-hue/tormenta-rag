# Projeto RAG — Tormenta20

Perguntar ao **livro de Tormenta20** (RPG) em linguagem natural, usando **RAG**
(Retrieval-Augmented Generation) com um modelo de linguagem **local e
quantizado**. Tudo roda **offline, na CPU, fora do Google Drive**.

> **Este README é a fonte-de-verdade do projeto.** Ele reflete o estado real do
> código e é autossuficiente: uma pessoa (ou outra IA) deve conseguir entender e
> continuar o projeto lendo só este arquivo + os scripts. Se você alterar o
> comportamento, **atualize este README junto**.
>
> **Documentação modular (`docs/`):** para permitir trabalho paralelo sem conflito,
> componentes/famílias novas são documentados em arquivos próprios em [`docs/`](docs/)
> (ex.: [Magia](docs/familias/magia.md), [MCP](docs/mcp.md)); este README permanece o
> índice. Regra: cada frente edita **só o seu** arquivo de doc.
>
> **Versionamento:** o repositório git versiona **apenas a ferramenta** (código). O
> `.gitignore` exclui `livro/`, `index/`, `dados/`, `logs/`, `models/` — dados
> derivados do livro (protegidos). Para compartilhar: distribua o código; cada
> usuário gera o índice do **próprio exemplar**.

Contexto da máquina: Windows 11, Intel Core Ultra 7 258V, GPU Intel Arc **sem
CUDA → tudo em CPU**. Projeto em `C:\LLM-Local\tormenta\` (disco local, fora do
Drive, para performance e para não sincronizar GBs).

---

## 1. Estado atual (o que já funciona)

- [x] PDF do livro em `livro\` (exemplar próprio, uso pessoal).
- [x] Dependências instaladas (ver §6).
- [x] **Ingestão pronta** (`ingestao.py`) → índice gerado em `index\`
      (**1165 chunks** brutos da ingestão via TOC; hoje **~1498 chunks** após
      integrar as famílias estruturadas — ver §11 —, embeddings bge-m3, FAISS).
- [x] **Consulta pronta** (`perguntar.py`) → busca + Qwen3-8B via Ollama, com
      citação de fonte (seção/página).
- [x] **Interface web de testes** (`interface.py`) com **streaming** e **logs**.
- [x] Atalho na Área de Trabalho + `.bat` que cuida do Ollama.
- [ ] Melhorar recuperação nos casos catalogados como "Problema" (ver §9 e §10).
- [x] **Conhecimento estruturado — raças**: 17 raças em `dados/racas.json`,
      **integradas ao índice** (rank 1 nas perguntas de raça) e com **filtro
      híbrido por metadado** ("raças com bônus de Carisma"). Ver §11.
- [x] **Conhecimento estruturado — classes**: 14 classes em `dados/classes.json`,
      **integradas ao índice** (1 chunk de visão geral + 1 por habilidade;
      rank 1 nas perguntas de classe). Inclui o **atributo principal no texto do chunk**
      (Tabela 1-3, `extrair_atributos_classe.py`+`integrar_atributo_classe.py`) — resolve
      "qual o atributo do paladino?" (=Força e Carisma) via RAG puro. Ver §11.
- [x] **Poderes de classe (Stage A)**: 296 poderes em `dados/poderes_classe.json`,
      **integrados ao índice** (1 chunk fino por poder + 1 chunk-lista por classe;
      substituem os 14 chunks grossos "Poder de X"). Ver §11.
- [x] **Poderes gerais (Stage A)**: 162 poderes (combate/destino/magia/concedidos/
      tormenta) em `dados/poderes_gerais.json`, **integrados ao índice** (1 chunk por
      poder + listas por categoria e por deus). Concedidos trazem o(s) **deus(es)**
      concedente(s). Ver §11.
- [x] **Poderes — Stages B/C/D (motor relacional)**: **B** predicados
      (`pre_requisito_estruturado`, 219 poderes, `estruturar_prereqs.py`); **C**
      elegibilidade derivada (`elegibilidade.py` — categoria→acesso, conjuração,
      devoção→deuses→devotos); **D** motor do personagem (`personagem.py`) que avalia
      B+C: "poderes disponíveis agora" e "árvore de pré-requisitos". **Integrado ao RAG**
      (`perguntar.py`: intenções de planejamento e elegibilidade por classe). Ver §11.
- [x] **Conhecimento estruturado — perícias**: 29 perícias em `dados/pericias.json`
      (atributo-chave + flags "só treinada"/"penalidade de armadura" + usos),
      **integradas ao índice** (1 chunk/perícia) e com **filtro híbrido por metadado**
      ("perícias de Destreza", "perícias só treinadas"). Ver §11.
- [x] **Conhecimento estruturado — origens**: 35 origens em `dados/origens.json`
      (itens, perícias e poderes concedidos, poder único), **integradas ao índice**
      (1 chunk/origem) e com **filtro híbrido** ("quais origens dão a perícia Cura",
      "origens que concedem o poder Vontade de Ferro"). Ver §11.
- [x] **Conhecimento estruturado — deuses**: 20 deuses em `dados/deuses.json` (energia,
      arma, símbolo, crenças, devotos, poderes concedidos, obrigações), **integrados ao
      índice** (1 chunk/deus) e com **filtro híbrido** por energia e por devoto ("quais
      deuses um paladino pode seguir" — casa acento/plural). Ver §11.
- [x] **Conhecimento estruturado — atributos e criação**: 6 atributos em
      `dados/atributos.json` (com `pericias_governadas`, cross-check exato vs perícias)
      + 2 chunks procedurais (9 passos de criação; método Pontos/Rolagens + tabela),
      **integrados ao índice**. Corrige a falha "por pontos" do §10. Ver §11.
- [x] **Conhecimento estruturado — equipamentos (Capítulo 3 completo)**: 47 armas/munições,
      12 armaduras/escudos, 121 itens gerais, 29 melhorias superiores, 6 materiais especiais,
      4 regras procedurais e 20 listas agregadas em `dados/equipamentos.json`,
      **integrados ao índice** (substitui os 64 chunks grossos por 239 chunks finos específicos;
      rank 1 nas consultas de itens e filtros híbridos de categoria). Ver §11.
- [x] **Conhecimento estruturado — magia (Capítulo 4 completo)**: 198 magias + 5 regras
      procedurais em `dados/magias.json`, **integradas ao índice** (1 chunk/magia + listas por
      escola/círculo/tipo; substitui 135 chunks de texto corrido por 219 finos) e com **filtro
      híbrido** por círculo/escola/tipo, inclusive combinados (`detectar_filtro_magia`). Doc
      completa em [`docs/familias/magia.md`](docs/familias/magia.md).
- [x] **Conhecimento estruturado — condições (Apêndice)**: 35 condições + 1 regra geral em
      `dados/condicoes.json` (nome, tipo de efeito, escalonamento, efeito), **integradas ao índice**
      (1 chunk/condição + lista por tipo; −4 texto corrido, +37 finos) e com **filtro híbrido** por
      tipo de efeito/escalonamento (`detectar_filtro_condicao`). Resolve "condição fatigado" (§10).
      Doc em [`docs/familias/condicoes.md`](docs/familias/condicoes.md).
- [x] **Conhecimento estruturado — ameaças / bestiário (Capítulo 7)**: 80 criaturas em
      `dados/ameacas.json` (stat block completo: ND, defesa/PV/PM, ataques, habilidades, atributos,
      perícias, tesouro), **integradas ao índice** (96 chunks: 80 criaturas + 9 listas por grupo +
      4 listas por faixa de ND + 3 regras; substitui os 96 chunks de texto corrido do Cap. 7) e com
      **filtro híbrido** por ND, faixa de ND e grupo ecológico (`detectar_filtro_ameaca`). Doc em
      [`docs/familias/ameacas.md`](docs/familias/ameacas.md).
- [x] **Conhecimento estruturado — regras de jogo / combate & parceiros (Capítulos 5 e 6)**: manobras,
      ações, táticas, ferimentos/descanso e o sistema de parceiros em `dados/regras_jogo.json`
      (7 manobras + 10 parceiros × 3 tiers + regras de combate/descanso), **integradas ao índice**
      (48 chunks estruturados; substitui os 93 chunks de texto corrido do Cap. 5) e com **filtro
      híbrido** por manobra/ação/tática/ferimento/parceiro (`detectar_filtro_regra_jogo`). Doc em
      [`docs/familias/jogando.md`](docs/familias/jogando.md).
- [x] **Conhecimento estruturado — mundo de Arton / geografia (Capítulo 9)**: 30 reinos e regiões
      (Reinado, grandes potências, lugares lendários, ermos, ilhas) + linha do tempo em
      `dados/mundo_arton.json` (capital, regente, divindades, cultura, ganchos), **integradas ao índice**
      (34 chunks: 30 regiões + 3 listas + 1 linha do tempo; substitui os 113 chunks de texto corrido do
      Cap. 9) e com **filtro híbrido** por reino/região/lugar/potência (`detectar_filtro_mundo_arton`). Doc
      em [`docs/familias/mundo_arton.md`](docs/familias/mundo_arton.md).
- [x] **Conhecimento estruturado — recompensas / itens mágicos (Capítulo 8)**: 104 registros em
      `dados/recompensas.json` (29 encantos de arma, 24 de armadura, armas/armaduras específicas, 18
      acessórios, 7 artefatos supremos, poções/pergaminhos, tabelas de tesouro por ND), **integrados ao
      índice** (104 chunks; substitui os 54 de texto corrido do Cap. 8) e com **filtro híbrido** por
      encanto/item/acessório/artefato/regra (`detectar_filtro_recompensa`). Doc em
      [`docs/familias/recompensas.md`](docs/familias/recompensas.md).
- [x] **Conhecimento estruturado — fichas das 14 classes + O Mestre (Capítulos 1 e 6)**: fichas completas
      das 14 classes (PV/PM, proficiências, perícias, habilidades automáticas condensadas e **tabela de
      progressão nível-a-nível**) + regras do Mestre (ambientes/queda/afogamento/fogo, perigos complexos,
      doenças e venenos, perseguições) em `dados/mestre_classes.json`, **integrados ao índice** (22 chunks:
      14 fichas + 8 de regras; substitui 243 chunks de texto corrido dos Caps. 1 e 6) e com **filtro
      híbrido** (`detectar_filtro_classe_progressao` / `detectar_filtro_mestre`). Doc em
      [`docs/familias/mestre_classes.md`](docs/familias/mestre_classes.md). **Nota:** as fichas consolidam
      o antigo par visão-geral/habilidades; a granularidade por-habilidade virou resumo na ficha, mas os
      poderes de classe (296) e os chunks de **evidência de atributo** (14, restaurados) permanecem.
- [x] **Procedência multi-livro (fundação)**: todo chunk carrega `fonte` (id do livro em `fontes.py`); a
      citação nomeia o **livro + página** ("segundo *Ameaças de Arton*, pág. X") e o log grava `fonte`/`livro`.
      Índice atual 100% `nucleo` (livro básico), marcado por `migrar_fonte.py`. Base para adicionar os livros
      de expansão sem colisão de regras entre edições. Ver §11.

**Fluxo de uso hoje:** clicar no atalho **"RAG Tormenta20"** → navegador abre em
`http://127.0.0.1:8000` → perguntar → marcar **OK/Problema**. Tudo fica em `logs\`.

---

## 2. Arquitetura (como está construído)

```
INGESTÃO (uma vez, offline)  — ingestao.py
  PDF → extrair texto por página (PyMuPDF) → limpar (de-hifenizar, reflow)
      → chunking ancorado no ÍNDICE (TOC) do livro
      → embeddings (bge-m3, dim 1024, normalizados) → índice FAISS

CONSULTA (cada pergunta)     — perguntar.py / interface.py
  pergunta → embedding (bge-m3) → busca top-k no FAISS (cosseno)
           → monta prompt (contexto recuperado + pergunta)
           → Qwen3-8B via Ollama → resposta citando [Fonte N] (seção/página)
```

Dois modelos, papéis diferentes:
- **Embedder** (`BAAI/bge-m3`, multilíngue): faz a **busca** — vira texto em
  vetores e acha os trechos por similaridade de cosseno. Roda em Python.
- **Qwen3-8B** (via Ollama): **redige** a resposta lendo o contexto recuperado.

Lembrete conceitual: **RAG = conhecimento (o "o quê")**, entregue no prompt;
fine-tuning/LoRA = comportamento (o "como"). Aqui é **só RAG**.

---

## 3. Como rodar

### Interface web (recomendado)
Dê dois cliques no atalho **"RAG Tormenta20"** na Área de Trabalho, ou rode:
```
C:\LLM-Local\tormenta\iniciar_interface.bat
```
O `.bat` verifica/inicia o Ollama, sobe a interface e abre o navegador em
`http://127.0.0.1:8000`. **A janela preta que fica aberta é o servidor — fechá-la
encerra a interface.** A primeira resposta pode demorar ~1 min (o Qwen carrega
~6 GB na RAM da CPU); as seguintes são mais rápidas.

### Linha de comando (alternativa)
```
python perguntar.py "Como funciona a condição fatigado?"
python perguntar.py                 # modo interativo (perguntas em loop)
python perguntar.py -k 8 "..."      # muda quantos trechos recupera (padrão 5)
```

### Suíte de regressão
```
python testar_lote.py               # roda um conjunto fixo de perguntas
```

### Refazer o índice (só quando mudar a ingestão)
```
python ingestao.py                  # ~22-30 min na CPU; sobrescreve index\
```
Pré-requisito de consulta: **Ollama no ar** com o modelo `qwen3:8b`.

---

## 4. Estrutura de pastas e arquivos

```
C:\LLM-Local\tormenta\
├─ livro\                     PDF do livro (fonte)
│   └─ Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf   (407 págs, ~111 MB)
├─ index\                     índice gerado pela ingestão
│   ├─ tormenta.faiss         índice vetorial FAISS (IndexFlatIP / cosseno)
│   ├─ chunks.jsonl           1 chunk por linha: id, titulo, secao, pagina, texto
│   └─ meta.json              modelo, dim, contagens, params
├─ logs\                      gerado em runtime (ver §9)
│   ├─ consultas.jsonl        toda pergunta + fontes + resposta + tempos
│   ├─ avaliacoes.jsonl       vereditos OK/Problema com nota
│   └─ servidor.log           erros/eventos do servidor web
├─ dados\                     conhecimento ESTRUTURADO (ver §11)
│   ├─ racas.json             17 raças tipadas (gerado por extrair_racas.py)
│   ├─ racas_tormenta.html    ferramenta de conferência das raças (abre offline)
│   ├─ classes.json           14 classes tipadas (gerado por extrair_classes.py)
│   ├─ classes_tormenta.html  ferramenta de conferência das classes (abre offline)
│   ├─ pericias.json          29 perícias tipadas (gerado por extrair_pericias.py)
│   ├─ pericias.html          ferramenta de conferência das perícias (gerada por gerar_pericias_html.py)
│   ├─ origens.json           35 origens tipadas (gerado por extrair_origens.py)
│   ├─ origens.html           ferramenta de conferência das origens (gerada por gerar_origens_html.py)
│   ├─ deuses.json            20 deuses tipados (gerado por extrair_deuses.py)
│   ├─ deuses.html            ferramenta de conferência dos deuses (gerada por gerar_deuses_html.py)
│   ├─ atributos.json         6 atributos tipados + perícias governadas (gerado por extrair_atributos.py)
│   ├─ criacao_personagem.json 9 passos + método/tabela de atributos (gerado por extrair_atributos.py)
│   ├─ atributos.html         referência de Construção de Personagem (gerada por gerar_atributos_html.py)
│   ├─ poderes_classe.json    296 poderes de classe (gerado por extrair_poderes_classe.py)
│   ├─ poderes_classe.html    ferramenta de conferência dos poderes de classe
│   ├─ poderes_gerais.json    162 poderes gerais (gerado por extrair_poderes_gerais.py)
│   ├─ poderes_gerais.html    ferramenta de conferência dos poderes gerais (gerada por gerar_poderes_gerais_html.py)
│   ├─ equipamentos.json      219 itens, armas, armaduras, melhorias, materiais e regras (gerado por extrair_equipamentos.py)
│   └─ equipamentos.html      ferramenta de conferência dos equipamentos (gerada por gerar_equipamentos_html.py)
├─ ingestao.py               extração → limpeza → chunking (TOC) → embeddings → FAISS
├─ extrair_racas.py          extração ESTRUTURADA de raças (tipografia) → dados/racas.json
├─ extrair_classes.py        extração ESTRUTURADA de classes (tipografia) → dados/classes.json
├─ extrair_pericias.py       extração ESTRUTURADA de perícias (tipografia) → dados/pericias.json
├─ gerar_pericias_html.py    gera a ferramenta de conferência das perícias (reusa o CSS)
├─ extrair_origens.py        extração ESTRUTURADA de origens (tipografia) → dados/origens.json
├─ gerar_origens_html.py     gera a ferramenta de conferência das origens (reusa o CSS)
├─ extrair_deuses.py         extração ESTRUTURADA de deuses (tipografia) → dados/deuses.json
├─ gerar_deuses_html.py      gera a ferramenta de conferência dos deuses (reusa o CSS)
├─ extrair_atributos.py      extrai 6 atributos + 9 passos + método/tabela → atributos.json + criacao_personagem.json
├─ gerar_atributos_html.py   gera a referência de Construção de Personagem (reusa o CSS)
├─ integrar_atributos.py     integra 6 atributos + 2 chunks procedurais; corrige a falha "por pontos" do §10
├─ extrair_poderes_classe.py explode "Poder de X" (classes.json) em nós de poder → dados/poderes_classe.json
├─ extrair_opcoes_poder.py   recupera os quadros de opção (Black) e anexa `opcoes` ao poder dono (§11)
├─ extrair_poderes_gerais.py extração ESTRUTURADA (tipografia) dos poderes do cap. Perícias & Poderes → dados/poderes_gerais.json
├─ gerar_poderes_gerais_html.py gera a ferramenta de conferência dos poderes gerais (reusa o CSS da poderes_classe.html)
├─ extrair_equipamentos.py   extração ESTRUTURADA de armas, armaduras, itens gerais, melhorias, materiais e regras → dados/equipamentos.json
├─ gerar_equipamentos_html.py gera a ferramenta de conferência dos equipamentos (dados/equipamentos.html)
├─ integrar_equipamentos.py  substitui os 64 chunks grossos do Cap. 3 por 239 chunks específicos e listas agregadas (§11)
├─ integrar_racas.py         substitui chunks de raça no índice pelos estruturados (§11)
├─ integrar_pericias.py      substitui os 79 chunks de texto corrido de perícia por 29 estruturados (§11)
├─ integrar_origens.py       substitui os 88 chunks de texto corrido de origem por 35 estruturados (§11)
├─ integrar_deuses.py        substitui os 47 chunks de texto corrido de deus por 20 estruturados (§11)
├─ integrar_classes.py       substitui chunks de classe no índice pelos estruturados (§11)
├─ extrair_atributos_classe.py extrai a coluna Atributo da Tabela 1-3 (pág 32) → campo atributo_principal em classes.json (§11)
├─ integrar_atributo_classe.py verbaliza atributo_principal no chunk de visão geral da classe; re-embute só os 14 (§11)
├─ integrar_evidencia_atributo.py cria 1 chunk/classe "o que cada atributo destrava" (pré-requisitos dos poderes de classe, Stage B) (§11)
├─ derivar_atributo_chave.py deriva o atributo de conjuração por classe (habilidades + evidência) → metadado atributo_chave em classes.json (§11)
├─ integrar_poderes_classe.py explode os chunks grossos "Poder de X" em 1 chunk fino por poder + 1 lista/classe (§11)
├─ integrar_poderes_gerais.py substitui os chunks de texto corrido de Poderes Gerais por 1 chunk/poder + listas por categoria e por deus (§11)
├─ estruturar_prereqs.py      Stage B: pre_requisito (texto) → pre_requisito_estruturado (predicados) nos JSON de poder (§11)
├─ elegibilidade.py           Stage C: deriva campo `elegibilidade` (acesso/conjuração/devoção + flags) nos JSON de poder (§11)
├─ personagem.py             Stage D: motor que avalia B+C p/ um personagem — poderes disponíveis + árvore de pré-requisitos (§11)
├─ perguntar.py              núcleo da consulta (busca vetorial + filtro híbrido + motor de poderes B/C/D + geração) + CLI + logs
├─ geradores.py              backend de GERAÇÃO plugável (env TORMENTA_GERADOR: ollama-local | ollama-remoto | api-claude)
├─ fontes.py                 registro canônico das FONTES/livros (id → título/versão) — procedência multi-livro
├─ migrar_fonte.py           backfill: carimba `fonte` nos chunks sem procedência (metadado puro, sem re-embed)
├─ extrair_ameacas_arton.py  [EM CURSO] bestiário de *Ameaças de Arton* (fonte=ameacas-arton) — geométrico (docs/familias/ameacas_arton.md)
├─ gerar_ameacas_arton_html.py  [EM CURSO] ferramenta de conferência do bestiário de Ameaças de Arton
├─ extrair_magias.py         extração ESTRUTURADA das 198 magias + 5 regras (Cap. 4) → dados/magias.json (docs/familias/magia.md)
├─ gerar_magias_html.py      gera a ferramenta de conferência das magias (dados/magias.html)
├─ integrar_magias.py        substitui os 135 chunks de texto corrido do Cap. 4 por 219 finos (1/magia + listas)
├─ extrair_condicoes.py      extração ESTRUTURADA das 35 condições + regra (Apêndice) → dados/condicoes.json (docs/familias/condicoes.md)
├─ gerar_condicoes_html.py   gera a ferramenta de conferência das condições (dados/condicoes.html)
├─ integrar_condicoes.py     substitui os 4 chunks de texto corrido do Apêndice por 37 finos (1/condição + lista + regra)
├─ interface.py              servidor web local (stdlib) com streaming e avaliação
├─ testar_lote.py            suíte: roda várias perguntas, carrega modelo 1x
├─ iniciar_interface.bat     trata Ollama + sobe a interface
├─ mcp_tormenta/             servidor MCP (stdio) que expõe a recuperação a clientes (Claude Code/Codex/Antigravity) — docs/mcp.md
├─ docs/                     documentação modular (familias/, mcp.md) — ver ponteiro no topo
├─ .gitignore                versiona só a ferramenta; exclui livro/index/dados/logs/models (dados protegidos)
└─ README.md                 este documento (fonte-de-verdade / índice)
```

Atalho: `C:\Users\rnaba\OneDrive\Desktop\RAG Tormenta20.lnk` → o `.bat`.

---

## 5. Parâmetros e decisões técnicas

| Item | Valor | Onde |
|---|---|---|
| Backend de geração | **plugável** via env `TORMENTA_GERADOR` (padrão `ollama-local`) | `geradores.py` |
| Modelo de geração (padrão) | **qwen3:8b** (Q4_K_M, ~5,2 GB) via Ollama local | `geradores.py` |
| API do Ollama | `http://127.0.0.1:11434/api/chat` | `geradores.py` |
| Modo *thinking* do Qwen | **desligado** (`"think": false`) — mais rápido | `geradores.py` |
| Temperatura | 0.2 (factual) | `perguntar.py` → `geradores.py` |
| Embedder | **BAAI/bge-m3** (dim **1024**, normalizado) | `ingestao.py` |
| Índice | FAISS `IndexFlatIP` (produto interno = cosseno) | `ingestao.py` |
| Chunking | por seção do TOC; seções grandes divididas | `ingestao.py` |
| `MAX_CHARS` / `OVERLAP` | 2000 / 200 caracteres | `ingestao.py` |
| `MIN_CHARS` | 60 (descarta fragmentos) | `ingestao.py` |
| `TOP_K` padrão | 5 | `perguntar.py` |
| Porta da interface | 8000 | `interface.py` |

O **PDF é texto vetorial real** (sem necessidade de OCR) e traz um **índice
(TOC) com 290 entradas**, usado como esqueleto do chunking → resulta em 288
seções úteis e 1165 chunks.

---

## 6. Ambiente e dependências (o que está instalado)

**Python base único do lab** (sem venv):
`C:\Users\rnaba\AppData\Local\Programs\Python\Python312\python.exe`
Pesos/cache dos modelos em `C:\LLM-Local\models` (variável `HF_HOME`).

| Item | Versão | Tamanho | Como (re)instalar |
|---|---|---|---|
| Ollama (programa) | 0.32.15 | ~700 MB | `winget install Ollama.Ollama` |
| qwen3:8b (modelo) | Q4_K_M | ~5,2 GB | `ollama pull qwen3:8b` |
| PyMuPDF (`pymupdf`) | 1.28.2 | ~20 MB | `pip install pymupdf` |
| sentence-transformers | 5.7.0 | — | (já no lab) |
| faiss | — | — | (já no lab) |
| torch (CPU) | 2.13.0+cpu | — | (já no lab) |
| requests | 2.34.2 | — | (já no lab) |
| BAAI/bge-m3 (embedder) | — | ~2,2 GB | baixa sozinho no 1º uso (→ `HF_HOME`) |

Binário do Ollama: `C:\Users\rnaba\AppData\Local\Programs\Ollama\ollama.exe`
(pode **não** estar no PATH de alguns shells — no `.bat` é chamado pelo caminho
completo).

> **Regra do projeto: nunca instalar nada sem aprovação explícita do usuário.**

---

## 7. Armadilhas já resolvidas (leia antes de mexer)

1. **TOC quebrado (o livro foi montado de vários PDFs).** Havia entradas-raiz com
   título terminando em `.pdf` e um marcador **"Capítulo 8: Recompensas"
   apontando para a pág. 1** (destino interno do PDF original; a página real é
   330). Sem tratar, o chunking "engolia" páginas[0:331] e gerava ~644 chunks
   duplicados/mal-rotulados. **Solução em `montar_secoes()`**: remove raízes
   `.pdf`; força páginas não-decrescentes; relocaliza marcador furado por
   `page.search_for` **limitado à janela entre vizinhos** (busca sem limite
   envenena o cálculo — acha a palavra numa seção distante). Resultado: 1989 →
   **1165 chunks**, citações corretas.

2. **"Failed to fetch" na interface.** A resposta antes chegava só no fim; na CPU
   a geração leva ~1 min e a conexão ociosa era derrubada (e o servidor caía).
   **Solução**: `/consultar` responde em **streaming NDJSON** (evento `fontes` →
   `token`s → `fim`); os bytes fluindo mantêm a conexão viva e dão feedback.
   Há tratamento de `BrokenPipe/ConnectionReset` e log em `logs/servidor.log`.

3. **Acentos "quebrados" no terminal.** São só o console do Windows (cp850). O
   texto real extraído/salvo está em **UTF-8 correto**. Não é bug.

4. **Performance na CPU.** Embeddings da ingestão: ~22-30 min para ~1165 chunks.
   Geração: ~40-85 s por resposta (mais lento na 1ª, "a frio"). O **Ollama
   serializa** requisições (uma por vez). `context_length` padrão do Ollama =
   **4096 tokens** — prompts com muitos trechos grandes podem chegar perto disso.

---

## 8. Fundamento conceitual (para quem está estudando)

- **RAG** entrega *conhecimento* no prompt: o modelo de geração (Qwen3-8B) não
  conhece Tormenta20 (perguntado "cru", ele achou que era uma "tempestade nº 20");
  com os trechos do livro no contexto, ele responde certo e cita a fonte.
- **Embedder ≠ gerador.** O bge-m3 só mede similaridade (busca); quem escreve é o
  Qwen. A qualidade do RAG depende **primeiro** da extração/limpeza do PDF e do
  **chunking**, depois do embedder, e por fim do gerador.

---

## 9. Bancada de testes e logs (como evoluir com dados)

A interface e a CLI **registram tudo** para permitir catalogar problemas **sem
reprocessar o índice** a cada dúvida.

- `logs/consultas.jsonl` — uma linha JSON por pergunta:
  `ts, pergunta, k, modelo_embed, modelo_llm, gerador, n_chunks_indice, filtro_metadado,
   filtro_pericia, filtro_origem, filtro_deus, filtro_atributo, filtro_equipamento, filtro_poder, resposta,
   fontes[ {rank, id, fonte, livro, secao, pagina, score, previa, match_filtro?} ], seg_busca, seg_geracao`.
   (`fonte` = id do livro; `livro` = rótulo resolvido via `fontes.py`.)
   (`gerador` = backend de geração ativo, ver §5 e `geradores.py`.)
- `logs/avaliacoes.jsonl` — quando você clica **OK/Problema** na interface:
  `ts, pergunta, veredito, nota, fontes, resposta`.
- `logs/servidor.log` — eventos e erros do servidor web.

**Método de trabalho:** teste perguntas, marque as ruins como **Problema** com
uma nota do que faltou. Quando houver um **padrão** (vários casos parecidos),
aí sim vale reprocessar. Um caso isolado **não** justifica re-embutir 1165 chunks.

---

## 10. Problemas conhecidos / limitações (candidatos a melhoria)

- **Diluição de chunk esconde informação (RESOLVIDO para o caso âncora).** Ex.:
  "criação de personagem **por pontos**" existia na pág. 23 mas ficava no **rank
  20** (janela de 2000 chars misturava o método com listas de perícias). A
  extração estruturada do Cap. 1 (`extrair_atributos.py` + `integrar_atributos.py`,
  §11) criou um chunk dedicado "Definindo seus atributos" — agora a pergunta traz
  o método no **rank 1–2**. O padrão geral (diluição) segue como candidato onde
  não houver extração estruturada.
- **Respostas às vezes incompletas.** Ex.: "perícias usadas para combate" trouxe
  "Atletismo e Luta", mas faltou **Pontaria** (ataques à distância).

Essas limitações são de **recuperação**, não do gerador. **Decisão atual
(2026-08-20): não corrigir caso a caso**; acumular evidência nos logs primeiro.

### Ideias de melhoria (quando os logs justificarem)
1. **Chunking por subtítulo** — detectar cabeçalhos em negrito via fontes do
   PyMuPDF (`get_text("dict")`) e cortar ali, isolando trechos como "Definindo
   seus atributos". Melhor qualidade; re-embute.
2. **Busca híbrida BM25 + vetor** — somar busca por palavra-chave à vetorial,
   para termos exatos ("pontos", "Pontaria") emergirem. **Não re-embute**; muda
   só `perguntar.py`/`interface.py`.
3. **Chunks menores** (`MAX_CHARS` ~900) — menos diluição no geral; re-embute.
4. **Aumentar `TOP_K`** — ajuda casos de borda, mas cuidado com o limite de
   contexto do Ollama (4096); ver §7.

---

## 11. Conhecimento estruturado (entidades tipadas)

Além do RAG por texto corrido (§2), a **via estruturada** extrai as **entidades do
jogo como registros tipados** (não pedaços soltos de texto), guiando-se pela
**tipografia** do PDF em vez do TOC. Isso ataca a causa-raiz diagnosticada no §10
(os "stat blocks" sumiam na extração de texto puro) e permite **filtrar por campo**
(ex.: raças com bônus de Carisma) — base para o caso de uso "auxiliar do jogador".

**Estado das famílias (todas extraídas E integradas ao índice).** O padrão de cada
uma: `extrair_*.py` (PDF→JSON, por tipografia) → ferramenta de conferência HTML →
`integrar_*.py` (substitui os chunks de texto corrido pelos estruturados, sem
reembutir o resto; idempotente). Subseções abaixo detalham cada uma.

**Procedência (multi-livro).** Cada chunk carrega `fonte` — o id de um livro
registrado em [`fontes.py`](fontes.py) (`nucleo`, `ameacas-arton`, `herois-arton`,
`atlas-arton`, `deuses-arton`). O chunk guarda só o id; o rótulo de exibição
("Ameaças de Arton, pág. X") é resolvido na citação. **Contrato ao adicionar um
livro:** todo `extrair_/integrar_` novo carimba a sua `fonte` + `pagina`; expansões
que repetem/variam/estendem uma entidade do núcleo devem ser registros próprios com
`fonte` distinta (e, quando fizer sentido, um campo de vínculo à entidade-base) — nunca
sobrescrever silenciosamente o chunk do núcleo. Índice atual (2533 chunks): `nucleo` 1498 +
`ameacas-arton` 377 + `herois-arton` 658.

**Expansão multi-livro — EM CURSO.**

*Ameaças de Arton* (`fonte="ameacas-arton"`) — **BESTIÁRIO FEITO.** 344 criaturas completas
(+55 pendentes isoladas) por auto-descoberta **geométrica** (layout adversarial). Conserto de
raiz do parser (descartar título-splash decorativo) recuperou ~20 criaturas antes fundidas e
limpou os nomes na origem. 377 chunks. Doc: [`docs/familias/ameacas_arton.md`](docs/familias/ameacas_arton.md).

*Heróis de Arton* (`fonte="herois-arton"`) — **Cap. 1 FEITO** (5 famílias-entidade; só faltam as
Tabelas de referência). 5 Novas Raças, 443 Novos Poderes (classe + gerais), classe Treinador (+pet),
14 Classes Variantes, 30 Novas Origens. 658 chunks. Layout IowanOldStyle (não SourceSansPro).
Doc: [`docs/familias/herois_campeoes.md`](docs/familias/herois_campeoes.md).

| Família | Nº | Filtro híbrido em `perguntar.py` |
|---|---|---|
| Raças | 17 | modificador de atributo (`detectar_filtro`) |
| Classes | 14 | — |
| Perícias | 29 | atributo-chave / flags (`detectar_filtro_pericia`) |
| Origens | 35 | perícia/poder concedido (`detectar_filtro_origem`) |
| Poderes de classe | 296 | — |
| Poderes gerais (combate/destino/magia/concedidos/tormenta) | 162 | — |
| Deuses | 20 | energia / devoto (`detectar_filtro_deus`) |
| Atributos + criação | 6 (+2 procedurais) | direto/inverso (`detectar_filtro_atributo`) |
| Equipamentos (Capítulo 3) | 219 (+20 listas) | armas, armaduras, esotéricos, venenos, materiais (`detectar_filtro_equipamento`) |
| Magia (Capítulo 4) | 198 (+5 regras) | círculo / escola / tipo, combinados (`detectar_filtro_magia`) — doc em `docs/familias/magia.md` |
| Condições (Apêndice) | 35 (+1 regra) | tipo de efeito / escalonamento (`detectar_filtro_condicao`) — doc em `docs/familias/condicoes.md` |
| Ameaças / Bestiário (Capítulo 7) | 80 (+13 listas, +3 regras) | ND / faixa de ND / grupo (`detectar_filtro_ameaca`) — doc em `docs/familias/ameacas.md` |
| Regras de Jogo / Combate & Parceiros (Cap. 5 e 6) | 48 (7 manobras, 10 parceiros, +regras) | manobra / ação / tática / ferimento / parceiro (`detectar_filtro_regra_jogo`) — doc em `docs/familias/jogando.md` |
| Mundo de Arton / Geografia (Capítulo 9) | 30 (+3 listas, +1 linha do tempo) | reino / região / lugar / potência (`detectar_filtro_mundo_arton`) — doc em `docs/familias/mundo_arton.md` |
| Recompensas / Itens Mágicos (Capítulo 8) | 104 (encantos, específicos, acessórios, 7 artefatos) | encanto / item / acessório / artefato / regra (`detectar_filtro_recompensa`) — doc em `docs/familias/recompensas.md` |
| Fichas das 14 Classes + O Mestre (Caps. 1 e 6) | 22 (14 fichas + 8 regras) | ficha/progressão de classe e regras do Mestre (`detectar_filtro_classe_progressao` / `detectar_filtro_mestre`) — doc em `docs/familias/mestre_classes.md` |

Índice atual: **~1498 chunks** (1165 brutos + estruturados − textos corridos
substituídos). ⚠️ Cuidado com a **ordem de re-run** dos integradores (ver a nota nos
Poderes de classe).

### Raças (integradas — a primeira família, serviu de piloto do método)

`extrair_racas.py` → `dados/racas.json` (**17 raças** do núcleo). Rode com:
```
python extrair_racas.py
```

Cada raça é um registro:
```
id, tipo="raca", nome, fonte (nucleo|ameaças|heróis…), versao, pagina,
modificadores {Atributo: ±N}         # + "_flexivel" p/ "+1 em N atributos"
modificadores_variantes {…}          # sub-raças (ex.: Suraggel → Aggelus/Sulfure)
resumo,
habilidades [ {nome, efeito} ]
```

**Como funciona (tipografia = schema):** nome da raça = fonte `Tormenta20`
(tam 27 no layout normal, 21 no compacto "Raças Extras"); o lore não tem
negrito, então o **1º span em negrito inicia a mecânica**; a 1ª frase em negrito
são os **modificadores**; cada habilidade é um **nome em negrito** seguido do
**efeito em roman**. Nas páginas compactas (págs. 33–37) dois frames de raças
diferentes se sobrepõem em x — por isso a ordenação é **por bloco/frame**, não
por span solto (senão as linhas intercalam). Ver `extrair_racas.py`.

**Conferência:** abra `dados/racas_tormenta.html` (offline, dois cliques) para
filtrar por raça/atributo e cruzar com a página do livro. Publicado também como
artifact privado.

**Resíduos de prosa (CORRIGIDOS).** Dois artefatos do PDF vazavam apesar dos filtros
tipográficos: o resumo do Lefou começava com "Sir" (nome roman numa legenda de arte
"— Sir Porti…", cujo resto é itálico) e a habilidade "Natureza Venenosa" da Medusa
terminava com o marcador de jogo "Veneno." (itálico). `corrigir_artefatos()` em
`extrair_racas.py` os remove com regras **pontuais e restritas por nome de raça** —
não dá para generalizar por itálico, pois nomes de magia nas habilidades também são
itálicos. Re-extraído e re-integrado; só Lefou e Medusa mudaram.

**Integração ao índice (FEITA).** `integrar_racas.py` substitui, no índice de
consulta, os chunks antigos de raça (texto corrido) pelos estruturados:
```
python integrar_racas.py
```
O que ele faz: backup de `index\` (pasta `backup-<timestamp>\`); remove os chunks
"...> Raças > Nome" (mantém a introdução "...> Raças"); serializa cada raça em um
`texto` (nome + modificadores verbalizados + resumo + habilidades) que serve ao
embedding **e** ao contexto do LLM; **reconstrói o índice sem reembutir os outros
chunks** (o FAISS guarda os vetores — só as 17 raças são embutidas, ~17s); grava
os campos estruturados (`tipo="raca"`, `modificadores`, …) como metadados no
chunk. Resultado: índice **1165 → 1144 chunks** (−38 antigos, +17 raças).
Idempotente (rodar de novo não duplica).

Efeito medido: perguntas diretas de raça ("atributos do Anão", "o que é um
osteon", "me explique a Sílfide") agora trazem o chunk estruturado no **rank 1**.

**Filtro híbrido / por metadado (FEITO).** Em `perguntar.py`, a busca agora é
híbrida: `detectar_filtro()` identifica perguntas que são um **filtro por
modificador de raça** e retorna os chunks cujos metadados satisfazem o predicado.
A regra é **conservadora** — só dispara com (a) a palavra "raça(s)", (b) um
atributo (nome completo) e (c) um sinal de bônus/penalidade — para NÃO disparar em
"como funciona Carisma". Quando dispara, devolve **só as raças que casam**
(ordenadas por similaridade, teto 10; considera sub-raças/variantes). Todo o resto
segue na busca vetorial pura.

Efeito medido: "raças com bônus de Carisma" agora traz as 6 raças com Carisma > 0
(antes vencia a classe Bucaneiro); "penalidade em Força" traz Kliren, Hynne,
Sílfide. O log (`logs/consultas.jsonl`) grava `filtro_metadado` e marca as fontes
que casaram (`match_filtro`).

### Perícias (integradas)

`extrair_pericias.py` → `dados/pericias.json` (**29 perícias**, Acrobacia a Vontade,
págs 121–129). Mesmo método (tipografia): nome = `Tormenta20` ~21; **stat block** =
`Tormenta20` ~16 com tokens separados por "•" (atributo-chave For/Des/Con/Int/Sab/Car
+ flags "Treinada" e "Armadura"); descrição = `IowanOldStyle-Roman`, onde o 1º trecho
roman é o **resumo** e cada **uso** é um nome em negrito (com "(CD X, Apenas Treinado)"
parseado para `cd`/`apenas_treinado`) seguido do efeito. Cada registro:
```
id, tipo="pericia", nome, atributo, so_treinada (bool), penalidade_armadura (bool),
resumo, usos [ {nome, cd?, apenas_treinado?, efeito} ], fonte, versao, pagina
```
Uma perícia só é emitida se tiver atributo (guarda contra sz21 que não seja perícia);
cross-refs/legendas em negrito ("Capítulo 5", "Tabela 2-1") são filtradas dos usos.
Total: 29 perícias, 70 usos. Distribuição por atributo (Des 8, Car/Int/Sab 6, For 2,
Con 1), 11 só-treinadas, 3 com penalidade de armadura — bate com as regras.

Conferência: `dados/pericias.html` (gerada por `gerar_pericias_html.py`) — filtra por
atributo e pelas flags, lista os usos. Rode `python extrair_pericias.py`.

**Integração ao índice (FEITA).** `integrar_pericias.py` substitui os **79 chunks de
texto corrido** de perícia (ingestão via TOC, 2–3 por perícia) por **29 chunks
estruturados** (1 por perícia: resumo + usos verbalizados; metadados atributo/flags/
usos). Mantém a introdução ("Escolhendo/Usando Perícias"). Reconstrói sem reembutir o
resto (~30s). Índice: **1600 → 1550 chunks** (−79, +29). Idempotente.
```
python integrar_pericias.py
```
**Filtro híbrido / por metadado (FEITO).** Em `perguntar.py`, `detectar_filtro_pericia()`
identifica listagens por campo de perícia. Conservador: exige o **plural "perícias"**
(intenção de listar) + um predicado — "só/somente/apenas treinada", "penalidade de
armadura", ou um **atributo-chave** ("perícias de Destreza"). NÃO dispara em "o que faz
Acrobacia". Quando dispara, devolve só as perícias que casam (por similaridade, teto 12)
e marca `match_filtro`; o log grava `filtro_pericia`. Efeito medido: "perícias de
Destreza" → as 8 de Destreza; "perícias só treinadas" → as 11; "perícias com penalidade
de armadura" → Ladinagem, Acrobacia, Furtividade.

Nota: "perícias usadas para combate" (falha do §10) é **derivada**, não um campo do
livro — candidata a um tag `usada_em_combate` com evidência (camada de derivação).

### Origens (integradas)

`extrair_origens.py` → `dados/origens.json` (**35 origens**, Acólito a Trabalhador,
págs 91–101; "Sua Própria Origem" é regra, não origem → pulada). Tipografia: nome =
`Tormenta20` ~21 (pode ocupar 2 linhas → junta); rótulos em negrito "Itens." e
"Benefícios." (o rótulo pode vir partido em 2 spans negrito — pula-se todo span
negrito); poder único = `Tormenta20` ~16 + efeito; legendas de arte (~8) filtradas.
Cada registro:
```
id, tipo="origem", nome, pagina, resumo, itens,
beneficios (texto), pericias [lista], poderes [lista],
poder_unico { nome, efeito }, fonte, versao
```
Os Benefícios ("A, B (perícias); C, D (poderes).") são parseados em listas. As
**perícias são canonizadas** contra as 29 reais (fecha "Ofício (alquimista)" → "Ofício"
e a de-hifenização "Enga-nação" → "Enganação") — resultado: 29 perícias distintas, todas
reais. Caso especial: **Amnésico** não tem lista fixa ("recebe uma perícia e um poder a
sua escolha") — listas vazias, regra preservada em `beneficios`.

Conferência: `dados/origens.html` (gerada por `gerar_origens_html.py`) — filtra por
perícia concedida. Rode `python extrair_origens.py`.

**Integração ao índice (FEITA).** `integrar_origens.py` substitui os **88 chunks de
texto corrido** de origem (mantendo a intro) por **35 chunks estruturados** (1 por
origem: resumo + itens + benefícios + poder único; `pericias`/`poderes`/`poder_unico`
como metadados). Índice: **1550 → 1497 chunks** (−88, +35). Idempotente.
```
python integrar_origens.py
```
**Filtro híbrido / por metadado (FEITO).** Em `perguntar.py`, `detectar_filtro_origem()`
identifica "quais origens dão a perícia/poder X". Exige a palavra "origem/origens" + o
nome de uma perícia (conjunto fechado de 29) ou de um poder concedido. **Desambiguação:**
nomes de poder contêm nomes de perícia ("Vontade de Ferro" ⊃ "Vontade") — escolhe pelo
campo citado na pergunta ("perícia"/"poder") e pelo nome mais longo. Efeito medido:
"perícia Cura" → Curandeiro, Acólito; "poder Vontade de Ferro" → Acólito, Refugiado;
"poder Membro da Igreja" → Acólito. O log grava `filtro_origem`. Conecta
origens↔perícias↔poderes.

### Classes (integradas)

`extrair_classes.py` → `dados/classes.json` (**14 classes**, Arcanista a Paladino,
págs 42–90). Mesmo método (tipografia), segmentado por dois marcadores tam-21:
"Características de Classe" e "Habilidades de Classe". Cada registro:
```
id, tipo="classe", nome, fonte, versao, pagina, resumo,
caracteristicas { "Pontos de Vida", "Pontos de Mana", "Perícias", "Proficiências" },
habilidades [ {nome, efeito} ]
```
Conferência: `dados/classes_tormenta.html`. Rode a extração com `python extrair_classes.py`.

Decisões/limites do v1:
- **Tabela de progressão por nível OMITIDA** (o cabeçalho vazava; filtrado por
  conteúdo. A info "no Xº nível…" está no texto das habilidades). Candidata a v2.
- **Classes do núcleo NÃO têm campo "Atributo Principal"** — o stat block é só
  PV/PM/Perícias/Proficiências. O atributo-chave (ex.: Carisma do paladino) é
  **emergente** das habilidades, não um rótulo. O ganho aqui é texto completo e
  limpo, não um campo explícito.
- Sobre-segmentação leve: termos em negrito internos (ex.: no Inventor) viram
  "habilidades" — sem perda de texto.

**Integração ao índice (FEITA).** `integrar_classes.py` substitui os 109 chunks
antigos de classe (texto corrido) por chunks estruturados. **Granularidade
diferente das raças** (classes são grandes — a classe inteira daria ~2000-3800
tokens, estouraria o contexto de 4096 do Ollama e diluiria o embedding): cada
classe vira **1 chunk de visão geral** (resumo + características) + **1 chunk por
habilidade** (auto-identificado pela classe). As "Poder de X" ficam como um chunk
único (lista de poderes; granularidade por poder é da futura família "poderes").
Total: 14 → **111 chunks** (14 visão geral + 97 habilidades). Reconstrói o índice
sem reembutir o resto (só os 111 são embutidos, ~200s). Índice: **1144 → 1146**.
Idempotente.

Efeito medido: "o que faz o Golpe Divino" → chunk da habilidade no rank 1;
"proficiências do Guerreiro" / "me explique o Inventor" → chunk de visão geral no
rank 1. Perguntas específicas acertam a habilidade; gerais, a visão geral.

**Atributo principal por classe — NO CHUNK (RAG, não regex) (FEITO).** As classes do núcleo
não repetem o "Atributo Principal" no bloco de cada classe (págs 42+), então "qual o atributo
do paladino?" não tinha resposta no chunk de visão geral e a busca vetorial puxava um chunk
genérico do Cap. 5 → o LLM chutava. **Fonte autoritativa:** a **Tabela 1-3 (Classes)**, pág. 32
(pág. 38 do PDF), tem a coluna **Atributo** para as 14 — inclusive a flexibilidade de build
("Força ou Destreza", "Destreza ou Inteligência", "Força e Carisma").

Decisão de arquitetura (com o usuário): **colocar o fato no chunk da classe** (RAG de verdade),
não um regex hard-coded. O regex resolveria de forma determinística, mas (a) é frágil a
formulações fora do padrão e (b) não melhora a recuperação — só empilha caso especial. Aceita-se
o não-determinismo em troca de robustez.

- `extrair_atributos_classe.py` lê a Tabela 1-3 por tipografia (coluna "Atributo" em x≈300,
  SourceSansPro ~9pt; valores de 2 linhas unidos por proximidade) → grava `atributo_principal`
  `{texto, atributos[], relacao: "ou"|"e"|null}` em `classes.json`. As 14 conferidas contra o
  livro. Rode `python extrair_atributos_classe.py` (`--dry` para só ver).
- `integrar_atributo_classe.py` verbaliza isso **no texto do chunk de visão geral** de cada
  classe e re-embute **só os 14** `subtipo=visao_geral` (mantém posição/ordem; NÃO toca em
  poderes → sem o caveat de ordem de re-run; `n_chunks` inalterado, ~20s). Além do fato, o texto
  **ensina a leitura**: a importância de um atributo vem de quantas habilidades/poderes da classe
  dependem dele → builds alternativas são viáveis (ex.: Guerreiro de Destreza); o livro destaca
  o(s) principal(is) sem torná-lo obrigatório. Idempotente.

Efeito medido: "quais os atributos do paladino?" → chunk do Paladino no **rank 1** (0,649, antes
perdia para o Cap. 5) → resposta **"Força e Carisma"** citando a Tabela 1-3; idem Guerreiro
("Força ou Destreza"), Arcanista ("Inteligência ou Carisma"). É **RAG puro** — sem detector de
intenção; funciona com qualquer formulação que recupere a classe.

**Nota — os dois limites que apareceram (registrados para depois):** (1) *contexto do Ollama*:
o padrão é 4096 tokens (`num_ctx`); o qwen3:8b suporta ~32K nativos, então dá para subir em
`_payload_ollama` quando entrar **diálogo multi-turno** (custa RAM/tempo de prefill na CPU). Para
RAG bem recuperado, 4096 basta. (2) *variação de build*: a "importância" real é emergente dos
poderes escolhidos; o chunk entrega o fato do livro + a regra de leitura, mas a agregação sobre
todos os poderes acessíveis (perfil de dependência de atributo, via `poderes_por_acesso`) não
cabe no contexto — candidata a um **chunk de evidência pré-computada** por classe.

**Derivação alternativa (mantida como metadado, não como resposta).** `derivar_atributo_chave.py`
grava `atributo_chave` em `classes.json` inferindo o atributo-**de-conjuração** das habilidades
reais (Bardo=Car, Clérigo/Druida=Sab via *Magias*; Arcanista por Caminho; Paladino=Car via
*Abençoado*). Serve à camada de regras (PM/conjuração), não à resposta ao usuário — essa vem do
`atributo_principal` no chunk. Guarda também um palpite `inferido` (contagem) claramente fraco,
nunca apresentado como fato.

**Evidência de dependência de atributo — POR PRÉ-REQUISITO (FEITO).** Extensão para o min-maxer
("se eu investir em Destreza, o que abre?"). Investigamos primeiro um **perfil por contagem de
menções** e o **descartamos**: ele mistura combate com flavor e **contradiz o livro** (Bucaneiro→
Carisma vs Destreza; Caçador→Sabedoria vs For/Des; Cavaleiro→Carisma vs Força) — apresentá-lo
ensinaria o modelo errado. O único sinal **auditável** é o **pré-requisito de atributo** (Stage B):
um poder que exige "Des 2" é dependência mecânica real. `integrar_evidencia_atributo.py` cria 1 chunk
`subtipo=evidencia_atributo` por classe (14; **10 com gate, 4 sem**) listando "o que cada atributo
destrava" entre os **poderes DA classe** (os gerais são compartilhados por todas → citados, não
enumerados por classe, senão apagam a identidade). O chunk traz o `atributo_principal` do livro no
topo + um **guarda-corpo explícito**: "isto é dependência mecânica, não 'importância'". Índice
**1648 → 1662 chunks** (+14). Idempotente. Efeito: "quais poderes do guerreiro dependem de Destreza?"
→ chunk de evidência no **rank 1** (0,67).

Limite honesto: os pré-requisitos de atributo são **esparsos** em T20 (poucos poderes de classe os
têm) — a evidência é fiel, mas modesta; não é uma medida de importância (essa continua sendo o
`atributo_principal` do livro + a leitura de build).

### Poderes — família RELACIONAL (Stage A feito: poderes de classe)

Poderes não são uma lista de entidades autocontidas: são **nós num grafo**, com
arestas de **pré-requisito** (poder→atributo, poder→outro poder, poder→nível) e
**categoria** que define **elegibilidade** (condição→categoria). É a família que
destrava o min/maxer. Categorias em T20: de classe, gerais (combate/destino),
magia (conjuradores), concedidos (devotos de um deus), tormenta. **Elegibilidade
não é pura classe→categoria** — concedidos dependem de *devoção* (escolha do
personagem, não da classe); magia depende de *conjurar*. Modelar como regras
condicionais, não tabela rígida.

Staging: **A** catálogo de nós (nome, categoria, efeito, pré-requisito COMO TEXTO);
**B** estruturar pré-requisitos em predicados; **C** regras de elegibilidade +
flags derivados; **D** camada que monta a árvore de um personagem avaliando B+C.

**Stage A (poderes de classe) FEITO.** `extrair_poderes_classe.py` explode as
listas "Poder de X" de `dados/classes.json` em **296 nós** (`dados/poderes_classe.json`),
**~150 com pré-requisito** (texto). Cada nó: `tipo="poder", categoria="classe",
classe, nome, efeito, pre_requisito, fonte, pagina`. Conferência:
`dados/poderes_classe.html`. Prévia dos tipos de pré-requisito (insumo do Stage B):
nível ~74, poder/outro ~34, perícia ~28, atributo ~15, devoto ~1.

Armadilha resolvida — **quadros de opção**: poderes como Familiar (Arcanista),
Totem Espiritual (Bárbaro), Companheiro (Druida) e melhorias de arma (Inventor)
têm um *quadro lateral* listando OPÇÕES (cada animal/espírito/papel). Essas opções
usam a fonte **`IowanOldStyle-Black`** (nunca usada em poder legítimo) e viravam
poderes falsos. `extrair_classes.py` **pula os blocos com essa fonte** — isso limpa
tanto `classes.json` (habilidades "Poder de X") quanto os poderes.

**Opções recuperadas (FEITO).** `extrair_opcoes_poder.py` lê de volta os quadros
`IowanOldStyle-Black` e anexa suas opções ao PODER dono, como campo `opcoes`, em
`poderes_classe.json`: **Familiar** (Arcanista, 10 animais, pg44), **Totem
Espiritual** (Bárbaro, 8 totens, pg48), **Companheiro Animal** (Druida — 6 papéis,
pg68 — e Caçador, que reaproveita os mesmos; o "página 62" do Caçador é cross-ref
furado). `integrar_poderes_classe.py` leva as opções ao texto do chunk do poder.
Efeito: "que animais posso escolher no Totem Espiritual" traz o poder no rank 1 com
os 8 totens. Rode `python extrair_opcoes_poder.py` (depois re-integre).
**Ainda fora** (não são quadro de opção de poder): **Forma Selvagem** do Druida (é
TABELA, "veja a seguir") e as **17 melhorias de arma do Inventor** (pertencem a uma
habilidade de classe, não a um poder selecionável). Imperfeição menor: blocos de
*regra geral* (ex.: preâmbulo das Bravatas) grudam no poder anterior — texto
preservado, mal-alocado.

⚠️ **Ordem de re-run dos integradores.** Os integradores de poder compartilham
`tipo="poder"`; cada um remove só os seus (`integrar_poderes_classe.py` →
`categoria=="classe"`; `integrar_poderes_gerais.py` → categorias gerais). Se
re-rodar **`integrar_poderes_classe.py`**, re-rode **`integrar_poderes_gerais.py`**
em seguida por garantia. Cuidado análogo: `integrar_classes.py` remove por
`"Classes >" in secao`, que também casa a seção dos poderes de classe — re-rodá-lo
sozinho exige depois re-rodar os integradores de poder de classe.

**Integração ao índice (FEITA).** `integrar_poderes_classe.py` substitui os **14
chunks grossos "Poder de X"** (a lista inteira que `integrar_classes.py` metera como
uma habilidade única) por granularidade fina:
```
python integrar_poderes_classe.py
```
O que ele faz: backup de `index\`; remove os 14 chunks grossos "Poder de X" (e
quaisquer `tipo="poder"` de um re-run); gera **1 chunk por poder** (nome +
efeito + pré-requisito verbalizado — serve ao embedding **e** ao contexto do LLM) e
**1 chunk-lista leve por classe** (só os nomes — preserva o "quais poderes o X pode
escolher" que o chunk grosso fazia; curto, não estoura o contexto de 4096);
reconstrói o índice **sem reembutir os outros chunks** (só as 310 unidades de poder
são embutidas, ~196s); grava os campos estruturados (`tipo="poder"`,
`categoria="classe"`, `classe`, `nome`, `pre_requisito`) como metadados —
insumo dos Stages B/C/D. Total: **296 poderes → 310 chunks** (296 poderes + 14
listas). Índice: **1146 → 1442 chunks** (−14 grossos, +310). Idempotente.

Efeito medido (busca vetorial): "o que faz o poder Arcano de Batalha" traz o chunk
do poder no top-3 (o LLM recebe o efeito); "quais poderes o Bárbaro pode escolher"
traz o chunk-lista da classe no **rank 1**; o sistema distingue *poder* de
*habilidade de classe* (ex.: "Ataque Furtivo do Ladino" reconhece que Ataque Furtivo
é habilidade, não poder).

Nota de recuperação: em perguntas de efeito muito específico o chunk-lista às vezes
empata/passa à frente do chunk do poder (ambos ficam no top-5, então o efeito chega ao
LLM) — se virar padrão nos logs, dá para excluir o subtipo `lista` da busca quando a
pergunta é sobre um poder nomeado.

### Poderes gerais (Stage A feito — integrados)

As demais categorias de poder **não vêm de `classes.json`**: ficam numa seção própria
do livro (**Capítulo 2: Perícias & Poderes, págs 130–143**). `extrair_poderes_gerais.py`
extrai por **tipografia** (não pelo TOC) → `dados/poderes_gerais.json`:
```
python extrair_poderes_gerais.py
```
**162 poderes**: combate 40, destino 20, magia 8, concedidos 72, tormenta 22 (67 com
pré-requisito). Cada nó: `tipo="poder", categoria (combate|destino|magia|concedido|
tormenta), nome, efeito, pre_requisito (texto), fonte, pagina`.

**Tipografia = schema:** cabeçalho de categoria = `Tormenta20-Regular` ~27; nome do
poder = `Tormenta20` ~16 (pode ocupar 2 linhas → junta); efeito = `IowanOldStyle-Roman`
~9.5 (o "Pré-requisito:" em itálico fica embutido e é separado depois). A intro
("Grupos de Poderes") fica antes do 1º cabeçalho ~27 e é ignorada; processa o fluxo
inteiro trocando a categoria a cada cabeçalho.

**Concedidos trazem o DEUS.** Entre o nome e o efeito há um span `Tormenta20` ~11 com
o(s) deus(es) concedente(s) (ex.: "Ataque Piedoso" → Lena, Thyatis) — capturado em
`deuses[]`, já como insumo de **elegibilidade por devoção** (Stage C). Os nomes são
canonicalizados contra o panteão (corrige "Lin-wu"→"Lin-Wu" do PDF). Sinal de
consistência: os **20 deuses concedem exatamente 4 poderes cada**.

**Conferência:** `dados/poderes_gerais.html` (gerada por `gerar_poderes_gerais_html.py`,
que reusa o CSS da ferramenta de classe). Filtra por categoria e, nos concedidos, por
deus.

**Integração ao índice (FEITA).** `integrar_poderes_gerais.py` substitui os **29
chunks de texto corrido** da seção "Poderes Gerais" (págs 130–143, gerados pela
ingestão via TOC) por granularidade fina:
```
python integrar_poderes_gerais.py
```
Gera **1 chunk por poder** (nome + efeito + pré-requisito + deus verbalizados) + **1
chunk-lista por categoria** (nomes) + **1 chunk-lista por deus** (os concedidos de cada
deus — o análogo por-deus ao "por-classe"). NÃO toca nos poderes de classe
(`categoria="classe"`); reconstrói o índice sem reembutir o resto (só os 187 novos,
~72s). Total: **162 poderes → 187 chunks** (162 + 5 listas-categoria + 20 listas-deus).
Índice: **1442 → 1600 chunks** (−29 texto corrido, +187). Idempotente.

Efeito medido (busca vetorial): "que poderes o deus Khalmyr concede" → chunk-lista do
deus no **rank 1** (o caso de uso do devoto/min-maxer); "poder concedido Aura de Paz" →
o poder no rank 1 já com `deus=Marah`; "poderes de combate" → lista-categoria no rank 1;
"Esquiva" distingue o poder geral do poder de classe.

**Stages B/C/D FEITOS (motor relacional — o auxiliar do min-maxer).** Operam sobre os
JSON de poder (não sobre o índice — não re-embutem; o texto dos chunks não muda):

- **Stage B — predicados** (`estruturar_prereqs.py`). Converte `pre_requisito` (TEXTO)
  em `pre_requisito_estruturado`: lista de grupos-**AND**, cada um `{"ou":[átomos]}`
  (**OR** interno). Átomos tipados: `atributo` (attr/valor), `nivel_classe`,
  `nivel_personagem`, `treino_pericia` (perícia canonizada + `especializacao`),
  `proficiencia`, `poder` (com `ref_ids` **resolvidos** contra o catálogo — fecha a
  dívida poder→poder), `classe`/`caminho` (Bruxo/Mago/Feiticeiro = caminhos do
  Arcanista), `devoto`, `conjuracao`/`habilidade_classe`, `poder_quantificado`
  (quantidade + grupo: Tormenta/armadilha/Missa) e `livre` (fallback auditável).
  Cobertura: **219 poderes, 0 refs de poder órfãs, 8 átomos livres** (todos legítimos:
  citam magias/habilidades de classe fora do catálogo de poder). Gramática: vírgula =
  AND (respeita parênteses), " ou " = OR, "A e B" dentro de "treinado em" = duas perícias
  AND; aceita `º` e `°` no nível; narrativa ("ter conquistado terras…") vira `livre`.

- **Stage C — elegibilidade** (`elegibilidade.py`). Deriva o campo `elegibilidade` em
  cada poder: a dimensão de **ACESSO** que os predicados não capturam. Regra por
  categoria: `classe`→só a própria; `combate`/`destino`→geral (14 classes);
  `tormenta`→geral; `magia`→conjuradores (**Arcanista/Bardo/Clérigo/Druida**, derivados
  da habilidade "Magias" em `classes.json`), `requer_conjuracao`; `concedido`→**devoção**
  (`requer_devocao`, `deuses[]` do poder → `deuses.json.devotos` → classes elegíveis,
  reusando `casa_devoto`/amplo/clérigo=todos). Também grava flags derivados dos
  predicados: `nivel_minimo` e `atributos_minimos`. Ex.: concedido de Aharadak (amplo) →
  14 classes; de Allihanna → Bárbaro/Caçador/Clérigo/Druida (raças como "elfos" ficam
  fora das *classes*, corretamente).

- **Stage D — motor do personagem** (`personagem.py`). Avalia B+C para um personagem
  concreto (`classe, nivel, caminho?, deus?, raca?, atributos, pericias, poderes`) e
  responde: `disponiveis()` (poderes que pode pegar **agora**) e `arvore(nome)` (árvore
  recursiva de pré-requisitos, para planejar). CLI:
  ```
  python personagem.py                      # demo: Paladino 6 devoto de Khalmyr
  python personagem.py --arquivo p.json     # personagem de arquivo
  python personagem.py --arvore "Ripostar"  # Ripostar → Aparar → Esgrimista → Int 1
  ```
  Efeito medido (demo): 70 poderes disponíveis, e os concedidos são **exatamente os 4 de
  Khalmyr** (não os 72) — o ganho do min-maxer. Bloqueios trazem a razão exata
  ("ser da classe Bucaneiro", "poder Aparar", "12º nível de bucaneiro"). Predicados não
  modelados (`proficiencia`, `livre`) viram **indeterminado** ("verificar: …"), nunca
  falso-positivo silencioso.

**Limitações reconhecidas de B/C/D.** (a) `proficiencia` e `livre` não são avaliáveis →
marcados como indeterminado; (b) o átomo `devoto` de Arma Sagrada não impõe o "exceto
Lena e Marah" (a exceção fica em `detalhe`, texto); (c) personagem é **mono-classe** (o
átomo `classe`/`nivel_classe` de outra classe = multiclasse não é satisfeito).

**Integração ao RAG (FEITA).** `perguntar.py` importa o motor (`personagem.py`) e, antes
da busca vetorial, `detectar_intent_poder()` reconhece duas intenções (conservador — só
dispara com sinal claro + entidade nomeada) e responde com um **bloco factual
determinístico** que entra como Fonte; o Qwen apenas **redige** (instruído a reproduzir
fielmente, sem inventar pré-requisito). Não toca no índice (o motor lê os JSON) → **não
re-embute**. As duas intenções:
- **Planejamento** ("o que preciso para o poder Ripostar?", "pré-requisitos de X", "como
  pego X"): bloco = efeito + quem pode pegar + **árvore de pré-requisitos** (Ripostar →
  Aparar → Esgrimista → Int 1). Usa B+C.
- **Elegibilidade por classe** ("que poderes um paladino nível 6 devoto de Khalmyr pode
  pegar?"): bloco = poderes **acessíveis à classe** (Stage C), agrupados por categoria,
  filtrando por nível (se dado) e, nos concedidos, pelo deus (se dado). Extrai
  classe/nível/deus da pergunta. Sem atributos/perícias na NL, usa o **acesso da classe**
  (não a elegibilidade estrita — essa é o CLI `personagem.py`).

O log (`logs/consultas.jsonl`) grava `filtro_poder` ({tipo, rotulo}). Efeito medido:
"o que preciso para pegar o poder Ripostar?" → resposta correta (Aparar, 12º nível de
Bucaneiro, classe Bucaneiro), busca ~0,08 s (sem vetorial). A interface web usa o mesmo
`buscar()`/`montar_prompt()`, então funciona sem alterações.

**Próximo passo.** (1) Dados que faltam: a **tabela** da Forma Selvagem (Druida) e as **17
melhorias de arma do Inventor**. (2) Elegibilidade ESTRITA na NL (parsear um personagem
completo da pergunta, ou aceitar uma ficha) para usar `disponiveis()` em vez do overview
por classe. (3) Camada de derivação/inferência com evidência (ex.: "atributo mais
importante do Inventor").

### Deuses (integrados)

`extrair_deuses.py` → `dados/deuses.json` (**20 deuses** do Panteão, págs 102–111).
Tipografia: nome = `Tormenta20` ~21 **E** pertencente ao PANTEÃO (assim a intro, cujos
cabeçalhos também são ~21, é ignorada); campos em rótulos negrito (podem vir partidos —
pula-se todo span negrito, trocando de campo só no rótulo conhecido; prefixos
comparados **sem acento**). Cada registro:
```
id, tipo="deus", nome, pagina, resumo, crencas, simbolo,
energia (Positiva|Negativa|Qualquer), arma_preferida,
devotos [lista], poderes_concedidos [lista], obrigacoes, fonte, versao
```
`devotos` (raças/classes que podem seguir — alguns são regra livre, ex.: Aharadak
"Quaisquer") e `poderes_concedidos` são parseados em listas. Os poderes concedidos são
**canonizados** contra os nomes reais dos concedidos (`poderes_gerais.json`), fechando
divergências de caixa (Title Case da tabela vs sentence case da entrada) — resultado:
**0 divergências**, cross-ref exato. Sinal de consistência: os **20 deuses × 4 poderes
concedidos** batem com a extração dos concedidos.

Conferência: `dados/deuses.html` (gerada por `gerar_deuses_html.py`) — filtra por
energia. Rode `python extrair_deuses.py`.

**Integração ao índice (FEITA).** `integrar_deuses.py` substitui os **47 chunks de texto
corrido** de deus (mantendo a intro) por **20 chunks estruturados** (1 por deus; resumo +
campos no texto; `energia`/`devotos`/`poderes_concedidos` como metadados). Índice:
**1497 → 1470 chunks** (−47, +20). Idempotente.
```
python integrar_deuses.py
```
**Filtro híbrido / por metadado (FEITO).** Em `perguntar.py`, `detectar_filtro_deus()`
exige "deus/deuses" + (a) energia (Positiva/Negativa/Qualquer) ou (b) uma classe/raça.
**Tema de acentos/plural:** o matcher de devoto (`_casa_devoto`) dobra acento e plural,
inclusive o irregular "ão↔ões" — "paladino" casa "paladinos", "anão" casa "anões".
Regras especiais: humano/clérigo seguem **qualquer** deus (campo "todos"); deuses de
aceitação ampla (Aharadak "Quaisquer", Valkaria "todas as classes") entram em qualquer
consulta de devoto. Efeito medido: "paladino" → 9 deuses; "anão" → 6; "energia negativa"
→ os 5 negativos; "humano" → todos os 20. O log grava `filtro_deus`. Esta é a **base de
elegibilidade do Stage C** (devoção→concedidos), conectando deuses↔classes/raças↔poderes
concedidos.

### Atributos e Construção de Personagem (integrados)

Início do Capítulo 1 (págs 22–23). `extrair_atributos.py` produz DOIS arquivos:
- `dados/atributos.json` — **6 atributos** (Força•For … Carisma•Car): `nome`, `abrev`,
  `descricao` e **`pericias_governadas`** (perícias citadas na descrição, casadas contra
  as 29 reais). Cross-check: o mapa atributo→perícias bate **exatamente** com o
  perícia→atributo de `pericias.json` (29 perícias, dois sentidos consistentes) — valida
  ambas extrações e fecha o grafo atributo↔perícia.
- `dados/criacao_personagem.json` — **9 passos** de criação (Atributos→Raça→Classe→
  Origem→Divindade→Perícias→Equipamento→Magias→Toques Finais) + **Definindo atributos**
  (texto Pontos/Rolagens/Atributos Mínimos + **tabela de custo** valor→pontos→rolagem).

`integrar_atributos.py` substitui os 5 chunks de texto corrido ("Conceito de Personagem"
+ "Atributos Básicos") por **8 chunks**: 6 de atributo + 1 "Passos da Construção" + 1
"Definindo seus atributos". Índice: **1470 → 1473**. Idempotente. Conferência:
`dados/atributos.html` (por `gerar_atributos_html.py`) — mostra passos, atributos e a
tabela de custo.

Efeito medido: "quais os passos para criar um personagem" → chunk dos passos (sim 0,71);
**"criação de personagem por pontos" → os chunks procedurais no rank 1–2** (era rank 20 —
falha do §10 resolvida).

**Filtro híbrido / por metadado (FEITO).** Em `perguntar.py`, `detectar_filtro_atributo()`
exige a palavra "atributo" + (a) uma **perícia** → devolve o atributo que a governa
(inverso: "qual atributo governa a perícia Atletismo" → Força), ou (b) um **nome de
atributo** → devolve o próprio (direto: "o que faz o atributo Destreza" → Destreza). O
gatilho "atributo" separa do filtro de perícia ("perícias de Destreza" continua listando
perícias). O log grava `filtro_atributo`.

### Equipamentos (Capítulo 3 completo — integrados)

`extrair_equipamentos.py` → `dados/equipamentos.json` (**219 registros estruturados**, págs 144–173):
- **Armas & Munições (47 itens)**: Tabela 3-3 (Simples, Marciais, Exóticas, Fogo) + Descrições (págs 152–157) com dano, crítico, alcance, tipo de dano, proficiência, empunhadura, espaços, preço e regras completas.
- **Armaduras & Escudos (12 itens)**: Tabela 3-5 (Leves, Pesadas, Escudos) + Descrições (pág 160) com defesa, penalidade de armadura, espaços, preço e regras.
- **Itens Gerais (121 itens)**: Tabela 3-6 (9 subcategorias: Equipamento de Aventura, Ferramentas, Vestuário, Esotéricos, Alquímicos [Preparados, Catalisadores, Venenos], Alimentação, Animais, Veículos, Serviços) + Descrições mecânicas completas (págs 161–170).
- **Melhorias Superiores (29 melhorias)**: Tabela 3-8 + págs 170–172 com `aplica_a` e efeitos mecânicos.
- **Materiais Especiais (6 materiais)**: Aço-Rubi, Adamante, Gelo Eterno, Madeira Tollon, Matéria Vermelha, Mitral com efeitos em armas, armaduras/escudos, esotéricos e tabela de custos adicionais (Tabela 3-9).
- **Regras Procedurais (4 blocos)**: Riqueza & Moedas (Tabela 3-1), Usando & Carregando (Limites de Uso e Carga), Características das Armas & Passos de Dano (Tabela 3-2), Regras de Itens Superiores e Modificações (Tabela 3-7).

Conferência: `dados/equipamentos.html` (gerada por `gerar_equipamentos_html.py`) — visualizador offline com busca instantânea, badges de estatísticas e filtros por categoria.

**Integração ao índice (FEITA).** `integrar_equipamentos.py` substitui os **64 chunks grossos de 2000 caracteres** do Capítulo 3 por **239 chunks estruturados finos** (1 chunk por item específico + 20 chunks-lista de visão agregada + 4 procedurais). Reconstrói o índice sem reembutir o resto (~230s). Índice: **1473 → 1648 chunks** (−64 grossos, +239 novos). Idempotente.
```
python integrar_equipamentos.py
```

**Filtro híbrido / por metadado (FEITO).** Em `perguntar.py`, `detectar_filtro_equipamento()` identifica listagens categóricas:
- "armas simples", "armas marciais", "armas exóticas", "armas de fogo"
- "armaduras leves", "armaduras pesadas", "escudos"
- "materiais especiais", "melhorias superiores"
- "itens esotéricos", "preparados alquímicos", "venenos"

Efeito medido:
- "qual o dano e crítico da adaga?" → chunk da Adaga no **rank 1** (Score 0.533).
- "o que faz a Armadura Completa?" → chunk da Armadura Completa no **rank 1** (Score 0.572).
- "como funciona o Bálsamo Restaurador?" → chunk do Bálsamo Restaurador no **rank 1** (Score 0.655).
- "quais são os materiais especiais e o que o Aço-Rubi faz?" → Aço-Rubi no **rank 1** (Score 0.602) e Lista de Materiais no **rank 2**.
- "quais são as armas de fogo?" → Filtro híbrido ativa e retorna Pistola, Mosquete e Lista de Armas de Fogo.

### Magia (Capítulo 4)
- Documentação completa da família estruturada de Magia: consulte [docs/familias/magia.md](docs/familias/magia.md).

### Ameaças / Bestiário (Capítulo 7)
- Documentação completa da família estruturada de Ameaças: consulte [docs/familias/ameacas.md](docs/familias/ameacas.md).

### Regras de Jogo, Combate & Parceiros (Capítulo 5 & 6)
- Documentação completa da família estruturada de Regras de Jogo e Parceiros: consulte [docs/familias/jogando.md](docs/familias/jogando.md).

### Recompensas, Itens Mágicos & Artefatos (Capítulo 8)
- Documentação completa da família estruturada de Recompensas e Itens Mágicos: consulte [docs/familias/recompensas.md](docs/familias/recompensas.md).

### O Mundo de Arton (Capítulo 9)
- Documentação completa da família estruturada do Mundo de Arton: consulte [docs/familias/mundo_arton.md](docs/familias/mundo_arton.md).

### Fichas das 14 Classes (Capítulo 1) & O Mestre (Capítulo 6)
- Documentação completa da família estruturada de Fichas de Classes e O Mestre: consulte [docs/familias/mestre_classes.md](docs/familias/mestre_classes.md).

### Condições (Apêndice)
- Documentação completa da família estruturada de Condições: consulte [docs/familias/condicoes.md](docs/familias/condicoes.md).

---

## 12. Para continuar este projeto (IA ou pessoa)

1. Leia este README inteiro — ele descreve o estado real.
2. Confirme o ambiente: Ollama no ar (`ollama list` deve mostrar `qwen3:8b`),
   Python base com `pymupdf`/`sentence-transformers`/`faiss`/`requests`.
3. Para analisar a qualidade, **comece pelos logs** (`logs/avaliacoes.jsonl` e
   `logs/consultas.jsonl`), olhando os casos "Problema".
4. Só reprocesse o índice (`ingestao.py`) com **evidência acumulada**; prefira
   melhorias sem re-embute (busca híbrida) quando possível.
5. **Direitos autorais:** Tormenta20 é material protegido — manter **local e para
   uso pessoal**, com exemplar próprio.
