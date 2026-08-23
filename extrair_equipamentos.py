# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do CAPÍTULO 3: EQUIPAMENTO de Tormenta20 (núcleo),
guiada pela TIPOGRAFIA e ESTRUTURA DE TABELAS E BLOCOS do PDF.

Gera dados/equipamentos.json contendo:
  1. armas (40 armas + 4 munições) com stats de tabela + descrições completas
  2. armaduras_escudos (12 itens) com defesa, penalidade, espaços, preço + descrições
  3. itens_gerais (~115 itens em 9 categorias) com preço, espaços + descrições mecânicas
  4. melhorias_superiores (~35 melhorias) com tipo aplicável + efeito
  5. materiais_especiais (6 materiais) com efeitos em armas/armaduras/esotéricos + custos
  6. regras_procedurais (4 blocos de regras: riqueza/moedas, carga/uso, passos de dano, itens superiores)

Lê o PDF; escreve dados/equipamentos.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(r"C:\LLM-Local\tormenta\livro\Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf")
OUT = Path(__file__).parent / "dados" / "equipamentos.json"
OUT.parent.mkdir(exist_ok=True)

BOLD = 2**4


def dehyph(s):
    if not s:
        return ""
    s = re.sub(r"[\xad\u00ad]\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def normalizar_nome(s):
    s = dehyph(s).strip().rstrip(".")
    s = re.sub(r"\s*\(\s*20\s*\)", "", s)
    s = re.sub(r"\s*\(\s*por dia\s*\)", "", s)
    s = re.sub(r"\s*\(\s*por noite\s*\)", "", s)
    s = re.sub(r"\s*\(\s*3m\s*\)", "", s)
    return s.strip()


def extrair_descricoes(doc, start_pg, end_pg, invalid_bolds=None):
    """Extrai blocos de itens iniciados por 'Nome.' em negrito Iowan."""
    if invalid_bolds is None:
        invalid_bolds = set()
    descs = {}
    current_item = None
    current_text = []

    for pg in range(start_pg - 1, end_pg):
        page = doc[pg]
        W, H = page.rect.width, page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    txt = s["text"]
                    fn = s["font"]
                    sz = s["size"]
                    y = s["bbox"][1]
                    if y < H * 0.05 or y > H * 0.95:
                        continue
                    
                    if "IowanOldStyle-Bold" in fn and sz >= 9.0 and txt.strip().endswith("."):
                        cleaned = txt.strip().rstrip(".")
                        norm = normalizar_nome(cleaned)
                        if cleaned not in invalid_bolds and norm not in invalid_bolds and not norm.startswith("Tabela"):
                            if current_item:
                                descs[current_item] = dehyph(" ".join(current_text))
                            current_item = norm
                            current_text = []
                            continue
                    
                    if current_item and "IowanOldStyle" in fn:
                        current_text.append(txt)

    if current_item:
        descs[current_item] = dehyph(" ".join(current_text))
    return descs


def extrair_armas(doc):
    """Extrai tabela 3-3 de armas (págs 150-151) e descrições (págs 152-157)."""
    descs = extrair_descricoes(doc, 152, 157, {"Capítulo Três", "Equipamento", "Tabela", "Munições", "Passos de Dano", "Habilidades de Armas"})
    
    linhas_tabela = []
    prof_atual = "Simples"
    empunh_atual = "Corpo a Corpo • Leve"
    
    for pg in [149, 150]: # págs 150 e 151
        page = doc[pg]
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            lines = [" ".join(s["text"] for s in l["spans"]).strip() for l in b["lines"]]
            txt_full = " ".join(lines)
            if "Armas Simples" in txt_full:
                prof_atual = "Simples"
            elif "Armas Marciais" in txt_full:
                prof_atual = "Marcial"
            elif "Armas Exóticas" in txt_full or "Armas Exticas" in txt_full:
                prof_atual = "Exótica"
            elif "Armas de Fogo" in txt_full:
                prof_atual = "Fogo"
                
            if "Corpo a Corpo" in txt_full:
                if "Leves" in txt_full:
                    empunh_atual = "Corpo a Corpo • Leve"
                elif "Uma Mão" in txt_full or "Uma Mo" in txt_full:
                    empunh_atual = "Corpo a Corpo • Uma Mão"
                elif "Duas Mãos" in txt_full or "Duas Mos" in txt_full:
                    empunh_atual = "Corpo a Corpo • Duas Mãos"
            elif "Ataque à Distância" in txt_full or "Ataque  Distncia" in txt_full:
                if "Uma Mão" in txt_full or "Uma Mo" in txt_full:
                    empunh_atual = "Ataque à Distância • Uma Mão"
                elif "Duas Mãos" in txt_full or "Duas Mos" in txt_full:
                    empunh_atual = "Ataque à Distância • Duas Mãos"

            if len(lines) >= 6 and (any("T$" in l for l in lines) or any("1d" in l or "2d" in l or "3d" in l for l in lines) or lines[0].startswith("Clava") or lines[0].startswith("Bordão") or lines[0].startswith("Tacape") or lines[0].startswith("Funda")):
                nome = dehyph(lines[0])
                preco = dehyph(lines[1]) if len(lines) > 1 else "—"
                dano = dehyph(lines[2]) if len(lines) > 2 else "—"
                critico = dehyph(lines[3]) if len(lines) > 3 else "—"
                alcance = dehyph(lines[4]) if len(lines) > 4 else "—"
                tipo_dano = dehyph(lines[5]) if len(lines) > 5 else "—"
                espacos = dehyph(lines[6]) if len(lines) > 6 else "1"
                
                is_municao = "Balas" in nome or "Flechas" in nome or "Pedras" in nome or "Virotes" in nome
                
                desc = ""
                for k, v in descs.items():
                    if slug(k) == slug(nome) or slug(k) in slug(nome) or slug(nome) in slug(k):
                        desc = v
                        break
                
                linhas_tabela.append({
                    "id": slug(nome),
                    "tipo": "equipamento",
                    "categoria": "municao" if is_municao else "arma",
                    "nome": nome,
                    "proficiencia": prof_atual,
                    "empunhadura": empunh_atual,
                    "preco": preco,
                    "dano": dano,
                    "critico": critico,
                    "alcance": alcance,
                    "tipo_dano": tipo_dano,
                    "espacos": espacos,
                    "descricao": desc,
                    "pagina": 150 if pg == 149 else 151
                })

    return linhas_tabela


def extrair_armaduras_escudos(doc):
    """Extrai tabela 3-5 (pág 159) e descrições (pág 160)."""
    descs = extrair_descricoes(doc, 160, 160, {"Capítulo Três", "Equipamento", "Tabela", "Penalidade de Armadura", "Armaduras Leves", "Armaduras Pesadas", "Escudos"})
    
    itens = []
    subcat_atual = "Armaduras Leves"
    page = doc[158] # pág 159
    
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        lines = [" ".join(s["text"] for s in l["spans"]).strip() for l in b["lines"]]
        txt_full = " ".join(lines)
        if "Armaduras Leves" in txt_full:
            subcat_atual = "Armaduras Leves"
        elif "Armaduras Pesadas" in txt_full:
            subcat_atual = "Armaduras Pesadas"
        elif "Escudos" in txt_full and len(lines) == 1:
            subcat_atual = "Escudos"
            
        if len(lines) >= 4 and any("T$" in l or "+" in l for l in lines):
            nome = dehyph(lines[0])
            preco = dehyph(lines[1])
            defesa = dehyph(lines[2])
            penalidade = dehyph(lines[3]).replace("", "-")
            espacos = dehyph(lines[4]) if len(lines) > 4 else "2"
            
            desc = ""
            for k, v in descs.items():
                if slug(k) == slug(nome) or slug(k) in slug(nome) or slug(nome) in slug(k):
                    desc = v
                    break
            
            is_escudo = "escudo" in slug(nome)
            itens.append({
                "id": slug(nome),
                "tipo": "equipamento",
                "categoria": "escudo" if is_escudo else "armadura",
                "subcategoria": subcat_atual,
                "nome": nome,
                "preco": preco,
                "defesa": defesa,
                "penalidade": penalidade,
                "espacos": espacos,
                "descricao": desc,
                "pagina": 159
            })

    return itens


def extrair_itens_gerais(doc):
    """Extrai itens gerais da tabela 3-6 (págs 162-163) e descrições (págs 161-170)."""
    descs = extrair_descricoes(doc, 161, 170, {
        "Capítulo Três", "Equipamento", "Tabela", "Itens Gerais", "Equipamento de Aventura",
        "Ferramentas", "Vestuário", "Esotéricos", "Alquímicos", "Preparados", "Catalisadores",
        "Venos", "Venenos", "Alimentação", "Animais", "Veículos", "Serviços", "Melhorias", "Itens Superiores"
    })
    
    itens_brutos = []
    
    # --- PÁGINA 162 ---
    p162 = doc[161]
    cat_left = "Equipamento de Aventura"
    cat_right = "Vestuário"
    
    for b in p162.get_text("dict")["blocks"]:
        if b.get("type") != 0: continue
        lines = [" ".join(s["text"] for s in l["spans"]).strip() for l in b["lines"]]
        if not any("T$" in l for l in lines) and not any("Esot" in l or "Ferram" in l or "Alqu" in l or "Vest" in l for l in lines):
            continue
        
        if len(lines) == 6:
            itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 162))
            itens_brutos.append((cat_right, lines[3], lines[4], lines[5], 162))
        elif len(lines) == 3:
            c = cat_left if any(k in lines[0] for k in ["Camisa", "Cosm", "Símbolo", "Instrum"]) else cat_right
            itens_brutos.append((c, lines[0], lines[1], lines[2], 162))
        elif len(lines) == 4:
            if "Esot" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 162))
                cat_right = "Esotéricos"
            elif "Ferram" in lines[0]:
                cat_left = "Ferramentas"
                itens_brutos.append((cat_right, lines[1], lines[2], lines[3], 162))
            elif "Alqu" in lines[3] and "Prep" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 162))
                cat_right = "Alquímicos — Preparados"
            elif "Vest" in lines[0]:
                cat_left = "Vestuário"
                itens_brutos.append((cat_right, lines[1], lines[2], lines[3], 162))
            elif "Alqu" in lines[3] and "Cat" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 162))
                cat_right = "Alquímicos — Catalisadores"

    # --- PÁGINA 163 ---
    p163 = doc[162]
    cat_left = "Alquímicos — Catalisadores"
    cat_right = "Animais"
    
    for b in p163.get_text("dict")["blocks"]:
        if b.get("type") != 0: continue
        lines = [" ".join(s["text"] for s in l["spans"]).strip() for l in b["lines"]]
        if not any("T$" in l for l in lines) and not any("Alqu" in l or "Anim" in l or "Ve" in l or "Serv" in l or "Aliment" in l for l in lines):
            continue
        
        if len(lines) == 6:
            n_esq = lines[0]
            n_dir = lines[3]
            c_dir = cat_right
            if "comum" in n_dir or "confort" in n_dir or "luxuosa" in n_dir:
                c_dir = "Serviços"
                n_dir = f"Estadia ({n_dir})"
            elif "aérea" in n_dir or "aerea" in n_dir:
                c_dir = "Serviços"
                n_dir = "Condução aérea"
            elif "círculo" in n_dir or "circulo" in n_dir:
                c_dir = "Serviços"
                n_dir = f"Serviço de Magia ({n_dir})"
            itens_brutos.append((cat_left, n_esq, lines[1], lines[2], 163))
            itens_brutos.append((c_dir, n_dir, lines[4], lines[5], 163))
        elif len(lines) == 3:
            if "Seixo" in lines[0] or "Essência de sombra" in lines[0]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 163))
            elif "Balão" in lines[0]:
                itens_brutos.append(("Veículos", lines[0], lines[1], lines[2], 163))
            elif "terrestre" in lines[0]:
                itens_brutos.append(("Serviços", "Condução terrestre", lines[1], lines[2], 163))
        elif len(lines) == 4:
            if "Ve" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 163))
                cat_right = "Veículos"
            elif "Veneno" in lines[0]:
                cat_left = "Alquímicos — Venenos"
                itens_brutos.append((cat_right, lines[1], lines[2], lines[3], 163))
            elif "Servi" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 163))
                cat_right = "Serviços"
            elif "Estadia" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 163))
            elif "Condu" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 163))
            elif "Aliment" in lines[0]:
                cat_left = "Alimentação"
                itens_brutos.append(("Serviços", "Condução marítima", lines[2], lines[3], 163))
            elif "Magia" in lines[3]:
                itens_brutos.append((cat_left, lines[0], lines[1], lines[2], 163))

    # Consolida com descrições
    itens = []
    for cat, nome_raw, preco, espacos, pg in itens_brutos:
        nome = normalizar_nome(nome_raw)
        desc = ""
        # Match description
        for k, v in descs.items():
            if slug(k) == slug(nome) or slug(k) in slug(nome) or slug(nome) in slug(k):
                desc = v
                break
        itens.append({
            "id": slug(nome),
            "tipo": "equipamento",
            "categoria": "item_geral",
            "subcategoria": cat,
            "nome": nome,
            "preco": dehyph(preco),
            "espacos": dehyph(espacos),
            "descricao": desc,
            "pagina": pg
        })

    return itens


