# -*- coding: utf-8 -*-
"""
Stage B da família RELACIONAL de Poderes (ver README §11).

Lê os catálogos de poder (Stage A) e converte o campo `pre_requisito` (TEXTO)
em `pre_requisito_estruturado`: PREDICADOS auditáveis.

Estrutura de saída (campo novo em cada poder que tem pré-requisito):
    pre_requisito_estruturado = [ grupo, grupo, ... ]        # AND entre grupos
    grupo = { "ou": [ atomo, atomo, ... ] }                  # OR dentro do grupo

Tipos de átomo:
    {tipo:"atributo",         attr:"For", valor:1}
    {tipo:"nivel_classe",     classe:"arcanista", nivel:10}
    {tipo:"nivel_personagem", nivel:12}
    {tipo:"treino_pericia",   pericia:"Ofício", especializacao:"alquimista"?, escolhida:bool?}
    {tipo:"proficiencia",     alvo:"armaduras pesadas"}
    {tipo:"poder",            nome:"Raio Arcano", ref_ids:[...], com:"a escola escolhida"?}
    {tipo:"classe",           classe:"Mago"}          # multiclasse / pré-classe
    {tipo:"caminho",          nome:"Bruxo", classe_base:"Arcanista"}
    {tipo:"devoto",           detalhe:"de um deus maior"}
    {tipo:"habilidade_classe",nome:"Magias"}
    {tipo:"conjuracao",       detalhe:"lançar magias de 2º círculo"}
    {tipo:"poder_quantificado", quantidade:4, grupo:"Tormenta"}
    {tipo:"livre",            texto:"..."}

Rode:  python estruturar_prereqs.py            (grava de volta nos JSON + audita)
       python estruturar_prereqs.py --audit    (só imprime a auditoria, não grava)
"""
import json, re, sys, unicodedata, io

ARQ_CLASSE = "dados/poderes_classe.json"
ARQ_GERAIS = "dados/poderes_gerais.json"
ARQ_PERICIAS = "dados/pericias.json"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLASSES = {"arcanista","barbaro","bardo","bucaneiro","cacador","cavaleiro",
           "clerigo","druida","guerreiro","inventor","ladino","lutador",
           "nobre","paladino"}
CAMINHOS_ARCANISTA = {"bruxo","mago","feiticeiro"}   # caminhos do Arcanista
NUM = {"um":1,"uma":1,"dois":2,"duas":2,"tres":3,"quatro":4,"cinco":5,
       "qualquer":1,"outro":1,"outra":1}


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


# ---- resolvedores construídos a partir dos dados reais ----------------------
def carregar_indices():
    dc = json.load(open(ARQ_CLASSE, encoding="utf-8"))
    dg = json.load(open(ARQ_GERAIS, encoding="utf-8"))
    poderes = dc + dg
    por_nome = {}                       # norm(nome) -> [ids...]
    for p in poderes:
        por_nome.setdefault(norm(p["nome"]), []).append(p["id"])
    pericias = {norm(x["nome"]): x["nome"]
                for x in json.load(open(ARQ_PERICIAS, encoding="utf-8"))}
    return dc, dg, por_nome, pericias


# ---- utilidades de split ----------------------------------------------------
def split_virgulas(texto):
    """Divide em vírgulas de topo (ignora vírgulas dentro de parênteses)."""
    partes, buf, prof = [], [], 0
    for ch in texto:
        if ch == "(":
            prof += 1
        elif ch == ")":
            prof = max(0, prof - 1)
        if ch == "," and prof == 0:
            partes.append("".join(buf).strip()); buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        partes.append("".join(buf).strip())
    return partes


def split_ou(texto):
    return [a.strip() for a in re.split(r"\s+ou\s+", texto) if a.strip()]


