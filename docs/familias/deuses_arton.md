# Família estruturada: *Deuses de Arton* (4º livro de expansão)

> **Status: EM CURSO.** `fonte="deuses-arton"` (registrado em [`fontes.py`](../../fontes.py)).
> Livro de 324 págs; layout = Heróis/núcleo (corpo IowanOldStyle, nomes Tormenta20, caixas
> SourceSansPro). O núcleo já tem a família `deuses` (20 deuses) — o Deuses de Arton EXPANDE
> tudo com registros próprios `fonte="deuses-arton"` que COEXISTEM (contrato multi-livro).

## Estrutura do livro (TOC nativo, 195 entradas)

- **Cap. 1: Campeões dos Deuses** (11–68): Classes Divinas (Sacerdote/Druida/Paladino de X),
  Autoridades Divinas, Nova Linhagem Abençoada, **Nova Classe: Frade**, Novos Poderes
  Concedidos, Equipamentos Religiosos, Itens Litúrgicos, **Magias Divinas**. — MECÂNICO.
- **Cap. 2: Distinções** (69–144): 22 distinções divinas (mesmo formato do Heróis).
- **Cap. 3: Deuses e Avatares** (145–252): 20 deuses maiores expandidos (4 págs cada) +
  Deuses Menores + Antigos Deuses + Artefatos Divinos. — LORE + mecânica.
- **Cap. 4: Ameaças Divinas** (253–320): bestiário (Abissais, Aspectos, Celestiais, Fadas,
  Gênios, Gigantes) + Perigos Complexos + tabela por ND.

## Integrado

### Classes Divinas — Cap. 1 (`capitulo="classes-divinas"`, 44 chunks)

`extrair_devotos_deuses.py` + `extrair_frade_deuses.py` → `gerar_classes_divinas_deuses_html.py`
→ `integrar_classes_divinas_deuses.py` (idempotência estreita própria; estreia `deuses-arton`).

- **36 variantes de classe divina** (`tipo="devoto_variante"`): 21 **Sacerdote de X** + 6
  **Druida de X** + 9 **Paladino de X**. Cada uma = nome "Classe de Deus" (Tormenta20 ~21pt) +
  habilidades nomeadas (rótulo negrito + efeito; tipicamente Indumentária + Fundamentalista).
  Campos `classe` e `deus` derivados do nome. **Achado:** título de seção ≥24pt ENCERRA a
  variante (senão "Sacerdote do Panteão" absorvia a seção "Autoridade Eclesiástica" com os 20
  nomes de deus); capitalização de nomes hifenizados (Lin-Wu, Tanna-Toh).
- **Nova Classe: Frade** (`tipo="classe"`): visão geral (PV/PM/perícias/proficiências parseadas
  do bloco de Características, que vêm colados num span) + 6 habilidades (Devoto Fiel, Erudição,
  Versiculário, Poder de Frade, Dádiva da Fé, Solo Santificado).

Índice 3670→**3714**; `deuses-arton` estreia com 44 chunks. Recuperação rank-1 (Sacerdote de
Khalmyr, Paladino de Valkaria, Frade visão-geral, Frade: Solo Santificado). Cosmético: o kerning
do PDF às vezes injeta espaço em nomes ("Duyshid akk").

## Backlog (não integrado)

- **Resto do Cap. 1:** Autoridades Divinas, Nova Linhagem Abençoada, Outros Devotos, Suraggel
  Variantes, **Novos Poderes Concedidos**, Equipamentos Religiosos, Itens Litúrgicos, **Magias
  Divinas** (reusa o extrator de magias).
- **Cap. 2:** 22 Distinções divinas (reusa `extrair_distincoes_herois.py`, adaptado a este PDF).
- **Cap. 3:** 20 deuses expandidos + menores/antigos + artefatos divinos (lore + mecânica).
- **Cap. 4:** bestiário divino (~50 criaturas; reusa o padrão de Ameaças de Arton).
