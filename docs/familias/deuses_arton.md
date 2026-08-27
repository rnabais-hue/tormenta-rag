# Família estruturada: *Deuses de Arton* (4º livro de expansão)

> **Status: EM CURSO.** `fonte="deuses-arton"` (registrado em [`fontes.py`](../../fontes.py)).
> Livro de 324 págs; layout = Heróis/núcleo (corpo IowanOldStyle, nomes Tormenta20, caixas
> SourceSansPro). O núcleo já tem a família `deuses` (20 deuses) — o Deuses de Arton EXPANDE
> tudo com registros próprios `fonte="deuses-arton"` que COEXISTEM (contrato multi-livro).

## Estrutura do livro (TOC nativo, 195 entradas)

- **Cap. 1: Campeões dos Deuses** (11–68): Classes Divinas (Sacerdote/Druida/Paladino de X),
  Autoridades Divinas, Nova Linhagem Abençoada, **Nova Classe: Frade**, Novos Poderes
  Concedidos, Equipamentos Religiosos, Itens Litúrgicos, **Magias Divinas**. — MECÂNICO.
- **Cap. 2: Distinções** (69–144): 23 distinções divinas (mesmo formato do Heróis). — **INTEGRADO**.
- **Cap. 3: Deuses e Avatares** (145–252): 20 deuses maiores expandidos (4 págs cada) +
  Deuses Menores + Antigos Deuses + Artefatos Divinos. — LORE + mecânica.
- **Cap. 4: Ameaças Divinas** (253–320): bestiário (Abissais, Aspectos, Celestiais, Fadas,
  Gênios, Gigantes) + Perigos Complexos + tabela por ND. — **INTEGRADO** (56 criaturas).

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
Khalmyr, Paladino de Valkaria, Frade visão-geral, Frade: Solo Santificado).

### Resto do Cap. 1 (`capitulo="cap1-resto"`, 217 chunks)

`extrair_magias_deuses.py` + `extrair_poderes_concedidos_deuses.py` +
`extrair_itens_religiosos_deuses.py` → `integrar_cap1_resto_deuses.py`.

- **29 Magias Divinas** (62–68, `tipo="magia"`): reusa o schema/stat-block do núcleo (extrair_magias);
  26 divina + 3 universal, com aprimoramentos.
- **75 Novos Poderes Concedidos** (44–49, `tipo="poder"` `categoria="concedido"`): nome 16pt + tag
  **deus** 11pt (multi-deus dividido por vírgula) + efeito; os 20 deuses maiores cobertos.
- **110 itens** (50–61): **75 Equipamentos Religiosos** (`equipamento_religioso`, rótulo bold por
  subcategoria) + **35 Itens Litúrgicos** (`item_liturgico`, nome 16pt). Troca de modo litúrgico por
  página (≥57); SUBCATS accent-free. *(As subcategorias dos equipamentos ficam imperfeitas — os itens
  são completos (nome+descrição), só o metadado `categoria` às vezes agrupa errado.)*

Índice 3714→**3931**; `deuses-arton` 44→**261**. Recuperação rank-1 (Couraça de Allihanna, Dom da
Furtividade/Hyninn, Cilício Vivo, Água Benta Concentrada).

### Menores do Cap. 1 (`capitulo="cap1-menores"`, 64 chunks) — FECHA o Cap. 1

`extrair_devotos_menores_deuses.py` → `integrar_cap1_menores_deuses.py`. Quatro blocos pequenos:
- **20 Autoridade Eclesiástica** (24–25, `autoridade_eclesiastica`): por deus, o título/benefício de
  liderança do clero (rótulo negrito = deus + texto).
- **20 Outros Devotos** (36–37, `devotos_permitidos`): por deus, quais raças/classes podem cultuá-lo.
- **Linhagem Abençoada** (35, `linhagem`): 3 habilidades (Básica/Aprimorada/Superior) — **rótulos
  ITÁLICOS com bullet** ("• Básica."), diferente do Suraggel (negrito).
- **22 Heranças do Suraggel** (38–39, `heranca_suraggel`): "• Herança de X." (negrito) + efeito.

Índice 3931→**3995**; `deuses-arton` 261→**325**. **CAP. 1 do Deuses 100% COMPLETO.** Recuperação
rank-1 (Devotos de Khalmyr, Linhagem Abençoada).

