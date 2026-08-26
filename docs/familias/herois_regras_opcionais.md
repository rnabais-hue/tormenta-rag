# Família estruturada: *Heróis de Arton* — Cap. 4: Regras Opcionais

> **Status: RECORTE SEGURO INTEGRADO** (as listas entity-like do capítulo). 2º livro de
> expansão, `fonte="herois-arton"`, `capitulo="regras-opcionais"`. Cap. 4 (págs 280–331) =
> regras opcionais avulsas + o subsistema Domínios. Prioridade do usuário entre livros: **1 → 3 → 2 → 4**.

O Cap. 4 é heterogêneo: parte é **procedural** (módulos de regra soltos, como no
`regras_jogo` do núcleo), parte são **listas nomeadas entity-like**. Este recorte integrou
as listas (limpas e de alto valor p/ o jogador); os módulos procedurais e o subsistema
Domínios ficam no BACKLOG (ver fim).

## 0. Particularidades de layout (reusadas + novas)

Herda tudo de [`herois_campeoes.md`](herois_campeoes.md) §0 (corpo IowanOldStyle; negrito por
flag OU "Bold"; SourceSans = pull-quotes/caixas; drop-caps; splash de capítulo). **Novidades
deste capítulo:**

- **Duas colunas** por página → ordenação por bloco (`bcol = 0 se x0 < 40% da largura,
  senão 1`), reusando o método de `extrair_origens_herois.py`. Ordenar por y puro intercala
  as colunas.
- **`juntar()` (novo helper reusável):** cada span é uma LINHA; a junção reconstrói o fluxo —
  hífen de quebra (`letra-` no fim) → cola sem hífen; senão insere espaço quando nenhum lado
  já tem separador. Resolve `responsabi-lidade` e `tesoureiro.Bens` (linhas sem espaço final).
  A `dehyph()` deixou de "manter o hífen" (o núcleo mantinha) — este livro usa hífen de quebra
  de linha ASCII de verdade.
- **Drop-cap religado:** a letra capitular (Tormenta20 ≥36pt, 1 letra) é guardada e prefixada
  ao próximo corpo (senão "Grupos" virava "rupos").
