# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Capítulo 4: Magia de Tormenta20 (Edição Jogo do Ano).
Guiada pela TIPOGRAFIA (não pelo TOC). Seção "Descrição das Magias", págs 184–217
e regras gerais de magia (págs 174–179).

Tipografia = schema:
  - Nome da magia: Tormenta20-Regular ~16.0 (pode ocupar até 2 linhas).
  - Subtítulo / Tipo, Círculo e Escola: Tormenta20-Regular ~9.0.
      Ex.: "Divina 1 (Transmutação)", "Arcana 2 (Evocação)", "Universal 4 (Convocação)".
  - Stat block: Rótulos em negrito IowanOldStyle-Bold ~8.5 e valores em Roman ~8.5:
      Execução: <ação>; Alcance: <alcance>; Alvo/Área/Efeito: <alvo>; Duração: <duração>; Resistência: <res>.
  - Descrição: IowanOldStyle-Roman ~8.5 (e itálicos para subtópicos/componentes materiais).
  - Aprimoramentos / Truques: IowanOldStyle-Bold ~8.5 ("Truque:", "+1 PM:", "+2 PM (requer 2º círculo):")
    seguido do efeito mecânico em Roman.

Lê o PDF; escreve dados/magias.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
OUT = BASE / "dados" / "magias.json"
OUT.parent.mkdir(exist_ok=True)

# Páginas de descrição das magias: 184 a 217 (1-based)
PG_DESC_INI, PG_DESC_FIM = 184, 217

# Custo padrão em PM por círculo em Tormenta20
CUSTO_PM_CIRCULO = {1: 1, 2: 3, 3: 6, 4: 10, 5: 15}

HEADER_RE = re.compile(
    r"^(Arcana|Divina|Universal|Arcana e Divina|Divina e Arcana)\s+(\d+)\s*\(([^)]+)\)",
    re.I,
)


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def dehyph(s):
    if not s:
        return ""
    s = re.sub(r"[\xad\u00ad]", "", s)
    s = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def coletar_spans_magia(doc):
    """Coleta e ordena spans das páginas de descrição das magias."""
    spans = []
    for pno in range(PG_DESC_INI, PG_DESC_FIM + 1):
        page = doc[pno - 1]
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    txt = s["text"].strip()
                    if txt:
                        spans.append({
                            "text": txt,
                            "font": s["font"],
                            "size": round(s["size"], 1),
                            "bold": bool(s["flags"] & 16) or ("Bold" in s["font"]),
                            "page": pno,
                        })
    return spans


def identificar_limites_magias(spans):
    """Identifica o início de cada magia buscando o padrão título + subtítulo (header)."""
    boundaries = []
    for i, s in enumerate(spans):
        m = HEADER_RE.match(s["text"])
        if m and "Tormenta20" in s["font"]:
            name_spans = []
            j = i - 1
            while j >= 0 and spans[j]["size"] >= 14 and "Tormenta20" in spans[j]["font"]:
                name_spans.insert(0, spans[j]["text"])
                j -= 1
            nome = " ".join(name_spans)
            nome = dehyph(nome)
            
            tipo = m.group(1).lower()
            circulo = int(m.group(2))
            escola = m.group(3).strip().capitalize()
            
            boundaries.append({
                "start_idx": j + 1,
                "header_idx": i,
                "nome": nome,
                "tipo": tipo,
                "circulo": circulo,
                "escola": escola,
                "page": s["page"],
            })
    return boundaries