### Distinções Divinas — Cap. 2 (`capitulo="distincoes"`, 139 chunks)

`extrair_distincoes_deuses.py` → `integrar_distincoes_deuses.py`. **23 distinções** (entidade nova):
1 overview cada (conceito + Admissão + Marca + lista de poderes) + **115 poderes** com efeito limpo
+ 1 lista geral. **0 poderes finos** (efeito < 40c) — nada foi para backlog.

**PORTE do `extrair_distincoes_herois.py`** (mesma família de layout). Reusa: TOC como lista de nomes,
máquina de estados conceito→Admissão→Marca→Poderes, `COL_X=280`, corpo IowanOldStyle, descarte de
caixas SourceSansPro. **Diferença vs. Heróis:** aqui o TOC aponta para a PRÓPRIA página de splash (não
a mecânica), então os pares (nome, página) do TOC dão os limites diretamente (cada distinção = da sua
página até a anterior à próxima). Ajustes: `cola-drop-cap SÓ no conceito` (marca/poderes começam com
corpo normal e podem iniciar com "A cada" — não colar lá); capitalização inicial de nome de poder
(versalete às vezes vem minúsculo: "titereiro"→"Titereiro"). Exegeta do Akzath tem só 2 poderes
(Círculo Externo/Interno) — correto, não é merge.

Índice 4061→**4200**; `deuses-arton` 391→**530**. Recuperação rank-1 (Cavaleiro de Khalmyr, Numeromante,
Sombra de Tenebra, poder "Sopro Compartilhado").

### Bestiário Divino — Cap. 4 (`capitulo="cap4-ameacas-divinas"`, 66 chunks)

`extrair_ameacas_deuses.py` → `integrar_ameacas_deuses.py`. **56 criaturas** (`tipo="ameaca"`)
em 6 grupos: Abissais (10), Aspectos dos Deuses (6), Celestiais (12), Fadas (13), Gênios (7),
Gigantes (10). Mais 6 chunks-lista por grupo + 4 chunks-lista por faixa de ND.

**Por que NÃO foi um porte direto do Ameaças de Arton:** este livro usa o STAT BLOCK COMPACTO
com rótulos em **VERSALETE** — a maiúscula sai a ~9pt e a continuação a ~6.3pt
(SourceSansPro-Bold-SC700). Achatar spans (como no Ameaças) embaralha a continuação e perde
espaços internos. O motor aqui é **BASE-LINHA e DIRIGIDO POR RÓTULOS** (descoberta reutilizável):
1. Reconstrói cada LINHA concatenando spans em ordem-x (o versalete cola certo: "Iniciativa +10").
2. Segmenta por âncora (Nome Tormenta20 16pt + ND + Tipo/Tamanho); **`COL_SPLIT=280`** — a coluna
   direita começa em x≈289 e o ND da esquerda fica em x≈233 (mesma geometria das Distinções).
3. Classifica cada linha pelo rótulo inicial (regex SEM `\b` no fim, pois o valor cola:
   "Defesa26"); linhas sem rótulo = continuação. Habilidade = título Bold-SC700 que NÃO é rótulo.
4. Formato compacto às vezes OMITE atributos e usa **"—" (em-dash) para stats de não-combatentes**
   (ex.: Luminar): completude aceita ND+Def+PV OU (Iniciativa + Tipo + ≥2 habilidades) — o que
   distingue ficha real de cabeçalho-splash.

Resíduo (5 em `ameacas_deuses_pendentes.json`, fora do índice): 3 splash-duplicados de Aspectos já
capturados + 2 cabeçalhos-splash de seção (Duende, Gênio da Terra) — todos corretamente excluídos.

Índice 3995→**4061**; `deuses-arton` 325→**391**. Recuperação rank-1 (Aucharai, Gigante do Fogo,
Dríade, Aspecto de Khalmyr).

## Backlog (não integrado)

- ~~**Cap. 2:** Distinções divinas~~ — **FEITO** (23 distinções, 115 poderes, ver acima).
- **Cap. 3:** 20 deuses expandidos + menores/antigos + artefatos divinos (lore + mecânica).
- ~~**Cap. 4:** bestiário divino~~ — **FEITO** (56 criaturas, ver acima).