- **Detecção de CAIXAS via `page.get_drawings()`:** retângulos preenchidos grandes (w≥100,
  h≥55) são **caixas** (tabelas embutidas / sidebars tingidas). Seus spans saem do fluxo
  principal (senão a caixa, que fica no topo da coluna, **rouba** o texto que a contorna — foi
  o bug do objetivo *Riqueza* e da Tabela 4-2 embutida em Idades). Um retângulo que contém um
  span **≥24pt é banner de título**, não caixa → flui normal. Título de tabela vazado ("Tabela
  N-…") fora do retângulo é filtrado à parte.

## 1. Sub-famílias integradas

| Sub-família | Págs | Extrator | Nº |
|---|---|---|---|
| **Papéis no Grupo** | 296–297 | `extrair_papeis_herois.py` | 9 |
| **Complicações** | 284–289 | `extrair_complicacoes_herois.py` | 54 (32 gerais + 22 de classe) |
| **Objetivos Heroicos** | 294–295 | `extrair_objetivos_herois.py` | 7 |
| **Idades Variadas** | 290–293 | `extrair_idades_herois.py` | 7 faixas + 19 mazelas |
| **Combate Avançado** | 298–306 | `extrair_combate_avancado_herois.py` | 18 regras + 3 tabelas |
| **Domínios** | 316–329 | `extrair_dominios_herois.py` | 23 módulos + 80 construções + tabela de unidades |

Cada extrator gera `dados/<familia>_herois.json` + uma ferramenta de conferência HTML
(`gerar_<familia>_herois_html.py` → `<familia>_herois.html`, offline). Nenhum toca no índice.

### Papéis no Grupo (`tipo="papel_grupo"`)
Funções que um jogador assume na mesa (Advogado, Arquivista, Bibliotecário, Cartógrafo,
Enfermeiro, Estrategista, Teratólogo, Tesoureiro, Xerife). Cada papel = **descrição** (corpo
não-negrito) + **benefício mecânico** (frase negrito "Se for o X, você recebe +…"). Âncora:
nome Tormenta20 ~21pt. A introdução (antes do 1º papel) vira o chunk de overview.

### Complicações (`tipo="complicacao"`)
Restrição/penalidade escolhida na criação (uma só) em troca de um poder geral extra. Duas
categorias: **Gerais** e **de Classe**. Âncoras: nome Tormenta20 ~16pt; categoria = cabeçalho
Tormenta20 ~21pt (**partido** em 2 spans: "Complicações" + "de Classe" → buffer `hdr21`); no
formato compacto (p289) a **classe** vem taggeada em Tormenta20 ~11pt após o nome (senão
derivada do nome/efeito contra os 14+1 nomes de classe). Flag **`voto`** (†): complicação de
código/voto — viola → perde todos os PM (o dagger U+2020 é removido do texto). Caixa capturada:
"Regra Opcional: Superação".

### Objetivos Heroicos (`tipo="objetivo_heroico"`)
Meta grandiosa; enquanto perseguida dá **Benefício** em cenas ligadas, **Penalidade** ao se
afastar, e **Conclusão** permanente ao alcançar. 7 objetivos (Desafio, Descoberta, Liderança,
Obra, Riqueza, Salvação, Vingança). Âncora: nome Tormenta20 ~16pt; campos = rótulos negrito
"Benefício.", "Penalidade.", "Conclusão."; descrição = corpo antes do 1º rótulo. A legenda
geral dos campos (antes do 1º objetivo) e os 4 cabeçalhos 21pt vão para o overview. Caixa:
"Abandonando um Objetivo". **Foi aqui que a detecção de caixas nasceu** (Riqueza perdia os
campos p/ a sidebar no topo da col1).

### Idades Variadas (`tipo="faixa_etaria"` + `tipo="mazela_idade"`)
Três grupos: **7 faixas etárias** (Criança…Ancião) com nome (21pt) + intervalo de idade (16pt,
casa "\d+ a \d+ anos"/"\d+\+ anos") + **modificadores** de atributo (parseados do corpo) +
**traços** nomeados (rótulos negrito); **19 mazelas** de "O Peso da Idade" (nome 16pt + efeito).
Chaveamento de modo: "O Peso da Idade" (21pt) faixas→mazelas; "Envelhecendo" (27pt) → epílogo.
Caixas: Tabela 4-2 (redundante c/ as faixas → **não** vira chunk) e a sidebar "Idades das
Raças". O overview inclui a regra de "O Peso da Idade" (adultos+ escolhem N complicações de
idade por faixa: 1 adulto, 2 maduro, 3 velho, 4 ancião).

### Combate Avançado (`tipo="regra_opcional"` subtipo `combate_avancado` + `tabela`)
~18 REGRAS opcionais de combate (Ações Rápidas, Ataques de Oportunidade, Ataques Mirados,
Cobertura Leve, Defesa Épica, Efeitos Críticos, Falhas Críticas, Lesões, Posicionamento, RD
Combinada, …), cada uma um módulo (nome Tormenta20 ~21pt — às vezes PARTIDO em 2 spans → buffer
`hdr21`; corpo IowanOldStyle) + as **3 tabelas**: Acertos Críticos, Teste de Morte, Falhas
Críticas. **Parser de tabela numerada REUSÁVEL:** o número d%/d10 fica numa sub-coluna estreita,
**centrado no bloco do efeito** (por isso o `find_tables` desalinha ímpar/par) → reconstrução por
**MIDPOINT** entre números consecutivos (cada linha de efeito cai na faixa vertical do número mais
próximo); chave textual (Teste de Morte) via split no maior gap de x. Falhas (99 linhas) e Teste
de Morte (4) saem limpas; Acertos Críticos (55) é matriz de severidade multi-coluna (flatten
best-effort, legível).

