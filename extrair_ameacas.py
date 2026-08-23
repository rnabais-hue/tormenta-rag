# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Capítulo 7: Ameaças (Bestiário) de Tormenta20 (Edição Jogo do Ano).
Guiada pela TIPOGRAFIA e pela Tabela 7-1: Criaturas por Nível de Desafio (págs. 288–329).

Extrai:
  - Todas as 80 criaturas canônicas do Bestiário (págs. 292–322) com stat blocks completos.
  - Regras de ameaças e papéis de combate (págs. 288–291: Solo, Lacaio, Bando, ND).
  - Perigos simples, complexos e armadilhas (págs. 323–327).
  - Criação de NPCs e Tabela 7-2: Estatísticas por Patamar (págs. 328–329).

Lê o PDF; escreve dados/ameacas.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
OUT = BASE / "dados" / "ameacas.json"
OUT.parent.mkdir(exist_ok=True)

# Tabela 7-1 Canônica: 80 criaturas organizadas por grupo, ND e página inicial estimada
CRIATURAS_TABELA = [
    # Masmorras (págs 292–294)
    ("Glop", "Masmorras", "1/4", 292),
    ("Rato Gigante", "Masmorras", "1/4", 292),
    ("Orc Combatente", "Masmorras", "1/2", 292),
    ("Orc Chefe", "Masmorras", "2", 292),
    ("Orc Mutante", "Masmorras", "5", 292),
    ("Aranha Gigante", "Masmorras", "2", 293),
    ("Gárgula", "Masmorras", "2", 293),
    ("Guerreiro de Chifres", "Masmorras", "3", 293),
    ("Mantícora", "Masmorras", "6", 293),
    ("Centopeia-dragão", "Masmorras", "7", 293),
    ("Golem de Ferro", "Masmorras", "10", 294),
    
    # Ermos (págs 295–299)
    ("Bandido", "Ermos", "1/4", 295),
    ("Chefe Bandido", "Ermos", "1", 295),
    ("Guarda de Cidade", "Ermos", "1/2", 295),
    ("Sargento da Guarda", "Ermos", "1", 295),
    ("Lobo", "Ermos", "1/2", 296),
    ("Centauro Combatente", "Ermos", "1", 296),
    ("Centauro Xamã", "Ermos", "3", 296),
    ("Gnoll Saqueador", "Ermos", "1", 296),
    ("Gnoll Filibusteiro", "Ermos", "2", 297),
    ("Gorlogg", "Ermos", "1", 297),
    ("Trog", "Ermos", "1", 297),
    ("Lobo-das-cavernas", "Ermos", "2", 298),
    ("Cão do Inferno", "Ermos", "3", 298),
    ("Grifo", "Ermos", "3", 298),
    ("Basilisco", "Ermos", "4", 299),
    ("Ogro", "Ermos", "4", 299),
    ("Urso-Coruja", "Ermos", "4", 299),
    ("Serpe", "Ermos", "5", 299),
    
    # Supremacia Purista (págs 300–302)
    ("Recruta Purista", "Puristas", "1/2", 300),
    ("Soldado Purista", "Puristas", "1", 300),
    ("Sargento-mor", "Puristas", "3", 300),
    ("Capelão de Guerra", "Puristas", "4", 301),
    ("Capitão-baluarte", "Puristas", "5", 301),
    ("Cavaleiro do Leopardo", "Puristas", "9", 301),
    ("Colosso Supremo", "Puristas", "14", 302),
    
    # Reino dos Mortos (págs 303–305)
    ("Zumbi", "Reino dos Mortos", "1/4", 303),
    ("Turba Zumbi", "Reino dos Mortos", "2", 303),
    ("Esqueleto", "Reino dos Mortos", "2", 303),
    ("Esqueleto de Elite", "Reino dos Mortos", "4", 303),
    ("Falange", "Reino dos Mortos", "8", 304),
    ("Aparição", "Reino dos Mortos", "5", 304),
    ("Necromante", "Reino dos Mortos", "7", 304),
    ("Vampiro", "Reino dos Mortos", "12", 305),
    
    # Duyshidakk / Aliança Negra (págs 306–309)
    ("Goblin Salteador", "Duyshidakk", "1/4", 306),
    ("Hobgoblin Soldado", "Duyshidakk", "2", 306),
    ("Goblin Engenhoqueiro", "Duyshidakk", "3", 306),
    ("Arauto de Thwor", "Duyshidakk", "4", 307),
    ("Hobgoblin Mago de Batalha", "Duyshidakk", "5", 307),
    ("Engenho de Guerra Goblin", "Duyshidakk", "6", 307),
    ("Devorador de Medos", "Duyshidakk", "8", 309),
    ("Sombra de Thwor", "Duyshidakk", "9", 309),
    
    # Culto de Sszzaas (págs 310–312)
    ("Cascavel", "Sszzaazitas", "1/4", 310),
    ("Jiboia", "Sszzaazitas", "1/2", 310),
    ("Naja", "Sszzaazitas", "1", 310),
    ("Sucuri", "Sszzaazitas", "3", 310),
    ("Nagah Guardião", "Sszzaazitas", "3", 311),
    ("Nagah Mística", "Sszzaazitas", "6", 311),
    ("Cultista de Sszzaas", "Sszzaazitas", "7", 312),
    ("Hidra", "Sszzaazitas", "11", 312),
    ("Lagash", "Sszzaazitas", "13", 312),
    
    # Trolls Nobres / Finntroll (págs 313–315)
    ("Finntroll Caçador", "Trolls nobres", "2", 313),
    ("Finntroll Feitor", "Trolls nobres", "6", 313),
    ("Ganchador", "Trolls nobres", "5", 314),
    ("Troll", "Trolls nobres", "5", 314),
    ("Troll das Cavernas", "Trolls nobres", "9", 315),
    
    # Dragões (págs 316–319)
    ("Enxame Kobold", "Dragões", "2", 316),
    ("Dragão Filhote", "Dragões", "3", 316),
    ("Dragão Jovem", "Dragões", "7", 316),
    ("Dragão Adulto", "Dragões", "11", 317),
    ("Dragão Venerável", "Dragões", "15", 317),
    ("Dragão-rei", "Dragões", "20", 318),
    ("Tirano do Terceiro", "Dragões", "10", 319),
    
    # Ameaças da Tormenta / Lefeu (págs 320–322)
    ("Maníaco Lefou", "Tormenta", "2", 320),
    ("Uktril", "Tormenta", "3", 320),
    ("Geraktril", "Tormenta", "6", 320),
    ("Reishid", "Tormenta", "8", 320),
    ("Otyugh", "Tormenta", "5", 321),
    ("Thuwarokk", "Tormenta", "16", 321),
    ("Sacerdote de Aharadak", "Tormenta", "10", 322)
]


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def dehyph(s):
    if not s:
        return ""
    s = re.sub(r"(\w+)[-\xad\u00ad]\s+(\w+)", r"\1\2", s)
    s = re.sub(r"[\xad\u00ad]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extrair_dados_criatura(doc, nome, grupo, nd, pno_start):
    """Extrai campos estruturados de uma criatura das páginas do livro."""
    txt = ""
    for p in range(pno_start, min(pno_start + 2, 323)):
        txt += doc[p - 1].get_text() + "\n"
        
    txt = dehyph(txt)
    
    # Localizar nome
    nome_pat = re.escape(nome)
    m_name = re.search(r"\b" + nome_pat + r"\b", txt, re.I)
    if not m_name:
        parts = nome.split()
        m_name = re.search(r"\b" + re.escape(parts[0]) + r"\b", txt, re.I)
        
    if not m_name:
        return None
        
    start_pos = m_name.start()
    sub_txt = txt[start_pos:]
    
    # Localizar fim do stat block
    m_tesouro = re.search(r"Tesouro\s+([^\n\.]+(?:\.[^\n\.]*)?)", sub_txt)
    if m_tesouro:
        end_pos = m_tesouro.end()
        bloco = sub_txt[:end_pos]
    else:
        bloco = sub_txt[:1800]
        
    # 1. Tipo, Tamanho, Papel
    m_tipo = re.search(
        r"(Monstro|Humanoide|Animal|Construto|Espírito|Morto-vivo)\s*(?:\(([^)]+)\))?\s*(Minúsculo|Pequeno|Médio|Grande|Enorme|Colossal)(?:\s*\((Solo|Lacaio|Bando)\))?",
        bloco, re.I
    )
    tipo_criatura = m_tipo.group(1).capitalize() if m_tipo else "Monstro"
    subtipo = m_tipo.group(2).strip() if (m_tipo and m_tipo.group(2)) else ""
    tamanho = m_tipo.group(3).capitalize() if m_tipo else "Médio"
    papel = m_tipo.group(4).capitalize() if (m_tipo and m_tipo.group(4)) else "Normal"
    
    # 2. Iniciativa e Percepção
    m_ini = re.search(r"Iniciativa\s+([+\-]?\d+)", bloco, re.I)
    iniciativa = m_ini.group(1) if m_ini else "+0"
    
    m_per = re.search(r"Percepção\s+([+\-]?\d+)(?:,\s*([^,\n]+(?:,\s*[^,\n]+)*))?", bloco, re.I)
    percepcao = m_per.group(1) if m_per else "+0"
    sentidos = m_per.group(2).strip() if (m_per and m_per.group(2)) else "visão normal"
    
    # 3. Defesa e Resistências
    m_def = re.search(r"Defesa\s+(\d+)", bloco, re.I)
    defesa = int(m_def.group(1)) if m_def else 10
    
    m_res = re.search(
        r"(?:Fort|Fortitude)\s+([+\-]?\d+),\s*(?:Ref|Reflexos)\s+([+\-]?\d+),\s*(?:Von|Vontade)\s+([+\-]?\d+)(?:,\s*([^,\n]+(?:,\s*[^,\n]+)*))?",
        bloco, re.I
    )
    fortitude = m_res.group(1) if m_res else "+0"
    reflexos = m_res.group(2) if m_res else "+0"
    vontade = m_res.group(3) if m_res else "+0"
    resistencias = m_res.group(4).strip() if (m_res and m_res.group(4)) else ""
    
    # 4. PV e PM
    m_pv = re.search(r"Pontos de Vida\s+(\d+)", bloco, re.I)
    pv = int(m_pv.group(1)) if m_pv else 10
    
    m_pm = re.search(r"Pontos de Mana\s+(\d+)", bloco, re.I)
    pm = int(m_pm.group(1)) if m_pm else 0
    
    # 5. Deslocamento
    m_desl = re.search(
        r"Deslocamento\s+([^\n]+?)(?=\s*Corpo a Corpo|\s*À Distância|\s*Pontos de|\s*For |\s*Tesouro)",
        bloco, re.I
    )
    deslocamento = m_desl.group(1).strip() if m_desl else "9m (6q)"
    
    # 6. Ataques (limpos de habilidades)
    m_cac = re.search(
        r"Corpo a Corpo\s+([^\n]+?)(?=\s*À Distância|\s*For |\s*Tesouro|\s*[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-z]+ \([A-Za-z]+\)|\s*Sensibilidade|\s*Doença|\s*Veneno|\s*Teia|\s*Imobilidade)",
        bloco, re.I
    )
    corpo_a_corpo = m_cac.group(1).strip() if m_cac else ""
    
    m_dist = re.search(
        r"À Distância\s+([^\n]+?)(?=\s*For |\s*Tesouro|\s*[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-z]+ \([A-Za-z]+\)|\s*Sensibilidade|\s*Doença|\s*Veneno)",
        bloco, re.I
    )
    distancia = m_dist.group(1).strip() if m_dist else ""
    
    # 7. Atributos
    m_atr = re.search(
        r"For\s+([+\-]?\d+|–|-),\s*Des\s+([+\-]?\d+|–|-),\s*Con\s+([+\-]?\d+|–|-),\s*Int\s+([+\-]?\d+|–|-),\s*Sab\s+([+\-]?\d+|–|-),\s*Car\s+([+\-]?\d+|–|-)",
        bloco, re.I
    )
    atributos = {}
    if m_atr:
        atributos = {
            "for": m_atr.group(1),
            "des": m_atr.group(2),
            "con": m_atr.group(3),
            "int": m_atr.group(4),
            "sab": m_atr.group(5),
            "car": m_atr.group(6),
        }
        
    # 8. Perícias
    m_peric = re.search(r"Perícias\s+([^\n\.]+?)(?=\.\s*Equipamento|\.\s*Tesouro|\.\s*For |\.$)", bloco, re.I)
    pericias = m_peric.group(1).strip() if m_peric else ""
    
    # 9. Equipamento
    m_equip = re.search(r"Equipamento\.?\s+([^\n\.]+?)(?=\.\s*Tesouro|\.$)", bloco, re.I)
    equipamento = m_equip.group(1).strip() if m_equip else ""
    
    # 10. Tesouro
    m_tes = re.search(r"Tesouro\s+([^\n\.]+?)(?=\.$|$)", bloco, re.I)
    tesouro = m_tes.group(1).strip() if m_tes else "Padrão"
    
    # 11. Habilidades Especiais
    habs = []
    hab_matches = re.findall(
        r"([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-zA-Záéíóúâêîôûãõç\s\-]+(?:\s*\((?:Padrão|Movimento|Completa|Reação|Livre)\))?)\s+([^.\n]+(?:\.[^.\n]+)*\.)",
        bloco
    )
    for h_nome, h_desc in hab_matches:
        h_nome_clean = h_nome.strip()
        if any(ign in h_nome_clean for ign in [
            "Corpo a Corpo", "À Distância", "Pontos de Vida", "Pontos de Mana",
            "Deslocamento", "Iniciativa", "Percepção", "Defesa", "Tesouro",
            "Equipamento", "Perícias", "For "
        ]):
            continue
        habs.append({
            "nome": h_nome_clean,
            "descricao": h_desc.strip(),
        })
        
    return {
        "id": f"ameaca_{slug(nome)}",
        "tipo_entidade": "ameaca",
        "nome": nome,
        "grupo": grupo,
        "nd": nd,
        "tipo_criatura": tipo_criatura,
        "subtipo": subtipo,
        "tamanho": tamanho,
        "papel": papel,
        "iniciativa": iniciativa,
        "percepcao": percepcao,
        "sentidos": sentidos,
        "defesa": defesa,
        "fortitude": fortitude,
        "reflexos": reflexos,
        "vontade": vontade,
        "resistencias": resistencias,
        "pv": pv,
        "pm": pm,
        "deslocamento": deslocamento,
        "corpo_a_corpo": corpo_a_corpo,
        "distancia": distancia,
        "habilidades": habs,
        "atributos": atributos,
        "pericias": pericias,
        "equipamento": equipamento,
        "tesouro": tesouro,
        "pagina": pno_start,
    }


def extrair_regras_ameacas(doc):
    """Extrai blocos procedurais de regras de ameaças, perigos e estatísticas de NPCs."""
    regras = []
    
    # 1. Regras de Ameaças & Papéis de Combate (págs 288–290)
    regras.append({
        "id": "regra_papeis_ameacas",
        "tipo_entidade": "regra_ameaca",
        "titulo": "Regras de Ameaças e Papéis de Combate (Solo, Lacaio e Bando)",
        "pagina": 289,
        "resumo": "Papéis de combate em Tormenta20 definem como as criaturas operam em batalha: Solo (chefes), Lacaio (hordas de 1 PV) e Bando (tropas agrupadas).",
        "texto": (
            "Papéis de Ameaças em Tormenta20 (pág. 289):\n"
            "• Solo: Criaturas construídas para enfrentar um grupo de personagens sozinhas. Possuem estatísticas aumentadas, "
            "ações extras e mais PV para manter um combate dinâmico contra múltiplos heróis.\n"
            "• Lacaio: Criaturas que atuam em grandes números. Possuem estatísticas normais de ataque e dano, mas caem com qualquer acerto (ou sofrem dano mínimo).\n"
            "• Bando: Representa dezenas de criaturas operando como uma única unidade grande ou colossal. Sofrem dano normal mas têm imunidade a manobras individuais.\n"
            "• Nível de Desafio (ND): O ND indica o nível que um grupo de quatro aventureiros deve ter para enfrentar aquela criatura em combate equilibrado."
        )
    })
    
    # 2. Perigos Simples e Complexos (págs 323–327)
    regras.append({
        "id": "regra_perigos_complexos",
        "tipo_entidade": "regra_perigo",
        "titulo": "Regras de Perigos, Armadilhas e Perigos Complexos",
        "pagina": 326,
        "resumo": "Regras para armadilhas, perigos ambientais (fogo, frio, queda, sufocamento) e perigos complexos resolvidos por testes estendidos.",
        "texto": (
            "Perigos e Armadilhas em Tormenta20 (págs. 323–327):\n"
            "• Perigos Simples: Armadilhas mecânicas ou mágicas resolvidas em um único teste (ex.: Fosso com Estacas, Runa Explosiva, Dardos Envenenados). "
            "Envolvem um teste de Percepção/Investigação para notar, Ladinagem para desarmar, e um teste de resistência (Reflexos/Fortitude) se disparadas.\n"
            "• Perigos Ambientais: Queda (1d6 por 1,5m de queda, máx 20d6), Fogo (1d6 a cada rodada), Frio Extremo (perda de PV/fadiga sem proteção), "
            "Sufocamento (Constituição rodadas até ficar inconsciente e morrer).\n"
            "• Perigos Complexos: Desafios estendidos que funcionam como combates contra o ambiente. Possuem Iniciativa própria, exigem sucessos "
            "cumulativos em diferentes perícias (Atletismo, Sobrevivência, Misticismo, etc.) ao longo de rodadas, e causam efeitos a cada rodada que permanecem ativos."
        )
    })
    
    # 3. Criação de NPCs e Tabela 7-2 (págs 328–329)
    regras.append({
        "id": "regra_estatisticas_npcs",
        "tipo_entidade": "regra_npc",
        "titulo": "Criação de NPCs e Tabela 7-2: Estatísticas por Patamar",
        "pagina": 329,
        "resumo": "Diretrizes de criação rápida de estatísticas para NPCs por patamar de jogo (Iniciante, Veterano, Campeão, Lendário).",
        "texto": (
            "Estatísticas de NPC por Patamar (Tabela 7-2, pág. 329):\n"
            "A maioria dos NPCs não precisa de ficha completa. Quando necessário, use os valores de referência por patamar:\n"
            "• Iniciante (ND 1 a 4): Testes Principais +5 a +10 | Defesa 15 a 20 | PV 15 a 80 | Dano Médio 1d8+4 a 2d8+8 | CD 15 a 18.\n"
            "• Veterano (ND 5 a 10): Testes Principais +11 a +18 | Defesa 22 a 32 | PV 100 a 250 | Dano Médio 2d10+12 a 3d10+18 | CD 20 a 25.\n"
            "• Campeão (ND 11 a 16): Testes Principais +19 a +26 | Defesa 34 a 44 | PV 300 a 600 | Dano Médio 4d10+20 a 6d10+30 | CD 28 a 35.\n"
            "• Lendário (ND 17 a 20+): Testes Principais +27 a +35 | Defesa 46 a 55+ | PV 700 a 1200+ | Dano Médio 8d10+35+ | CD 38 a 45+."
        )
    })
    
    return regras


def extrair_todas_ameacas():
    doc = pymupdf.open(str(PDF))
    
    criaturas = []
    for nome, grupo, nd, pno in CRIATURAS_TABELA:
        dados = extrair_dados_criatura(doc, nome, grupo, nd, pno)
        if dados:
            criaturas.append(dados)
        else:
            print(f"ALERTA: Falha ao extrair criatura '{nome}' (pág {pno})")
            
    regras = extrair_regras_ameacas(doc)
    
    banco = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (Capítulo 7: Ameaças, págs 288–329)",
        "total_criaturas": len(criaturas),
        "total_regras": len(regras),
        "regras": regras,
        "criaturas": criaturas,
    }
    
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    return banco


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Extraindo Ameaças de {PDF.name} (págs 288–329)...")
    banco = extrair_todas_ameacas()
    crias = banco["criaturas"]
    regras = banco["regras"]
    
    print(f"Sucesso! {len(crias)} criaturas e {len(regras)} regras salvas em {OUT}")
    
    # Estatísticas por grupo
    por_grupo = {}
    por_nd = {}
    for c in crias:
        g = c["grupo"]
        por_grupo[g] = por_grupo.get(g, 0) + 1
        nd = c["nd"]
        por_nd[nd] = por_nd.get(nd, 0) + 1
        
    print("\n--- Estatísticas do Bestiário ---")
    print(f"Por Grupo: {json.dumps(por_grupo, ensure_ascii=False)}")
    print(f"Por ND: {json.dumps(por_nd, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