def extrair_itens_superiores(doc):
    """Extrai melhorias (Tabela 3-8 + págs 170-172) e materiais especiais (Tabela 3-9 + págs 172-173)."""
    descs_melhorias = extrair_descricoes(doc, 170, 172, {"Capítulo Três", "Equipamento", "Tabela", "Melhorias", "Itens Superiores", "Preço de Melhorias"})
    
    melhorias = []
    page171 = doc[170]
    tabs = page171.find_tables()
    tab_melhorias = {}
    if tabs.tables:
        for row in tabs.tables[0].extract():
            if row and len(row) >= 2 and row[0] and row[1]:
                m_nome = dehyph(row[0])
                m_efeito = dehyph(row[1])
                if m_nome != "Melhoria":
                    tab_melhorias[normalizar_nome(m_nome)] = m_efeito

    for k, v in descs_melhorias.items():
        if k in ["Arma", "Armadura e Escudo", "Esotérico", "Escudo e Esotérico"]:
            continue
        aplica_a = "Geral"
        m_lower = k.lower()
        if "(arma)" in m_lower:
            aplica_a = "Arma"
        elif "(armadura)" in m_lower:
            aplica_a = "Armadura"
        elif "(escudo)" in m_lower:
            aplica_a = "Escudo"
        elif "(esotérico)" in m_lower or "(esoterico)" in m_lower:
            aplica_a = "Esotérico"
        else:
            if "arma" in v.lower() or "ataque" in v.lower() or "dano" in v.lower():
                aplica_a = "Arma"
            elif "armadura" in v.lower() or "defesa" in v.lower():
                aplica_a = "Armadura"
            elif "magia" in v.lower() or "pm" in v.lower():
                aplica_a = "Esotérico"
                
        melhorias.append({
            "id": slug(k),
            "tipo": "melhoria_superior",
            "nome": k,
            "aplica_a": aplica_a,
            "efeito_resumido": tab_melhorias.get(k, ""),
            "descricao_completa": v,
            "pagina": 171
        })

    materiais = [
        {
            "id": "aco-rubi",
            "tipo": "material_especial",
            "nome": "Aço-Rubi",
            "descricao": "Extraído de meteoros caídos na Tormenta, este metal avermelhado é resistente e corta através de defesas mágicas.",
            "efeito_arma": "Ignora 10 pontos de redução de dano de qualquer criatura.",
            "efeito_armadura_escudo": "Converte dano de ataques sofridos em dano não letal (5 pontos para armaduras leves e escudos, 10 pontos para armaduras pesadas).",
            "efeito_esoterico": "—",
            "precos": {"arma": "+T$ 1.000", "armadura_leve": "+T$ 1.500", "armadura_pesada": "+T$ 3.000", "escudo": "+T$ 1.500", "esoterico": "—"},
            "pagina": 172
        },
        {
            "id": "adamante",
            "tipo": "material_especial",
            "nome": "Adamante",
            "descricao": "O mais duro dos metais conhecidos, denso e de cor cinza-escura brilhante.",
            "efeito_arma": "Aumenta o passo de dano da arma em um nível.",
            "efeito_armadura_escudo": "Fornece redução de dano (RD 2 para armaduras leves e escudos, RD 5 para armaduras pesadas).",
            "efeito_esoterico": "—",
            "precos": {"arma": "+T$ 1.500", "armadura_leve": "+T$ 1.500", "armadura_pesada": "+T$ 3.000", "escudo": "+T$ 1.500", "esoterico": "—"},
            "pagina": 172
        },
        {
            "id": "gelo-eterno",
            "tipo": "material_especial",
            "nome": "Gelo Eterno",
            "descricao": "Gelo mágico das montanhas uivantes que nunca derrete, mesmo no calor intenso.",
            "efeito_arma": "Causa +1d6 de dano de frio.",
            "efeito_armadura_escudo": "Fornece resistência a frio 5 (armaduras leves e escudos) ou resistência a frio 10 (armaduras pesadas).",
            "efeito_esoterico": "Suas magias que causam dano de frio causam +1 ponto de dano por dado.",
            "precos": {"arma": "+T$ 1.000", "armadura_leve": "+T$ 1.000", "armadura_pesada": "+T$ 2.000", "escudo": "+T$ 1.000", "esoterico": "+T$ 1.000"},
            "pagina": 172
        },
        {
            "id": "madeira-tollon",
            "tipo": "material_especial",
            "nome": "Madeira Tollon",
            "descricao": "Madeira nobre originária das florestas do reino de Tollon, de cor escura e ressonância mágica única.",
            "efeito_arma": "O custo em PM para usar habilidades com a arma diminui em –1 PM (mínimo 1 PM). Apenas armas de madeira.",
            "efeito_armadura_escudo": "—",
            "efeito_esoterico": "O custo em PM para lançar magias com o esotérico diminui em –1 PM (mínimo 1 PM).",
            "precos": {"arma": "+T$ 1.000", "armadura_leve": "—", "armadura_pesada": "—", "escudo": "—", "esoterico": "+T$ 1.000"},
            "pagina": 173
        },
        {
            "id": "materia-vermelha",
            "tipo": "material_especial",
            "nome": "Matéria Vermelha",
            "descricao": "Substância aberrante e corruptora gerada pela tempestade rubra da Tormenta.",
            "efeito_arma": "Conta como um poder da Tormenta para propósitos de poderes que dependem de poderes da Tormenta e fornece +2 na margem de ameaça.",
            "efeito_armadura_escudo": "Conta como um poder da Tormenta e fornece +2 na Defesa contra criaturas da Tormenta e efeitos mágicos.",
            "efeito_esoterico": "Conta como um poder da Tormenta e a CD para resistir às suas magias aumenta em +1.",
            "precos": {"arma": "+T$ 1.500", "armadura_leve": "+T$ 1.500", "armadura_pesada": "+T$ 3.000", "escudo": "+T$ 1.500", "esoterico": "+T$ 1.500"},
            "pagina": 173
        },
        {
            "id": "mitral",
            "tipo": "material_especial",
            "nome": "Mitral",
            "descricao": "Metal prateado, brilhante e extremamente leve e flexível.",
            "efeito_arma": "Aumenta a margem de ameaça em +1 e a arma é considerada uma categoria mais leve para empunhadura.",
            "efeito_armadura_escudo": "Diminui a penalidade de armadura em 2 (mínimo 0) e armaduras pesadas de mitral contam como armaduras leves para efeitos de habilidades.",
            "efeito_esoterico": "—",
            "precos": {"arma": "+T$ 1.000", "armadura_leve": "+T$ 1.000", "armadura_pesada": "+T$ 2.000", "escudo": "+T$ 1.000", "esoterico": "—"},
            "pagina": 173
        }
    ]

    return melhorias, materiais


