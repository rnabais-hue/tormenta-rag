# -*- coding: utf-8 -*-
r"""
Consulta RAG ao livro de Tormenta20.

Fluxo (cada pergunta):
  pergunta -> embedding (bge-m3) -> busca top-k no FAISS
           -> monta prompt (contexto recuperado + pergunta)
           -> Qwen3-8B via Ollama -> resposta citando a fonte (seção/página)

Uso:
  python perguntar.py "Como funciona a condição fatigado?"
  python perguntar.py                # modo interativo (perguntas em loop)
  python perguntar.py -k 8 "..."     # muda quantos trechos recupera

Pré-requisitos: ingestao.py já rodado (index\ populado) e Ollama no ar
(servidor em http://127.0.0.1:11434 com o modelo qwen3:8b).
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import faiss
import requests
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
LOG_DIR = BASE / "logs"
LOG_CONSULTAS = LOG_DIR / "consultas.jsonl"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODELO_LLM = "qwen3:8b"
TOP_K = 5

INSTRUCAO = (
    "Você é um assistente de regras do RPG Tormenta20. Responda à pergunta "
    "USANDO SOMENTE os trechos do livro fornecidos como contexto. Seja preciso "
    "e direto. Cite a(s) fonte(s) usando a marca [Fonte N]. Se a resposta não "
    "estiver no contexto, diga claramente que não encontrou no material fornecido "
    "— não invente regra."
)


def carregar():
    """Carrega índice FAISS, metadados dos chunks e o embedder."""
    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    chunks = [
        json.loads(l)
        for l in (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    model = SentenceTransformer(meta["modelo_embed"])
    return index, chunks, model, meta


# ---------------------------------------------------- motor de poderes (B/C/D)
# Camada relacional (Stages B/C/D): responde perguntas de PLANEJAMENTO
# ("o que preciso para o poder X?") e de ELEGIBILIDADE por classe ("que poderes
# um paladino nível 6 pode pegar?") com um bloco FACTUAL determinístico — sem
# alucinar pré-requisito. O motor vive em personagem.py e lê os JSON de dados.
from personagem import Mundo, Personagem, bloco_overview, norm as _pnorm

_MUNDO = None


def _mundo():
    global _MUNDO
    if _MUNDO is None:
        _MUNDO = Mundo()
    return _MUNDO


_SINAL_PREREQ = re.compile(
    r"pr[ée]-?requisito|requisito|o que .*(preciso|precisa|necess)|"
    r"como (pego|consigo|conseguir|pegar|obter|ter|adquirir)|"
    r"[áa]rvore|do que depende|o que .*(exige|pede)", re.I)
_SINAL_LISTA = re.compile(
    r"(quais|que|quantos)\s+poderes|poderes\s+(que|dispon|posso|pode)|"
    r"lista de poderes", re.I)
_SINAL_PODE = re.compile(
    r"pode(m)?\s+(pegar|escolher|comprar|ter|usar)|posso\s+(pegar|escolher|ter)|"
    r"dispon[íi]ve", re.I)
_RE_NIVEL = re.compile(r"n[íi]vel\s+(\d+)|\bnv?\.?\s*(\d+)\b|\bn(\d+)\b", re.I)


def _acha_poder_na_query(query, mundo):
    """Maior nome de poder citado na query (evita casar 'Aparar' em 'reparar')."""
    ql = " " + _pnorm(query) + " "
    melhor = None
    for p in mundo.poderes:
        n = _pnorm(p["nome"])
        if len(n) < 4:
            continue
        if re.search(r"(?<![\wáéíóúâêôãõç])" + re.escape(n) + r"(?![\wáéíóúâêôãõç])", ql):
            if melhor is None or len(n) > len(_pnorm(melhor["nome"])):
                melhor = p
    return melhor


def detectar_intent_poder(query):
    """Detecta intenção do motor de poderes. Conservador: só dispara com sinal
    claro + entidade nomeada. Retorna (tipo, dados, rotulo) ou None.
      ("prereq", nome_do_poder, rotulo)
      ("overview", {classe, nivel, deus}, rotulo)"""
    m = _mundo()
    ql = _pnorm(query)

    # ELEGIBILIDADE por classe: "que poderes um paladino [nível N] [devoto de X] pode pegar"
    if _SINAL_LISTA.search(query) and _SINAL_PODE.search(query):
        classe = next((c["nome"] for c in m.classes
                       if re.search(r"\b" + re.escape(_pnorm(c["nome"])) + r"\b", ql)), None)
        if classe:
            mn = _RE_NIVEL.search(query)
            nivel = int(next(g for g in mn.groups() if g)) if mn else None
            deus = next((d["nome"] for d in m.deuses
                         if re.search(r"\b" + re.escape(_pnorm(d["nome"])) + r"\b", ql)), None)
            rot = f"poderes de {classe}" + (f" nível {nivel}" if nivel else "") \
                  + (f" devoto de {deus}" if deus else "")
            return ("overview", {"classe": classe, "nivel": nivel, "deus": deus}, rot)

    # PLANEJAMENTO: pré-requisitos / árvore de um poder nomeado
    if _SINAL_PREREQ.search(query):
        p = _acha_poder_na_query(query, m)
        if p:
            return ("prereq", p["nome"], f"pré-requisitos de {p['nome']}")

    return None


def _hit_motor(texto, secao, pagina):
    """Empacota o bloco do motor como um 'chunk' sintético (Fonte) para o prompt."""
    return {"id": "motor:poderes", "tipo": "motor", "secao": secao,
            "titulo": secao, "pagina": pagina, "texto": texto, "score": 1.0,
            "match_filtro": "motor de poderes (B/C/D)"}


def hits_do_motor(intent):
    """Constrói o(s) hit(s) determinístico(s) para a intenção detectada."""
    m = _mundo()
    tipo, dados, _ = intent
    if tipo == "prereq":
        pj = Personagem(m, {})                     # personagem vazio: só caminha a árvore
        texto, p = pj.bloco_prereq(dados)
        if not texto:
            return []
        return [_hit_motor(texto, f"Motor de Poderes — {p['nome']}", p.get("pagina", "—"))]
    if tipo == "overview":
        texto, n = bloco_overview(m, dados["classe"], dados.get("nivel"), dados.get("deus"))
        return [_hit_motor(texto, f"Motor de Poderes — {dados['classe']}", "—")]
    return []


# ---------------------------------------------------- filtro híbrido (metadado)
# Nomes completos dos atributos (sem abreviações de 3 letras — ruído em texto NL).
_ATRIB = {
    "força": "Força", "forca": "Força",
    "destreza": "Destreza",
    "constituição": "Constituição", "constituicao": "Constituição",
    "inteligência": "Inteligência", "inteligencia": "Inteligência",
    "sabedoria": "Sabedoria",
    "carisma": "Carisma",
}
_CUE_POS = re.compile(r"b[ôo]nus|positiv|aumenta|ganha|melhor|\+\s*\d", re.I)
_CUE_NEG = re.compile(r"penalidad|negativ|reduz|redu[çc]|desvantag|pior|-\s*\d", re.I)


def detectar_filtro(query):
    """Detecta intenção de FILTRO por modificador de raça. Conservador: só dispara
    com (a) menção a 'raça(s)', (b) um atributo e (c) um sinal de bônus/penalidade.
    Assim NÃO dispara em 'como funciona Carisma'. Retorna (atributo, 'pos'|'neg')."""
    ql = query.lower()
    if not re.search(r"ra[çc]as?\b", ql):
        return None
    attr = next((v for k, v in _ATRIB.items() if re.search(r"\b" + k + r"\b", ql)), None)
    if not attr:
        return None
    neg, pos = _CUE_NEG.search(ql), _CUE_POS.search(ql)
    if neg and not pos:
        return (attr, "neg")
    if pos:
        return (attr, "pos")
    return None                        # atributo + raça, mas sem sinal → não filtra


def _satisfaz(chunk, attr, pol):
    """O chunk (raça) tem o modificador pedido? Considera sub-raças (variantes)."""
    vals = []
    m = chunk.get("modificadores") or {}
    if isinstance(m.get(attr), int):
        vals.append(m[attr])
    for d in (chunk.get("modificadores_variantes") or {}).values():
        if isinstance(d.get(attr), int):
            vals.append(d[attr])
    if not vals:
        return False
    return any(v > 0 for v in vals) if pol == "pos" else any(v < 0 for v in vals)


# ---- filtro híbrido de PERÍCIA (por atributo-chave / flags) -----------------
_CUE_SO_TREINADA = re.compile(r"(s[óo]|somente|apenas)\s+treinad", re.I)
_CUE_ARMADURA = re.compile(r"penalidade\s+de\s+armadura|armadura", re.I)


def detectar_filtro_pericia(query):
    """Detecta FILTRO por campo de perícia. Conservador: exige o plural
    'perícias' (intenção de listar) + um predicado. Retorna (campo, valor,
    rotulo) ou None. Predicados: 'só treinada', 'penalidade de armadura', ou um
    atributo-chave ('perícias de Destreza'). NÃO dispara em 'o que faz Acrobacia'."""
    ql = query.lower()
    if not re.search(r"per[íi]cias\b", ql):        # plural → listar
        return None
    if _CUE_SO_TREINADA.search(ql):
        return ("so_treinada", True, "só treinada")
    if _CUE_ARMADURA.search(ql):
        return ("penalidade_armadura", True, "penalidade de armadura")
    attr = next((v for k, v in _ATRIB.items() if re.search(r"\b" + k + r"\b", ql)), None)
    if attr:
        return ("atributo", attr, f"atributo-chave {attr}")
    return None


def _satisfaz_pericia(chunk, campo, valor):
    return chunk.get(campo) == valor


# ---- filtro híbrido de ORIGEM (por perícia/poder concedido) -----------------
def detectar_filtro_origem(query, chunks):
    """Detecta FILTRO 'quais origens dão a perícia/poder X'. Exige a palavra
    'origem/origens' + o nome de uma PERÍCIA (conjunto fechado de 29) ou de um
    PODER concedido por alguma origem. Retorna (campo, valor, rotulo) ou None.

    Desambiguação: nomes de poder contêm nomes de perícia (ex.: "Vontade de
    Ferro" ⊃ "Vontade"). Escolhe o match preferindo (a) o campo citado na pergunta
    ('perícia'/'poder') e (b) o nome MAIS LONGO."""
    ql = query.lower()
    if not re.search(r"orige[mn]s?\b", ql):
        return None
    pref = "pericias" if re.search(r"per[íi]cias?\b", ql) else \
           ("poderes" if re.search(r"poder", ql) else None)
    cands = [(n, "pericias") for n in {c["titulo"] for c in chunks if c.get("tipo") == "pericia"}]
    cands += [(p, "poderes") for p in {p for c in chunks if c.get("tipo") == "origem"
                                       for p in (c.get("poderes") or []) if len(p.split()) >= 2}]
    achados = [(n, campo) for n, campo in cands
               if re.search(r"\b" + re.escape(n.lower()) + r"\b", ql)]
    if not achados:
        return None
    achados.sort(key=lambda x: (x[1] != pref, -len(x[0])))   # campo citado, depois mais longo
    nome, campo = achados[0]
    rotulo = f"origem concede {'a perícia' if campo == 'pericias' else 'o poder'} {nome}"
    return (campo, nome, rotulo)


# ---- filtro híbrido de DEUS (por energia / devoto) --------------------------
def _sem_acento(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return s


def _base_dev(s):
    """Normaliza p/ casar devoto: sem acento + dobra plural 'ões'→'ão'."""
    return _sem_acento(s).replace("oes", "ao")


def _casa_devoto(nome, devoto):
    """'paladino' casa 'paladinos'; 'anão' casa 'anões'; etc. (prefixo tolerante)."""
    a, b = _base_dev(nome), _base_dev(devoto)
    return len(a) >= 3 and (b.startswith(a) or a.startswith(b))


def _devotos_amplo(chunk):
    """O deus aceita QUALQUER classe? (Aharadak 'Quaisquer', Valkaria 'todas as
    classes'/'aventureiros'). Não conta 'Qualquer duyshidakk' (restrito a raça)."""
    txt = " ".join(chunk.get("devotos") or [])
    return bool(re.search(r"quaisquer|todas as classes|aventureiros", _sem_acento(txt)))


_ENERGIAS = {"positiva": "Positiva", "negativa": "Negativa", "qualquer": "Qualquer"}


def detectar_filtro_deus(query, chunks):
    """Detecta FILTRO de deus. Exige 'deus/deuses' + (a) energia
    (Positiva/Negativa/Qualquer) ou (b) uma classe/raça ('quais deuses um paladino
    pode seguir'). Humano/clérigo seguem qualquer deus. Retorna (campo, valor,
    rotulo) ou None."""
    ql = _sem_acento(query)
    if not re.search(r"deus(es)?\b", ql):
        return None
    if re.search(r"\benergia\b", ql):
        for k, v in _ENERGIAS.items():
            if re.search(r"\b" + k + r"\b", ql):
                return ("energia", v, f"energia {v}")
    # humanos e clérigos são exceção: podem seguir qualquer deus
    if re.search(r"\bhumano\b|\bclerigo\b", ql):
        return ("todos", None, "humano/clérigo: qualquer deus")
    # classe/raça mencionada (conjuntos fechados vindos dos chunks)
    nomes = {c.get("classe") for c in chunks if c.get("tipo") == "classe"} | \
            {c.get("titulo") for c in chunks if c.get("tipo") == "raca"}
    for nome in sorted((n for n in nomes if n), key=len, reverse=True):
        if re.search(r"\b" + re.escape(_sem_acento(nome)) + r"\b", ql):
            return ("devoto", nome, f"devoto: {nome}")
    return None


def _satisfaz_deus(chunk, campo, valor):
    if campo == "todos":
        return True
    if campo == "energia":
        return chunk.get("energia") == valor
    if campo == "devoto":
        return _devotos_amplo(chunk) or \
            any(_casa_devoto(valor, dv) for dv in (chunk.get("devotos") or []))
    return False


# ---- filtro híbrido de ATRIBUTO (direto e inverso via perícia governada) -----
def detectar_filtro_atributo(query, chunks):
    """Exige a palavra 'atributo' + (a) uma PERÍCIA → devolve o atributo que a
    governa (inverso), ou (b) um nome de ATRIBUTO → devolve o próprio atributo
    (direto). Conservador: o gatilho 'atributo' separa de 'perícias de Força'
    (que fica no filtro de perícia). Retorna (campo, valor, rotulo) ou None."""
    ql = _sem_acento(query)
    if not re.search(r"\batributo", ql):
        return None
    pericias = sorted({c["titulo"] for c in chunks if c.get("tipo") == "pericia"},
                      key=len, reverse=True)
    for nome in pericias:
        if re.search(r"\b" + re.escape(_sem_acento(nome)) + r"\b", ql):
            return ("governa", nome, f"atributo que governa {nome}")
    attrs = sorted({c.get("nome") for c in chunks if c.get("tipo") == "atributo"},
                   key=lambda n: len(n or ""), reverse=True)
    for nome in attrs:
        if nome and re.search(r"\b" + re.escape(_sem_acento(nome)) + r"\b", ql):
            return ("nome", nome, f"atributo {nome}")
    return None


def _satisfaz_atributo(chunk, campo, valor):
    if campo == "nome":
        return chunk.get("nome") == valor
    if campo == "governa":
        return valor in (chunk.get("pericias_governadas") or [])
    return False


# ---- filtro híbrido de EQUIPAMENTO (armas, armaduras, esotéricos, etc.) -------
def detectar_filtro_equipamento(query, chunks):
    """Detecta perguntas de listagem de categoria de equipamento:
    - 'armas simples' / 'armas marciais' / 'armas exóticas' / 'armas de fogo'
    - 'armaduras leves' / 'armaduras pesadas' / 'escudos'
    - 'materiais especiais' / 'melhorias superiores'
    - 'itens esotéricos' / 'preparados alquímicos' / 'venenos'
    Retorna (campo, valor, rotulo) ou None.
    """
    ql = _sem_acento(query)
    
    # Armas por proficiência
    if re.search(r"\barmas?\s+simples\b", ql):
        return ("arma_prof", "Simples", "armas simples")
    if re.search(r"\barmas?\s+marciais?\b", ql):
        return ("arma_prof", "Marcial", "armas marciais")
    if re.search(r"\barmas?\s+exoticas?\b", ql):
        return ("arma_prof", "Exótica", "armas exóticas")
    if re.search(r"\barmas?\s+de\s+fogo\b", ql):
        return ("arma_prof", "Fogo", "armas de fogo")
        
    # Armaduras e Escudos
    if re.search(r"\barmaduras?\s+leves?\b", ql):
        return ("armadura_sub", "Armaduras Leves", "armaduras leves")
    if re.search(r"\barmaduras?\s+pesadas?\b", ql):
        return ("armadura_sub", "Armaduras Pesadas", "armaduras pesadas")
    if re.search(r"\b(quais|lista\s+de)\s+escudos\b", ql):
        return ("armadura_sub", "Escudos", "escudos")
        
    # Materiais e Melhorias
    if re.search(r"\bmateriais?\s+especia(is|l)\b", ql):
        return ("tipo", "material_especial", "materiais especiais")
    if re.search(r"\bmelhorias?\s+(superiores?|de\s+item)\b|\bmelhorias?\s+para\s+(armas?|armaduras?)\b", ql):
        return ("tipo", "melhoria_superior", "melhorias superiores")
        
    # Esotéricos e Alquímicos
    if re.search(r"\b(itens?\s+)?esotericos?\b", ql) and not re.search(r"\bo\s+que\s+faz\b", ql):
        return ("item_sub", "Esotéricos", "itens esotéricos")
    if re.search(r"\bpreparados?\s+alquimicos?\b", ql):
        return ("item_sub", "Alquímicos — Preparados", "preparados alquímicos")
    if re.search(r"\bvenenos?\s+alquimicos?\b|\bquais\s+s?a?o?\s+os\s+venenos\b", ql):
        return ("item_sub", "Alquímicos — Venenos", "venenos")

    return None


def _satisfaz_equipamento(chunk, campo, valor):
    tipo = chunk.get("tipo", "")
    if campo == "arma_prof":
        return (tipo == "equipamento" and chunk.get("categoria") == "arma" and chunk.get("proficiencia") == valor) or \
               (tipo == "equipamento_lista" and chunk.get("proficiencia") == valor)
    if campo == "armadura_sub":
        return (tipo == "equipamento" and chunk.get("subcategoria") == valor) or \
               (tipo == "equipamento_lista" and chunk.get("subcategoria") == valor)
    if campo == "item_sub":
        return (tipo == "equipamento" and chunk.get("subcategoria") == valor) or \
               (tipo == "equipamento_lista" and chunk.get("subcategoria") == valor)
    if campo == "tipo":
        return tipo == valor or (tipo == "equipamento_lista" and chunk.get("categoria") == valor)
    return False


def buscar(query, index, chunks, model, k=TOP_K):
    """Embeda a pergunta e retorna os k chunks mais similares (com score).

    Busca HÍBRIDA: se a pergunta é um filtro por modificador de raça (detectar_
    filtro), os chunks de raça que satisfazem o predicado nos METADADOS sobem ao
    topo (ordenados por similaridade), resolvendo casos como 'raças com bônus de
    Carisma' que a busca vetorial pura erra. Caso contrário, busca vetorial normal."""
    # motor de poderes (B/C/D): resposta determinística tem prioridade
    intent = detectar_intent_poder(query)
    if intent:
        hits = hits_do_motor(intent)
        if hits:
            return hits

    q = model.encode([query], normalize_embeddings=True).astype("float32")

    filtro = detectar_filtro(query)
    if filtro:
        attr, pol = filtro
        idxs = [i for i, c in enumerate(chunks)
                if c.get("tipo") == "raca" and _satisfaz(c, attr, pol)]
        if idxs:
            vecs = np.array([index.reconstruct(int(i)) for i in idxs], dtype="float32")
            sims = vecs @ q[0]                          # similaridade (cosseno) dos que casam
            hits = []
            for j in np.argsort(-sims):
                c = dict(chunks[idxs[int(j)]])
                c["score"] = float(sims[int(j)])
                c["match_filtro"] = f"{attr} {'>' if pol == 'pos' else '<'} 0"
                hits.append(c)
            # a pergunta é uma LISTA por modificador: as raças que casam SÃO a
            # resposta — não polui com chunks de texto vetorial (só ruído). Teto 10.
            return hits[:10]

    filtro_p = detectar_filtro_pericia(query)
    if filtro_p:
        campo, valor, rotulo = filtro_p
        idxs = [i for i, c in enumerate(chunks)
                if c.get("tipo") == "pericia" and _satisfaz_pericia(c, campo, valor)]
        if idxs:
            vecs = np.array([index.reconstruct(int(i)) for i in idxs], dtype="float32")
            sims = vecs @ q[0]
            hits = []
            for j in np.argsort(-sims):
                c = dict(chunks[idxs[int(j)]])
                c["score"] = float(sims[int(j)])
                c["match_filtro"] = rotulo
                hits.append(c)
            return hits[:12]                        # há no máx. ~11 por predicado

    filtro_a = detectar_filtro_atributo(query, chunks)
    if filtro_a:
        campo, valor, rotulo = filtro_a
        idxs = [i for i, c in enumerate(chunks)
                if c.get("tipo") == "atributo" and _satisfaz_atributo(c, campo, valor)]
        if idxs:
            vecs = np.array([index.reconstruct(int(i)) for i in idxs], dtype="float32")
            sims = vecs @ q[0]
            hits = []
            for j in np.argsort(-sims):
                c = dict(chunks[idxs[int(j)]])
                c["score"] = float(sims[int(j)])
                c["match_filtro"] = rotulo
                hits.append(c)
            return hits[:6]

    filtro_o = detectar_filtro_origem(query, chunks)
    if filtro_o:
        campo, valor, rotulo = filtro_o
        idxs = [i for i, c in enumerate(chunks)
                if c.get("tipo") == "origem" and valor in (c.get(campo) or [])]
        if idxs:
            vecs = np.array([index.reconstruct(int(i)) for i in idxs], dtype="float32")
            sims = vecs @ q[0]
            hits = []
            for j in np.argsort(-sims):
                c = dict(chunks[idxs[int(j)]])
                c["score"] = float(sims[int(j)])
                c["match_filtro"] = rotulo
                hits.append(c)
            return hits[:12]

    filtro_d = detectar_filtro_deus(query, chunks)
    if filtro_d:
        campo, valor, rotulo = filtro_d
        idxs = [i for i, c in enumerate(chunks)
                if c.get("tipo") == "deus" and _satisfaz_deus(c, campo, valor)]
        if idxs:
            vecs = np.array([index.reconstruct(int(i)) for i in idxs], dtype="float32")
            sims = vecs @ q[0]
            hits = []
            for j in np.argsort(-sims):
                c = dict(chunks[idxs[int(j)]])
                c["score"] = float(sims[int(j)])
                c["match_filtro"] = rotulo
                hits.append(c)
            return hits[:20]                        # há 20 deuses

    filtro_eq = detectar_filtro_equipamento(query, chunks)
    if filtro_eq:
        campo, valor, rotulo = filtro_eq
        idxs = [i for i, c in enumerate(chunks)
                if _satisfaz_equipamento(c, campo, valor)]
        if idxs:
            vecs = np.array([index.reconstruct(int(i)) for i in idxs], dtype="float32")
            sims = vecs @ q[0]
            hits = []
            for j in np.argsort(-sims):
                c = dict(chunks[idxs[int(j)]])
                c["score"] = float(sims[int(j)])
                c["match_filtro"] = rotulo
                hits.append(c)
            return hits[:15]

    scores, ids = index.search(q, k)
    hits = []
    for score, i in zip(scores[0], ids[0]):
        if i < 0:
            continue
        c = dict(chunks[i])
        c["score"] = float(score)
        hits.append(c)
    return hits


def montar_prompt(query, hits):
    """Monta o texto de contexto numerado + a pergunta."""
    blocos = []
    for n, h in enumerate(hits, 1):
        blocos.append(
            f"[Fonte {n}] (Seção: {h['secao']} — pág. {h['pagina']})\n{h['texto']}"
        )
    contexto = "\n\n".join(blocos)
    nota = ""
    if any(h.get("tipo") == "motor" for h in hits):
        nota = ("\n\nOBS: a fonte acima é uma resposta CALCULADA pelo sistema de regras "
                "(elegibilidade e pré-requisitos de poderes). Apresente-a fielmente, sem "
                "omitir itens da lista nem inventar pré-requisitos.")
    return f"CONTEXTO:\n{contexto}\n\nPERGUNTA: {query}{nota}"


def _payload_ollama(prompt, stream):
    return {
        "model": MODELO_LLM,
        "messages": [
            {"role": "system", "content": INSTRUCAO},
            {"role": "user", "content": prompt},
        ],
        "think": False,                 # desliga o modo 'thinking' (mais rápido)
        "stream": stream,
        "options": {"temperature": 0.2},
    }


def iter_ollama(prompt):
    """Gera a resposta token a token (para streaming). Cada yield é um pedaço
    de texto. Manter os bytes fluindo evita que conexões ociosas longas sejam
    derrubadas ('Failed to fetch') e dá feedback progressivo na CPU lenta."""
    resp = requests.post(OLLAMA_URL, json=_payload_ollama(prompt, True),
                         stream=True, timeout=600)
    resp.raise_for_status()
    for linha in resp.iter_lines():
        if not linha:
            continue
        dado = json.loads(linha)
        if "message" in dado and dado["message"].get("content"):
            yield dado["message"]["content"]
        if dado.get("done"):
            break


def perguntar_ollama(prompt, stream=True):
    """Chama o Qwen3-8B via Ollama e devolve o texto completo. Se stream=True,
    também imprime os tokens no terminal enquanto chegam (usado pela CLI)."""
    if not stream:
        resp = requests.post(OLLAMA_URL, json=_payload_ollama(prompt, False),
                             timeout=600)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    partes = []
    for tok in iter_ollama(prompt):
        partes.append(tok)
        print(tok, end="", flush=True)
    print()
    return "".join(partes)


def registrar_log(registro):
    """Anexa um registro de consulta em logs/consultas.jsonl (uma linha JSON).
    É a base para catalogar falhas de recuperação sem reprocessar o índice."""
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_CONSULTAS, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def fontes_de_hits(hits):
    """Converte os chunks recuperados no formato leve usado em logs/respostas."""
    fontes = []
    for n, h in enumerate(hits, 1):
        f = {
            "rank": n,
            "id": h.get("id"),
            "secao": h["secao"],
            "pagina": h["pagina"],
            "score": round(h["score"], 4),
            "previa": h["texto"][:160].replace("\n", " "),
        }
        if h.get("match_filtro"):
            f["match_filtro"] = h["match_filtro"]
        fontes.append(f)
    return fontes


def consultar(query, index, chunks, model, meta, k=TOP_K, stream=False, log=True):
    """Executa a consulta RAG completa e devolve um dicionário estruturado
    (pergunta, resposta, trechos com rank/score, duração). Grava em log se log=True.
    Esta é a função central usada pela CLI, pela interface web e pela suíte."""
    t0 = time.time()
    hits = buscar(query, index, chunks, model, k)
    t_busca = time.time() - t0
    resposta = ""
    if hits:
        t1 = time.time()
        resposta = perguntar_ollama(montar_prompt(query, hits), stream=stream)
        t_gerar = time.time() - t1
    else:
        t_gerar = 0.0

    fontes = fontes_de_hits(hits)
    filtro = detectar_filtro(query)
    filtro_p = detectar_filtro_pericia(query)
    filtro_o = detectar_filtro_origem(query, chunks)
    filtro_d = detectar_filtro_deus(query, chunks)
    filtro_a = detectar_filtro_atributo(query, chunks)
    filtro_eq = detectar_filtro_equipamento(query, chunks)
    intent_poder = detectar_intent_poder(query)
    registro = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "pergunta": query,
        "k": k,
        "modelo_embed": meta.get("modelo_embed"),
        "modelo_llm": MODELO_LLM,
        "n_chunks_indice": meta.get("n_chunks"),
        "filtro_metadado": ({"atributo": filtro[0], "polaridade": filtro[1]}
                            if filtro else None),
        "filtro_pericia": ({"campo": filtro_p[0], "valor": filtro_p[1]}
                           if filtro_p else None),
        "filtro_origem": ({"campo": filtro_o[0], "valor": filtro_o[1]}
                          if filtro_o else None),
        "filtro_deus": ({"campo": filtro_d[0], "valor": filtro_d[1]}
                        if filtro_d else None),
        "filtro_atributo": ({"campo": filtro_a[0], "valor": filtro_a[1]}
                            if filtro_a else None),
        "filtro_equipamento": ({"campo": filtro_eq[0], "valor": filtro_eq[1]}
                              if filtro_eq else None),
        "filtro_poder": ({"tipo": intent_poder[0], "rotulo": intent_poder[2]}
                         if intent_poder else None),
        "resposta": resposta,
        "fontes": fontes,
        "seg_busca": round(t_busca, 2),
        "seg_geracao": round(t_gerar, 2),
    }
    if log:
        registrar_log(registro)
    return registro


def responder(query, index, chunks, model, meta, k=TOP_K):
    """Versão para terminal: streama a resposta e imprime as fontes."""
    print("\n" + "=" * 70)
    print("RESPOSTA:\n")
    reg = consultar(query, index, chunks, model, meta, k=k, stream=True)
    if not reg["fontes"]:
        print("Nenhum trecho recuperado.")
        return reg
    print("\n" + "-" * 70)
    if reg.get("filtro_metadado"):
        fm = reg["filtro_metadado"]
        sinal = "bônus" if fm["polaridade"] == "pos" else "penalidade"
        print(f"[filtro híbrido ativo: raças com {sinal} em {fm['atributo']}]")
    print("FONTES RECUPERADAS:")
    for f in reg["fontes"]:
        marca = "  ⟵ filtro" if f.get("match_filtro") else ""
        print(f"  [Fonte {f['rank']}] {f['secao']} (pág. {f['pagina']}) — sim={f['score']:.3f}{marca}")
    print(f"(busca {reg['seg_busca']}s | geração {reg['seg_geracao']}s | log em {LOG_CONSULTAS.name})")
    return reg


def main():
    ap = argparse.ArgumentParser(description="Consulta RAG ao livro de Tormenta20")
    ap.add_argument("pergunta", nargs="*", help="pergunta (se vazio, modo interativo)")
    ap.add_argument("-k", type=int, default=TOP_K, help="quantos trechos recuperar")
    args = ap.parse_args()

    if not (INDEX_DIR / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py primeiro.")

    print("Carregando índice e embedder...")
    index, chunks, model, meta = carregar()
    print(f"  {meta['n_chunks']} chunks | embedder {meta['modelo_embed']} | LLM {MODELO_LLM}")

    if args.pergunta:
        responder(" ".join(args.pergunta), index, chunks, model, meta, args.k)
    else:
        print("Modo interativo. Digite a pergunta (Ctrl+C ou vazio para sair).")
        try:
            while True:
                q = input("\n> ").strip()
                if not q:
                    break
                responder(q, index, chunks, model, meta, args.k)
        except (KeyboardInterrupt, EOFError):
            print("\nAté mais.")


if __name__ == "__main__":
    main()
