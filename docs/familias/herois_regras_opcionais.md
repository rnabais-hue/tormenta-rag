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

## 2. Integração (`integrar_regras_opcionais_herois.py`)

Aditivo, `fonte="herois-arton"`, `capitulo="regras-opcionais"`, **idempotência estreita**
(remove só chunks desse capítulo; recomputa `meta["fontes"]`; embute só os vetores novos).
**108 chunks:** 4 overviews + 9 papéis + 54 complicações + 7 objetivos + 7 faixas + 19 mazelas
+ 3 caixas + 4 listas + 1 backlog. Metadados por chunk (`categoria`/`classe`/`voto`,
`modificadores`, `idade`) ficam filtráveis mesmo sem `detectar_filtro_*` dedicado (a busca
vetorial já resolve — ver §3).

Índice: **2959 → 3067 chunks** (`nucleo` 1498 + `ameacas-arton` 377 + `herois-arton` 1192).
`herois-arton`: Cap1 664 + Arsenal 205 + Distinções 215 + **Regras Opcionais 108**.

Uso:
```
python extrair_papeis_herois.py && python gerar_papeis_herois_html.py
python extrair_complicacoes_herois.py && python gerar_complicacoes_herois_html.py
python extrair_objetivos_herois.py && python gerar_objetivos_herois_html.py
python extrair_idades_herois.py && python gerar_idades_herois_html.py
python integrar_regras_opcionais_herois.py
```

Efeito medido (recuperação vetorial pura, top-1/top-3): "papel de xerife" → Xerife rank 1;
"preparação litúrgica do clérigo" → rank 1 c/ classe; "modificadores de criança" → faixa rank 1;
"mazelas de ancião" → lista + mazelas no topo; "objetivos heroicos" → overview rank 1.

## 3. BACKLOG (não integrado) — módulos procedurais do Cap. 4

Há um chunk `tipo="pendencia"` no índice registrando o que falta. São os **módulos de regra
procedurais** (natureza `regras_jogo`, não entity-list):

- **Regras Mais Soltas** (282–283): Atributos Variados, Raças Abertas, Devoções Abertas.
- **Combate Avançado** (298–306): dezenas de regras opcionais de combate + as **tabelas** de
  Acertos Críticos (300), Teste de Morte (302), Falhas Críticas (304).
- **Culinária Avançada** (307–311): Fabricando Pratos Especiais, Ingredientes, Novos Poderes.
- **Exploração de Masmorras** (312–315): encontros/luz/ruído/recursos/sobrevivência.
- **Domínios** (316–329): subsistema de regência — Tornando-se Regente, Características (Terreno/
  Corte/Popularidade/Fortificações), **Construções** (318, entity-like), **Unidades Militares**
  (324, entity-like), Turnos de Domínio, Domínios Místicos, Eventos Aleatórios. É o maior bloco.
- **Lista de Regras Opcionais / Estilos de Jogo** (330): índice-resumo do capítulo.

**Próximo passo natural:** modelar Domínios (Construções + Unidades como entidades; regência
como regras procedurais) e Combate Avançado (cada regra opcional = 1 chunk `tipo="regra_opcional"`).
Reusar a máquina de caixas para as tabelas de crítico/morte/falha.