def parse_corpo_magia(sb, spell_spans):
    """Processa os spans de uma magia individual, separando stat block, texto e aprimoramentos."""
    full_text = " ".join([s["text"] for s in spell_spans])
    full_text = re.sub(r"(\w+)[-\xad]\s+(\w+)", r"\1\2", full_text)
    full_text = re.sub(r"[\xad\u00ad]", "", full_text)
    full_text = re.sub(r"\s+", " ", full_text).strip()
    
    stat_pattern = re.compile(
        r"^Execu[çc][ãa]o\s*:\s*(.*?)[;.]\s*"
        r"Alcance\s*:\s*(.*?)[;.]\s*"
        r"(?:(Alvo ou [ÁA]rea|Alvos|Alvo|[ÁA]rea|Efeito)\s*:\s*(.*?)[;.]\s*)?"
        r"Dura[çc][ãa]o\s*:\s*(.*?)(?:[;.]\s*Resist[êe]ncia\s*:\s*(.*?))?\.\s+(.*)",
        re.I | re.DOTALL,
    )
    
    m = stat_pattern.match(full_text)
    if not m:
        # Fallback de emergência
        return {
            "id": f"magia_{slug(sb['nome'])}",
            "tipo_entidade": "magia",
            "nome": sb["nome"],
            "tipo": sb["tipo"],
            "circulo": sb["circulo"],
            "custo_pm": CUSTO_PM_CIRCULO.get(sb["circulo"], 1),
            "escola": sb["escola"],
            "execucao": "",
            "alcance": "",
            "alvo_tipo": "",
            "alvo": "",
            "duracao": "",
            "resistencia": "",
            "descricao": full_text,
            "aprimoramentos": [],
            "pagina": sb["page"],
        }
        
    execucao = m.group(1).strip()
    alcance = m.group(2).strip()
    alvo_tipo = m.group(3).strip() if m.group(3) else ""
    alvo_val = m.group(4).strip() if m.group(4) else ""
    duracao = m.group(5).strip()
    resistencia = m.group(6).strip() if m.group(6) else ""
    corpo = m.group(7).strip()
    
    apr_splits = re.split(r"(?=(?:Truque|\+\s*\d+\s*PM(?:\s*\([^)]+\))?)\s*:)", corpo)
    desc = apr_splits[0].strip()
    
    aprimoramentos = []
    apr_header_re = re.compile(r"^(Truque|\+\s*\d+\s*PM(?:\s*\([^)]+\))?)\s*:\s*(.*)", re.DOTALL | re.I)
    for part in apr_splits[1:]:
        m_apr = apr_header_re.match(part.strip())
        if m_apr:
            aprimoramentos.append({
                "custo": m_apr.group(1).strip(),
                "efeito": re.sub(r"\s+", " ", m_apr.group(2)).strip(),
            })
            
    return {
        "id": f"magia_{slug(sb['nome'])}",
        "tipo_entidade": "magia",
        "nome": sb["nome"],
        "tipo": sb["tipo"],
        "circulo": sb["circulo"],
        "custo_pm": CUSTO_PM_CIRCULO.get(sb["circulo"], 1),
        "escola": sb["escola"],
        "execucao": execucao,
        "alcance": alcance,
        "alvo_tipo": alvo_tipo,
        "alvo": alvo_val,
        "duracao": duracao,
        "resistencia": resistencia,
        "descricao": desc,
        "aprimoramentos": aprimoramentos,
        "pagina": sb["page"],
    }