# ---- classificação de átomos ------------------------------------------------
RE_ATRIB = re.compile(r"^(For|Des|Con|Int|Sab|Car)\s+(\d+)$", re.I)
ATTR_CANON = {"for":"For","des":"Des","con":"Con","int":"Int","sab":"Sab","car":"Car"}
# aceita º (masculine ordinal U+00BA) e ° (degree U+00B0)
RE_NIVEL = re.compile(r"^(\d+)\s*[º°o]?\s*n[íi]vel\s+de\s+(.+)$", re.I)
RE_TREINO = re.compile(r"^treinad[oa]\s+(?:em|n[ao])\s+(.+)$", re.I)
RE_PROF = re.compile(r"^profici[êe]ncia\s+com\s+(.+)$", re.I)
RE_DEVOTO = re.compile(r"^devoto\s+de\s+(.+)$", re.I)
RE_HABCLASSE = re.compile(r"^habilidade\s+de\s+classe\s+(.+)$", re.I)
RE_PERICIA_PAREN = re.compile(r"^(.+?)\s*\(([^)]+)\)\s*$")
RE_COM_ESCOLHA = re.compile(r"^(.+?)\s+com\s+(a\s+\w+\s+escolhid[ao])$", re.I)


def resolver_poder(nome, por_nome, classe_ctx=None):
    ids = por_nome.get(norm(nome), [])
    if classe_ctx and len(ids) > 1:
        pref = [i for i in ids if i.split(":")[1] == norm(classe_ctx)]
        if pref:
            return pref
    return ids


def classificar_pericia(texto, pericias):
    """'Ofício (alquimista)' -> treino_pericia com especializacao."""
    esp = None
    m = RE_PERICIA_PAREN.match(texto)
    if m:
        base, esp = m.group(1).strip(), m.group(2).strip()
    else:
        base = texto.strip()
    canon = pericias.get(norm(base))
    at = {"tipo": "treino_pericia", "pericia": canon or base}
    if not canon:
        at["nao_canonizada"] = True
    if esp:
        at["especializacao"] = esp
    return at


def classificar_atomo(texto, por_nome, pericias, classe_ctx=None):
    t = texto.strip()
    tn = norm(t)

    m = RE_ATRIB.match(t)
    if m:
        return {"tipo": "atributo", "attr": ATTR_CANON[m.group(1).lower()],
                "valor": int(m.group(2))}

    m = RE_NIVEL.match(t)
    if m:
        alvo = m.group(2).strip()
        if norm(alvo) == "personagem":
            return {"tipo": "nivel_personagem", "nivel": int(m.group(1))}
        return {"tipo": "nivel_classe", "classe": norm(alvo), "nivel": int(m.group(1))}

    m = RE_PROF.match(t)
    if m:
        return {"tipo": "proficiencia", "alvo": m.group(1).strip()}

    m = RE_DEVOTO.match(t)
    if m:
        return {"tipo": "devoto", "detalhe": m.group(1).strip()}

    m = RE_HABCLASSE.match(t)
    if m:
        return {"tipo": "habilidade_classe", "nome": m.group(1).strip()}

    if tn.startswith("lancar magias") or tn.startswith("conjurar"):
        return {"tipo": "conjuracao", "detalhe": t}

    # poder quantificado: "um poder de armadilha", "quatro outros poderes da Tormenta"
    if re.search(r"\bpoder(es)?\b", tn) and re.search(r"\bd[aeo]s?\s+\w", tn):
        g = re.search(r"\bd[aeo]s?\s+(.+)$", t)
        grupo = g.group(1).strip() if g else t
        qtd = 1
        for w in tn.split():
            if w in NUM:
                qtd = NUM[w]; break
        return {"tipo": "poder_quantificado", "quantidade": qtd, "grupo": grupo}

    if tn == "personagem" or tn in CLASSES:
        return {"tipo": "classe", "classe": t}
    if tn in CAMINHOS_ARCANISTA:
        return {"tipo": "caminho", "nome": t, "classe_base": "Arcanista"}

    # "X com a escola/arma escolhida" -> poder + nota
    com = None
    m = RE_COM_ESCOLHA.match(t)
    if m:
        base_nome, com = m.group(1).strip(), m.group(2).strip()
    else:
        base_nome = t

    ids = resolver_poder(base_nome, por_nome, classe_ctx)
    if ids:
        at = {"tipo": "poder", "nome": base_nome, "ref_ids": ids}
        if com:
            at["com"] = com
        return at

    return {"tipo": "livre", "texto": t}