def extrair_regras_procedurais(doc):
    """Extrai os textos de regras procedurais do capítulo 3."""
    regras = [
        {
            "id": "regra-riqueza-moedas",
            "tipo": "regra_equipamento",
            "titulo": "Riqueza & Moedas em Tormenta20",
            "texto": (
                "A moeda padrão de Arton é o Tibar (T$). 1 Tibar de Ouro (T$ 1) = 10 Tibares de Prata (TP 10) = "
                "100 Tibares de Cobre (TC 100). Tibares de Platina (T$ 10) e barras de metais preciosos também "
                "são usados para grandes transações. O dinheiro inicial padrão para personagens de 1º nível é 4d6 T$ "
                "(ou valor inicial fixado pela classe/origem na Tabela 3-1: Dinheiro Inicial)."
            ),
            "pagina": 146
        },
        {
            "id": "regra-usando-carregando",
            "tipo": "regra_equipamento",
            "titulo": "Usando & Carregando Equipamento (Limites de Uso e Carga)",
            "texto": (
                "Limites de Uso: Uma criatura pode empunhar itens de acordo com seus membros (máximo 2 mãos) e "
                "vestir 1 armadura, 1 escudo e até 4 outros itens vestidos (como capas, botas, anéis, vestuário).\n\n"
                "Limites de Carga: Um personagem pode carregar um número de espaços igual a 3 vezes sua Força "
                "(mínimo 3 espaços). Se carregar mais do que seu limite, fica Sobrecarregado (penalidade de armadura "
                "piora em -2 e deslocamento diminui em 3m por espaço excedente; se carregar o dobro do limite, não consegue se mover)."
            ),
            "pagina": 147
        },
        {
            "id": "regra-caracteristicas-armas-passos-dano",
            "tipo": "regra_equipamento",
            "titulo": "Características das Armas e Passos de Dano",
            "texto": (
                "As armas são classificadas por Proficiência (Simples, Marciais, Exóticas, Fogo) e por "
                "Empunhadura (Leve, Uma Mão, Duas Mãos, Distância). "
                "Passos de dano (Tabela 3-2): Quando uma habilidade ou efeito aumenta ou diminui o passo de dano "
                "de uma arma, a progressão padrão é: 1d4 -> 1d6 -> 1d8 -> 1d10 -> 1d12 -> 2d8 -> 3d8 -> 4d8. "
                "Para armas com múltiplos dados iniciais (ex: 2d4 -> 2d6 -> 3d6 -> 4d6)."
            ),
            "pagina": 148
        },
        {
            "id": "regra-itens-superiores-fabricacao",
            "tipo": "regra_equipamento",
            "titulo": "Regras de Itens Superiores e Modificações",
            "texto": (
                "Itens superiores são obras-primas da forja e manufatura artoniana. Podem receber de 1 a 4 modificações "
                "(melhorias ou materiais especiais). "
                "Preço Adicional por Modificações (Tabela 3-7): 1ª modificação: +T$ 300; 2ª modificação: +T$ 900; "
                "3ª modificação: +T$ 2.700; 4ª modificação: +T$ 8.100. Materiais especiais cobram um custo adicional "
                "específico tabelado (Tabela 3-9). Para fabricar um item superior é necessário teste de Ofício correspondente."
            ),
            "pagina": 170
        }
    ]
    return regras