### Domínios (`tipo="regra_opcional"` subtipo `dominios` + `construcao_dominio` + `tabela`)
Subsistema de regência. **23 módulos procedurais** (Tornando-se Regente +Criando/Conquistando;
Características: Níveis/Terreno/Corte/Popularidade/Fortificações; Turnos de Domínio Etapas 1–3;
Domínios Místicos; Eventos Aleatórios: Resolvendo/Batalhas/Revoltas) + **80 Construções**
(`construcao_dominio`: nome = rótulo negrito terminando em "." + descrição/efeito; lista A→Z) +
a **Tabela 4-11 de Unidades Militares** (6 tropas). Máquina de estados dirigida por cabeçalhos
Tormenta20 (**27/21/16pt** — cuidado: 27pt é cabeçalho de seção, NÃO splash; splash/drop-cap só
≥40pt) com buffer flush-no-corpo (separa título partido de seções distintas). A tabela de unidades
(8 colunas) é reconstruída por **GEOMETRIA** (colunas por x do cabeçalho + linhas por banda-y),
resolvendo o merge ímpar/par do `find_tables`.

## 2. Integração (`integrar_regras_opcionais_herois.py`)

Aditivo, `fonte="herois-arton"`, `capitulo="regras-opcionais"`, **idempotência estreita**
(remove só chunks desse capítulo; recomputa `meta["fontes"]`; embute só os vetores novos).
**237 chunks:** 6 overviews + 9 papéis + 54 complicações + 7 objetivos + 7 faixas + 19 mazelas
+ 18 regras de combate + 23 módulos de domínio + 80 construções + 4 tabelas + 3 caixas + 6 listas
+ 1 backlog. Metadados por chunk (`categoria`/`classe`/`voto`, `modificadores`, `idade`, `subtipo`)
ficam filtráveis mesmo sem `detectar_filtro_*` dedicado (a busca vetorial já resolve — ver §3).

Índice: **2959 → 3067 → 3196 chunks** (`nucleo` 1498 + `ameacas-arton` 377 + `herois-arton` 1321).
`herois-arton`: Cap1 664 + Arsenal 205 + Distinções 215 + **Regras Opcionais 237**.

Uso:
```
python extrair_papeis_herois.py && python gerar_papeis_herois_html.py
python extrair_complicacoes_herois.py && python gerar_complicacoes_herois_html.py
python extrair_objetivos_herois.py && python gerar_objetivos_herois_html.py
python extrair_idades_herois.py && python gerar_idades_herois_html.py
python extrair_combate_avancado_herois.py && python gerar_combate_avancado_herois_html.py
python extrair_dominios_herois.py && python gerar_dominios_herois_html.py
python integrar_regras_opcionais_herois.py
```

Efeito medido (recuperação vetorial pura, top-1): "papel de xerife" → Xerife rank 1;
"preparação litúrgica do clérigo" → rank 1 c/ classe; "modificadores de criança" → faixa rank 1;
"objetivos heroicos" → overview rank 1; "ataques de oportunidade" → Combate Avançado rank 1;
"tornar-se regente" → Domínios rank 1 (0,77); "construção biblioteca" → rank 1; "tabela de falhas
críticas" → rank 1.

## 3. BACKLOG (não integrado) — restante do Cap. 4

Há um chunk `tipo="pendencia"` no índice registrando o que falta. Já foram integrados: as listas
entity-like, **Combate Avançado** (18 regras + 3 tabelas) e o subsistema **Domínios** (23 módulos +
80 construções + unidades). Ainda NÃO integrados (menor prioridade):

- **Regras Mais Soltas** (282–283): Atributos Variados, Raças Abertas, Devoções Abertas.
- **Culinária Avançada** (307–311): Fabricando Pratos Especiais, Ingredientes, Novos Poderes.
- **Exploração de Masmorras** (312–315): encontros/luz/ruído/recursos/sobrevivência.
- **Tabelas-resumo de custo de Domínios**: Terrenos (Tabela 4-9), Construções (4-10) e Eventos
  Aleatórios (4-13) — numéricas multi-coluna, precisam do mesmo refino que a Acertos Críticos.

**Próximo passo natural:** os 3 módulos procedurais menores (Regras Mais Soltas, Culinária,
Exploração) — cada regra = 1 chunk `tipo="regra_opcional"`, reusando a máquina deste extrator.