def parse_clausula(clausula, por_nome, pericias, classe_ctx=None):
    """Uma cláusula (entre vírgulas) -> lista de grupos-AND."""
    t = clausula.strip()

    # narrativa livre: não fatiar
    if "conquistado" in norm(t):
        return [{"ou": [{"tipo": "livre", "texto": t}]}]

    # especial: "Canalizar Energia Positiva ou Negativa"
    m = re.match(r"^(Canalizar Energia)\s+(Positiva|Negativa)\s+ou\s+(Positiva|Negativa)$", t, re.I)
    if m:
        a = classificar_atomo(f"{m.group(1)} {m.group(2)}", por_nome, pericias, classe_ctx)
        b = classificar_atomo(f"{m.group(1)} {m.group(3)}", por_nome, pericias, classe_ctx)
        return [{"ou": [a, b]}]

    mt = RE_TREINO.match(t)
    if mt:
        resto = mt.group(1).strip()
        if re.search(r"\s+ou\s+", resto):                     # OR de perícias
            atoms = [classificar_pericia(x, pericias) for x in split_ou(resto)]
            return [{"ou": atoms}]
        # AND de perícias ("A e B") -> grupos separados
        skills = [s.strip() for s in re.split(r"\s+e\s+", resto) if s.strip()]
        return [{"ou": [classificar_pericia(s, pericias)]} for s in skills]

    if re.search(r"\s+ou\s+", t):                              # OR genérico
        atoms = [classificar_atomo(x, por_nome, pericias, classe_ctx) for x in split_ou(t)]
        return [{"ou": atoms}]

    return [{"ou": [classificar_atomo(t, por_nome, pericias, classe_ctx)]}]


def estruturar(pre_requisito, por_nome, pericias, classe_ctx=None):
    grupos = []
    for cl in split_virgulas(pre_requisito):
        grupos.extend(parse_clausula(cl, por_nome, pericias, classe_ctx))
    return grupos


# ---- runner + auditoria -----------------------------------------------------
def main():
    audit = "--audit" in sys.argv
    dc, dg, por_nome, pericias = carregar_indices()

    tot = livres = poderes_nao_res = 0
    livre_list, naores_list = [], []

    for arr in (dc, dg):
        for p in arr:
            pr = p.get("pre_requisito")
            if not pr:
                p.pop("pre_requisito_estruturado", None)
                continue
            classe_ctx = p.get("classe")
            estr = estruturar(pr, por_nome, pericias, classe_ctx)
            p["pre_requisito_estruturado"] = estr
            tot += 1
            for g in estr:
                for a in g["ou"]:
                    if a["tipo"] == "livre":
                        livres += 1
                        livre_list.append((p["nome"], a["texto"]))
                    if a["tipo"] == "poder" and not a.get("ref_ids"):
                        poderes_nao_res += 1
                        naores_list.append((p["nome"], a["nome"]))

    # auditoria
    print(f"Poderes com pré-requisito estruturado: {tot}")
    print(f"Átomos livres (não tipados): {livres}")
    print(f"Átomos poder sem ref resolvida: {poderes_nao_res}")
    if livre_list:
        print("\n--- LIVRES (revisar) ---")
        for nome, tx in livre_list:
            print(f"  [{nome}] {tx}")
    if naores_list:
        print("\n--- PODER NÃO RESOLVIDO ---")
        for nome, alvo in naores_list:
            print(f"  [{nome}] -> {alvo}")

    if not audit:
        json.dump(dc, open(ARQ_CLASSE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        json.dump(dg, open(ARQ_GERAIS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nGravado em {ARQ_CLASSE} e {ARQ_GERAIS}.")
    else:
        print("\n[--audit] nada gravado.")


if __name__ == "__main__":
    main()