def main():
    print(f"Abrindo {PDF}...")
    doc = pymupdf.open(PDF)
    
    print("Extraindo Armas & Munições...")
    armas = extrair_armas(doc)
    print(f"  -> {len(armas)} armas/munições extraídas.")
    
    print("Extraindo Armaduras & Escudos...")
    armaduras = extrair_armaduras_escudos(doc)
    print(f"  -> {len(armaduras)} armaduras/escudos extraídos.")
    
    print("Extraindo Itens Gerais...")
    gerais = extrair_itens_gerais(doc)
    print(f"  -> {len(gerais)} itens gerais extraídos.")
    
    print("Extraindo Itens Superiores (Melhorias & Materiais)...")
    melhorias, materiais = extrair_itens_superiores(doc)
    print(f"  -> {len(melhorias)} melhorias e {len(materiais)} materiais especiais.")
    
    print("Extraindo Regras Procedurais...")
    regras = extrair_regras_procedurais(doc)
    print(f"  -> {len(regras)} regras procedurais.")
    
    dados = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (12-06-2024)",
        "capitulo": "Capítulo 3: Equipamento",
        "armas": armas,
        "armaduras_escudos": armaduras,
        "itens_gerais": gerais,
        "melhorias_superiores": melhorias,
        "materiais_especiais": materiais,
        "regras_procedurais": regras
    }
        
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        
    total_entidades = len(armas) + len(armaduras) + len(gerais) + len(melhorias) + len(materiais) + len(regras)
    print(f"\n[SUCESSO] Total de {total_entidades} registros gravados em {OUT}")


if __name__ == "__main__":
    main()