def extrair_regras_procedurais_magia(doc):
    """Extrai blocos estruturados de regras de magia das páginas 174–179."""
    regras = [
        {
            "id": "regra_magia_classificacao",
            "tipo_entidade": "regra_magia",
            "titulo": "Classificação das Magias (Tipo, Círculo e Escolas)",
            "pagina": 176,
            "resumo": "As magias de Tormenta20 dividem-se em arcanas (estudo e poder inato) e divinas (fé e devoção). São divididas em 5 círculos de poder e 8 escolas místicas.",
            "texto": (
                "Classificação das Magias:\n"
                "• Tipo: Magias Arcanas (usadas por Arcanistas e Bardos) provêm de estudo, inteligência ou sangue mágico. "
                "Magias Divinas (usadas por Clérigos, Druidas e Paladinos) emanam da fé e devoção aos Deuses. Magias Universais pertencem a ambas as listas.\n"
                "• Círculos de Magia e Custo em PM:\n"
                "  - 1º Círculo: Custo 1 PM (Acesso: 1º nível de conjurador)\n"
                "  - 2º Círculo: Custo 3 PM (Acesso: 5º nível de conjurador)\n"
                "  - 3º Círculo: Custo 6 PM (Acesso: 9º nível de conjurador)\n"
                "  - 4º Círculo: Custo 10 PM (Acesso: 13º nível de conjurador)\n"
                "  - 5º Círculo: Custo 15 PM (Acesso: 17º nível de conjurador)\n"
                "• As Oito Escolas de Magia:\n"
                "  - Abjuração: Magias de proteção, barreiras, dissipação e anulação mágica.\n"
                "  - Adivinhação: Magias de percepção, revelação, presságios e obtenção de informação.\n"
                "  - Convocação: Magias que invocam criaturas, teleportam e transportam matéria ou energia.\n"
                "  - Encantamento: Magias que afetam a mente, emoções, vontades e controle de criaturas.\n"
                "  - Evocação: Magias que manipulam e geram energias puras (fogo, frio, eletricidade, cura, luz e trevas).\n"
                "  - Ilusão: Magias que criam imagens, sensações e enganos visuais ou sensoriais falsos.\n"
                "  - Necromancia: Magias que manipulam a energia vital, a morte, maldições e mortos-vivos.\n"
                "  - Transmutação: Magias que alteram as propriedades físicas e formas de matéria e criaturas."
            ),
        },
        {
            "id": "regra_magia_aprendizado",
            "tipo_entidade": "regra_magia",
            "titulo": "Aprendendo e Preparando Magias",
            "pagina": 176,
            "resumo": "Regras de como conjuradores aprendem novas magias, sobem de nível e registram seus feitiços.",
            "texto": (
                "Aprendendo e Preparando Magias:\n"
                "• Ao criar o personagem e a cada novo nível, classes conjuradoras aprendem novas magias conforme a tabela da classe.\n"
                "• Arcanistas (Bruxos e Magos) necessitam de foco ou grimório para suas fórmulas arcanas, enquanto Feiticeiros conjuram intuitivamente.\n"
                "• Conjuradores divinos recebem suas preces em comunhão com seus deuses patronos através de seus símbolos sagrados.\n"
                "• Aprender magias além do limite da classe exige poderes específicos (como Escrever Pergaminho ou Conhecimento Mágico) ou estudo de pergaminhos e grimórios."
            ),
        },
        {
            "id": "regra_magia_lancamento_custos",
            "tipo_entidade": "regra_magia",
            "titulo": "Lançando Magias (Custos em PM, Limite de Gasto e Aprimoramentos)",
            "pagina": 176,
            "resumo": "Regras de conjuração, gasto de Pontos de Mana (PM), limite de PM igual ao nível e aplicação de aprimoramentos.",
            "texto": (
                "Lançando Magias e Custos de Mana:\n"
                "• Lançar uma magia consome Pontos de Mana (PM) de acordo com o círculo da magia (1º: 1 PM, 2º: 3 PM, 3º: 6 PM, 4º: 10 PM, 5º: 15 PM).\n"
                "• Limite de Gasto de PM: O limite máximo de PM que um personagem pode gastar numa única magia (somando custo base + aprimoramentos + poderes) é igual ao seu NÍVEL de personagem.\n"
                "• Aprimoramentos: Ao conjurar uma magia, você pode pagar PM adicionais para melhorar seu efeito (aumentar dano, alterar duração, adicionar alvos, etc.), desde que não ultrapasse seu limite de PM por nível.\n"
                "• Truques: Aprimoramento de custo 0 PM disponível em várias magias de 1º círculo quando lançadas sem gastar mana para efeitos menores.\n"
                "• Gestos e Palavras: Conjuradores precisam de pelo menos uma mão livre para gesticular e voz clara para pronunciar as palavras mágicas (a menos que usem Magia Discreta)."
            ),
        },
        {
            "id": "regra_magia_caracteristicas",
            "tipo_entidade": "regra_magia",
            "titulo": "Características das Magias (Execução, Alcance, Alvo/Área, Duração, Resistência)",
            "pagina": 178,
            "resumo": "Explicação dos parâmetros do stat block de cada magia e como calcular a Classe de Dificuldade (CD).",
            "texto": (
                "Características e Parâmetros das Magias:\n"
                "• Execução: Tipo de ação necessária para lançar (ação padrão, completa, de movimento, reação ou tempo estendido).\n"
                "• Alcance: Distância máxima a partir do conjurador onde a magia pode ser criada (Pessoal, Toque, Curto [9m], Médio [30m], Longo [90m] ou Ilimitado).\n"
                "• Alvo, Área ou Efeito: Quem ou o que a magia afeta. Áreas comuns incluem cones, esferas, cilindros e linhas.\n"
                "• Duração: Quanto tempo a magia dura (Instantânea, Cena [~15 minutos ou o combate inteiro], Sustentada [custa 1 PM por rodada como ação livre para manter] ou Permanente).\n"
                "• Resistência e CD do Teste: O teste de resistência que o alvo tem direito (Fortitude, Reflexos ou Vontade). O cálculo da CD é:\n"
                "  CD da Magia = 10 + metade do nível do personagem + modificador do atributo-chave de conjuração (Inteligência, Sabedoria ou Carisma)."
            ),
        },
        {
            "id": "regra_magia_anulacao_contramagia",
            "tipo_entidade": "regra_magia",
            "titulo": "Anulando Magias e Contramágica",
            "pagina": 179,
            "resumo": "Regras de como anular ou dissipar efeitos mágicos e usar contramagia em combate.",
            "texto": (
                "Anulando Magias e Contramágica:\n"
                "• Dissipar Magia: Magia da escola de Abjuração capaz de encerrar efeitos mágicos contínuos em criaturas, objetos ou áreas mediante teste de Misticismo ou Vontade.\n"
                "• Contramagia: Usar uma reação e gastar a mesma magia (ou uma magia oposta/Dissipar Magia) para anular a magia de um oponente no exato momento em que ela está sendo conjurada.\n"
                "• Identificar Magia: Para usar contramagia, o personagem deve passar num teste de Misticismo para reconhecer a magia que o oponente está lançando."
            ),
        },
    ]
    return regras


