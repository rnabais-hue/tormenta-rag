# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Apêndice: Lista de Condições de Tormenta20 (Edição Jogo do Ano).
Guiada pela TIPOGRAFIA (não pelo TOC). Páginas 400 e 401 (livro, págs 394–395).

Tipografia = schema:
  - Cabeçalho de cada condição: IowanOldStyle-Bold ~9.5 pt (ex.: "Abalado.", "Fatigado.").
  - Descrição mecânica da condição: IowanOldStyle-Roman ~9.5 pt.
  - Tipo de efeito (se houver): IowanOldStyle-Italic ~9.5 pt ao final da descrição
    (ex.: Medo, Mental, Movimento, Metabolismo, Sentidos, Cansaço, Veneno, Metamorfose).
  - Progressão de condição (se houver): Detectada na regra (ex.: "Se ficar fatigado novamente, em vez disso fica exausto").
  - Regras gerais de condições: Bloco introdutório no topo da pág. 400 (acúmulo, duração de cena, tipos de efeitos).

Lê o PDF; escreve dados/condicoes.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
OUT = BASE / "dados" / "condicoes.json"
OUT.parent.mkdir(exist_ok=True)

# Páginas do apêndice de condições no PDF (1-based: 400 e 401)
PAGINAS_CONDICOES = [400, 401]

TIPOS_EFEITO_VALIDOS = {
    "Medo", "Mental", "Movimento", "Metabolismo",
    "Sentidos", "Cansaço", "Veneno", "Metamorfose"
}


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def dehyph(s):
    if not s:
        return ""
    # 1. Junta palavras hifenizadas quebradas em quebra de linha
    s = re.sub(r"(\w+)[-\xad\u00ad]\s+(\w+)", r"\1\2", s)
    # 2. Remove hifens suaves residuais
    s = re.sub(r"[\xad\u00ad]", "", s)
    # 3. Colapsa espaços múltiplos
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extrair_condicoes():
    doc = pymupdf.open(str(PDF))
    
    spans = []
    for pno in PAGINAS_CONDICOES:
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
                            "italic": bool(s["flags"] & 2) or ("Italic" in s["font"]),
                            "page": pno,
                        })
                        
    # 1. Identificar cabeçalhos de condições em negrito
    cond_spans_idx = []
    for i, s in enumerate(spans):
        t = s["text"]
        if (s["bold"] and s["size"] >= 9.0 and t.endswith(".") and 
            t not in ["Apêndice.", "Apêndice"] and "SourceSans" not in s["font"]):
            nome = t.rstrip(".")
            cond_spans_idx.append((i, nome, s["page"]))
            
    # 2. Extrair texto da regra geral de condições (topo da página 400 antes da primeira condição)
    primeiro_idx = cond_spans_idx[0][0] if cond_spans_idx else 0
    intro_spans = [
        s for s in spans[:primeiro_idx]
        if s["text"] not in ["Apêndice", "Lista de Condições", "394", "395"]
        and "SourceSans" not in s["font"]
        and not (s["size"] >= 20)
    ]
    intro_texto = dehyph(" ".join([s["text"] for s in intro_spans]))
    
    regra_geral = {
        "id": "regra_condicoes_acumulo_duracao",
        "tipo_entidade": "regra_condicao",
        "titulo": "Regras Gerais de Condições (Acúmulo, Duração e Tipos de Efeito)",
        "pagina": 400,
        "resumo": "Condições com mesmos efeitos não se acumulam. Duração padrão é até o fim da cena. Tipos de efeito definem imunidades e interações.",
        "texto": (
            "Regras Gerais de Condições:\n"
            "• Acúmulo: Condições com os mesmos efeitos não se acumulam; aplique apenas os mais severos. "
            "Por exemplo, um personagem desprevenido e vulnerável sofre –5 na Defesa, não –7.\n"
            "• Duração Padrão: A menos que especificado o contrário, condições terminam no fim da cena (ou ~15 minutos).\n"
            "• Tipos de Efeitos: Algumas condições possuem um tipo de efeito associado (Cansaço, Medo, Mental, Metabolismo, "
            "Metamorfose, Movimento, Sentidos, Veneno). Criaturas imunes a determinado tipo de efeito não são afetadas pelas condições daquele tipo."
        ),
    }

    # 3. Processar cada uma das 35 condições
    condicoes = []
    for idx, (span_i, nome, page) in enumerate(cond_spans_idx):
        next_span_i = cond_spans_idx[idx + 1][0] if idx + 1 < len(cond_spans_idx) else len(spans)
        
        body_spans = spans[span_i + 1 : next_span_i]
        cleaned_body_spans = [
            s for s in body_spans 
            if s["text"] not in ["Apêndice", "Lista de Condições", "394", "395"] 
            and "SourceSans" not in s["font"]
            and not (s["size"] >= 20)
        ]
        
        # Identificar tipo de efeito em itálico no final
        tipo_efeito = ""
        for s in reversed(cleaned_body_spans):
            stxt = s["text"].strip(" .")
            if s["italic"] and stxt in TIPOS_EFEITO_VALIDOS:
                tipo_efeito = stxt
                break
                
        full_text = " ".join([s["text"] for s in cleaned_body_spans])
        full_text = dehyph(full_text)
        
        # Limpar o rótulo do tipo de efeito do corpo da descrição
        if tipo_efeito:
            full_text = re.sub(r"\s*" + re.escape(tipo_efeito) + r"\s*\.?$", "", full_text).strip()
            
        # Detectar escalamento / progressão mecânica (ex: "Se ficar fatigado novamente, em vez disso fica exausto")
        m_piora = re.search(r"em vez disso fica\s+([a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ\s]+?)\.", full_text, re.I)
        piora_para = m_piora.group(1).strip().capitalize() if m_piora else ""
        
        condicoes.append({
            "id": f"condicao_{slug(nome)}",
            "tipo_entidade": "condicao",
            "nome": nome,
            "tipo_efeito": tipo_efeito if tipo_efeito else "Geral",
            "piora_para": piora_para,
            "descricao": full_text,
            "pagina": page,
        })
        
    banco = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (Apêndice: Lista de Condições, págs 400–401)",
        "total_condicoes": len(condicoes),
        "regra_geral": regra_geral,
        "condicoes": condicoes,
    }
    
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    return banco


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Extraindo condições de {PDF.name} (págs {PAGINAS_CONDICOES})...")
    banco = extrair_condicoes()
    conds = banco["condicoes"]
    
    print(f"Sucesso! {len(conds)} condições e 1 regra geral salvas em {OUT}")
    
    # Estatísticas por tipo de efeito
    por_tipo = {}
    escalam = []
    for c in conds:
        t = c["tipo_efeito"]
        por_tipo[t] = por_tipo.get(t, 0) + 1
        if c["piora_para"]:
            escalam.append(f"{c['nome']} -> {c['piora_para']}")
            
    print("\n--- Estatísticas de Condições ---")
    print(f"Por Tipo de Efeito: {json.dumps(por_tipo, ensure_ascii=False)}")
    print(f"Condições que Escalam ({len(escalam)}): {', '.join(escalam)}")


if __name__ == "__main__":
    main()