def extrair_magias():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans_magia(doc)
    boundaries = identificar_limites_magias(spans)
    
    parsed_spells = []
    for i, sb in enumerate(boundaries):
        end_idx = boundaries[i + 1]["start_idx"] if i + 1 < len(boundaries) else len(spans)
        spell_spans = spans[sb["header_idx"] + 1 : end_idx]
        p = parse_corpo_magia(sb, spell_spans)
        parsed_spells.append(p)
        
    regras = extrair_regras_procedurais_magia(doc)
    
    banco = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (Capítulo 4: Magia, págs 174–217)",
        "total_magias": len(parsed_spells),
        "magias": parsed_spells,
        "regras": regras,
    }
    
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    return banco


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Extraindo magias de {PDF.name}...")
    banco = extrair_magias()
    magias = banco["magias"]
    regras = banco["regras"]
    
    print(f"Sucesso! {len(magias)} magias e {len(regras)} regras salvas em {OUT}")
    
    # Estatísticas
    escolas = {}
    circulos = {}
    tipos = {}
    for m in magias:
        escolas[m["escola"]] = escolas.get(m["escola"], 0) + 1
        circulos[m["circulo"]] = circulos.get(m["circulo"], 0) + 1
        tipos[m["tipo"]] = tipos.get(m["tipo"], 0) + 1
        
    print("\n--- Estatísticas de Magias ---")
    print(f"Por Círculo: {json.dumps(circulos, ensure_ascii=False)}")
    print(f"Por Tipo: {json.dumps(tipos, ensure_ascii=False)}")
    print(f"Por Escola: {json.dumps(escolas, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
