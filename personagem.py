# -*- coding: utf-8 -*-
"""
Stage D da família RELACIONAL de Poderes (ver README §11).

Motor que AVALIA os predicados (Stage B) + elegibilidade (Stage C) para um
PERSONAGEM concreto e responde:
  - `avaliar(poder)`  -> (elegível?, faltando[])  explicando o que falta;
  - `disponiveis()`   -> poderes que o personagem PODE pegar agora;
  - `arvore(nome)`    -> árvore de pré-requisitos de um poder-alvo (planejamento).

Personagem = dict:
  { classe, nivel, caminho?, conjurador?(auto), deus?, raca?,
    atributos:{For,Des,Con,Int,Sab,Car}, pericias:[...], poderes:[...] }

Uso:
  python personagem.py                      # demo (Paladino 6 devoto de Khalmyr)
  python personagem.py --arquivo p.json     # avalia um personagem de arquivo
  python personagem.py --arvore "Ripostar"  # árvore de pré-requisitos do poder
"""
import json, sys, os, re, unicodedata, io
from pathlib import Path

_BASE = Path(__file__).parent
ARQ_CLASSE = str(_BASE / "dados/poderes_classe.json")
ARQ_GERAIS = str(_BASE / "dados/poderes_gerais.json")
ARQ_CLASSES = str(_BASE / "dados/classes.json")
ARQ_DEUSES = str(_BASE / "dados/deuses.json")


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def base_dev(s):
    return norm(s).replace("oes", "ao")


def casa_devoto(nome, devoto):
    a, b = base_dev(nome), base_dev(devoto)
    return len(a) >= 3 and (b.startswith(a) or a.startswith(b))


def devotos_amplo(deus):
    txt = norm(" ".join(deus.get("devotos") or []))
    return bool(re.search(r"quaisquer|todas as classes|aventureiros", txt))


class Mundo:
    """Carrega catálogos e monta índices de consulta."""
    def __init__(self):
        self.poderes = (json.load(open(ARQ_CLASSE, encoding="utf-8"))
                        + json.load(open(ARQ_GERAIS, encoding="utf-8")))
        self.classes = json.load(open(ARQ_CLASSES, encoding="utf-8"))
        self.deuses = json.load(open(ARQ_DEUSES, encoding="utf-8"))
        self.por_id = {p["id"]: p for p in self.poderes}
        self.por_nome = {}
        for p in self.poderes:
            self.por_nome.setdefault(norm(p["nome"]), []).append(p)
        self.conjuradores = {c["nome"] for c in self.classes
                             if "Magias" in {h["nome"] for h in c.get("habilidades", [])}}
        self.deus_por_nome = {norm(d["nome"]): d for d in self.deuses}

    def acha(self, nome):
        lst = self.por_nome.get(norm(nome), [])
        return lst[0] if lst else None

    def poderes_por_acesso(self, classe, nivel=None, deus=None):
        """Poderes ACESSÍVEIS a uma classe pela elegibilidade (Stage C), sem exigir
        um personagem completo (para 'que poderes um paladino pode pegar'). Filtra
        por nível mínimo (se dado) e, nos concedidos, pelo deus (se dado)."""
        cn = norm(classe)
        out = []
        for p in self.poderes:
            el = p.get("elegibilidade", {})
            if cn not in [norm(c) for c in el.get("classes", [])]:
                continue
            if nivel is not None and el.get("nivel_minimo") and el["nivel_minimo"] > nivel:
                continue
            if p["categoria"] == "concedido":
                if not deus:
                    continue                       # sem deus escolhido: não lista concedidos
                if norm(deus) not in [norm(x) for x in (p.get("deuses") or [])]:
                    continue
            out.append(p)
        return out


class Personagem:
    def __init__(self, mundo, d):
        self.m = mundo
        self.classe = d.get("classe")
        self.nivel = int(d.get("nivel", 1))
        self.caminho = d.get("caminho")
        self.deus = d.get("deus")
        self.raca = d.get("raca")
        self.atributos = {k: int(v) for k, v in (d.get("atributos") or {}).items()}
        self.pericias = {norm(p) for p in (d.get("pericias") or [])}
        # poderes possuídos: guarda normalizado + resolve categorias
        self.poderes = {norm(p) for p in (d.get("poderes") or [])}
        self.poder_obj = [self.m.acha(p) for p in (d.get("poderes") or [])]
        self.poder_obj = [p for p in self.poder_obj if p]
        self.conjurador = bool(d.get("conjurador",
                                     self.classe in self.m.conjuradores))

    # ---- checagem de devoção (reusa a semântica do filtro de deuses) --------
    def pode_ser_devoto(self, nome_deus):
        d = self.m.deus_por_nome.get(norm(nome_deus))
        if not d:
            return False
        if norm(self.classe or "") == "clerigo" or norm(self.raca or "") == "humano":
            return True                       # clérigo/humano seguem qualquer deus
        if devotos_amplo(d):
            return True
        alvos = [x for x in (self.classe, self.raca) if x]
        return any(casa_devoto(a, dv) for a in alvos
                   for dv in (d.get("devotos") or []))

    def eh_devoto_de_algum(self, deuses):
        """Character já é devoto de um deus da lista (precisa ter escolhido deus)."""
        if not self.deus:
            return False
        return any(norm(self.deus) == norm(x) for x in deuses)

    # ---- avaliação de um átomo de predicado ---------------------------------
    def _atomo_ok(self, a):
        t = a["tipo"]
        if t == "atributo":
            return self.atributos.get(a["attr"], 0) >= a["valor"]
        if t == "nivel_classe":
            return norm(self.classe or "") == a["classe"] and self.nivel >= a["nivel"]
        if t == "nivel_personagem":
            return self.nivel >= a["nivel"]
        if t == "treino_pericia":
            if a.get("escolhida"):
                return True                   # "na perícia escolhida" — sempre ok
            return norm(a["pericia"]) in self.pericias
        if t == "proficiencia":
            return None                       # não modelado → indeterminado
        if t == "poder":
            if any(rid in {p["id"] for p in self.poder_obj} for rid in a.get("ref_ids", [])):
                return True
            return norm(a["nome"]) in self.poderes
        if t == "caminho":
            return norm(self.caminho or "") == norm(a["nome"])
        if t == "classe":
            return norm(self.classe or "") == norm(a["classe"])
        if t == "poder_quantificado":
            return self._conta_grupo(a["grupo"]) >= a["quantidade"]
        if t == "devoto":
            return bool(self.deus)            # é devoto de alguém
        if t in ("conjuracao", "habilidade_classe"):
            return self.conjurador
        if t == "livre":
            return None                       # não avaliável automaticamente
        return None

    def _conta_grupo(self, grupo):
        g = norm(grupo)
        n = 0
        for p in self.poder_obj:
            if g == "tormenta" and p.get("categoria") == "tormenta":
                n += 1
            elif norm(p["nome"]).startswith(g + ":"):   # Armadilha:/Missa:/Música:
                n += 1
        return n

    def _descreve(self, a):
        t = a["tipo"]
        return {
            "atributo": lambda: f"{a['attr']} {a['valor']}",
            "nivel_classe": lambda: f"{a['nivel']}º nível de {a['classe']}",
            "nivel_personagem": lambda: f"{a['nivel']}º nível de personagem",
            "treino_pericia": lambda: f"treinado em {a['pericia']}"
                + (f" ({a['especializacao']})" if a.get("especializacao") else ""),
            "proficiencia": lambda: f"proficiência com {a['alvo']}",
            "poder": lambda: f"poder {a['nome']}",
            "caminho": lambda: f"caminho {a['nome']}",
            "classe": lambda: f"ser {a['classe']}",
            "poder_quantificado": lambda: f"{a['quantidade']} poder(es) de {a['grupo']}",
            "devoto": lambda: f"devoto ({a['detalhe']})",
            "conjuracao": lambda: a.get("detalhe", "conjurar magias"),
            "habilidade_classe": lambda: f"habilidade de classe {a['nome']}",
            "livre": lambda: a["texto"],
        }.get(t, lambda: t)()

    # ---- avaliação de um poder ----------------------------------------------
    def avaliar(self, poder):
        faltando, indeterminado = [], []
        el = poder.get("elegibilidade", {})

        # 1) ACESSO (Stage C)
        if el.get("acesso") == "classe":
            if norm(self.classe or "") != norm(poder.get("classe", "")):
                faltando.append(f"ser da classe {poder.get('classe')}")
        elif el.get("requer_conjuracao") and not self.conjurador:
            faltando.append("ser conjurador (habilidade Magias)")
        elif el.get("requer_devocao"):
            deuses = el.get("deuses", [])
            if not self.eh_devoto_de_algum(deuses):
                # pode ser devoto? (potencial) vs já é devoto (efetivo)
                pot = [d for d in deuses if self.pode_ser_devoto(d)]
                if pot:
                    faltando.append(f"ser devoto de {', '.join(deuses)} (pode: {', '.join(pot)})")
                else:
                    faltando.append(f"ser devoto de {', '.join(deuses)} (classe/raça não pode)")

        # 2) PREDICADOS (Stage B) — cada grupo AND precisa de ao menos 1 OR verdadeiro
        for g in poder.get("pre_requisito_estruturado", []):
            resultados = [self._atomo_ok(a) for a in g["ou"]]
            if any(r is True for r in resultados):
                continue
            desc = " ou ".join(self._descreve(a) for a in g["ou"])
            if all(r is None for r in resultados):
                indeterminado.append(desc)
            else:
                faltando.append(desc)

        # já possui?
        ja_tem = norm(poder["nome"]) in self.poderes
        elegivel = (not faltando) and (not ja_tem)
        return {"elegivel": elegivel, "ja_tem": ja_tem,
                "faltando": faltando, "indeterminado": indeterminado}

    def disponiveis(self):
        out = []
        for p in self.m.poderes:
            r = self.avaliar(p)
            if r["elegivel"]:
                out.append((p, r["indeterminado"]))
        return out

    # ---- árvore de pré-requisitos (planejamento) ----------------------------
    def arvore_linhas(self, nome, prof=0, visto=None, linhas=None):
        """Monta a árvore recursiva de pré-requisitos como lista de strings."""
        visto = visto if visto is not None else set()
        linhas = linhas if linhas is not None else []
        p = self.m.acha(nome)
        if not p:
            linhas.append("  " * prof + f"? {nome} (não encontrado)")
            return linhas
        if p["id"] in visto:
            linhas.append("  " * prof + f"↻ {p['nome']}")
            return linhas
        visto.add(p["id"])
        marca = "✔" if norm(p["nome"]) in self.poderes else " "
        linhas.append("  " * prof + f"[{marca}] {p['nome']}"
                      + (f"  «{p['pre_requisito']}»" if p.get("pre_requisito") else ""))
        for g in p.get("pre_requisito_estruturado", []):
            for a in g["ou"]:
                if a["tipo"] == "poder":
                    self.arvore_linhas(a["nome"], prof + 1, visto, linhas)
        return linhas

    def arvore(self, nome):
        for ln in self.arvore_linhas(nome):
            print(ln)

    # ---- blocos determinísticos para o RAG (perguntar.py) -------------------
    def bloco_prereq(self, nome):
        """Texto factual (efeito + elegibilidade + árvore) de UM poder, para o LLM
        redigir sem inventar pré-requisitos. Retorna (texto, poder) ou (None, None)."""
        p = self.m.acha(nome)
        if not p:
            return None, None
        el = p.get("elegibilidade", {})
        L = [f"PODER: {p['nome']}  (categoria: {p['categoria']}"
             + (f", classe {p['classe']}" if p.get("classe") else "") + f", pág. {p['pagina']})",
             f"Efeito: {p['efeito']}"]
        if p.get("pre_requisito"):
            L.append(f"Pré-requisito (texto do livro): {p['pre_requisito']}")
        else:
            L.append("Pré-requisito: nenhum.")
        acesso = el.get("acesso")
        if acesso == "classe":
            L.append(f"Quem pode pegar: apenas a classe {el['classes'][0]}.")
        elif acesso == "conjurador":
            L.append(f"Quem pode pegar: conjuradores ({', '.join(el['classes'])}).")
        elif acesso == "devocao":
            L.append(f"Quem pode pegar: devotos de {', '.join(el.get('deuses') or [])}"
                     f" (classes: {', '.join(el['classes'])}).")
        elif acesso in ("geral", "tormenta"):
            L.append("Quem pode pegar: qualquer classe (poder geral).")
        arv = self.arvore_linhas(p["nome"])
        if len(arv) > 1:
            L.append("Cadeia de pré-requisitos (poder → do que depende):")
            L.extend("  " + x.strip() for x in arv)
        return "\n".join(L), p

    def bloco_elegiveis(self, limite_cat=40):
        """Lista os poderes que o personagem PODE pegar agora, agrupados por
        categoria. Texto determinístico para o LLM apresentar."""
        disp = self.disponiveis()
        por_cat = {}
        for p, indet in disp:
            por_cat.setdefault(p["categoria"], []).append((p["nome"], indet))
        L = [f"PODERES QUE {self.classe} nível {self.nivel}"
             + (f" devoto de {self.deus}" if self.deus else "")
             + f" PODE PEGAR AGORA ({len(disp)} no total):"]
        for cat in sorted(por_cat):
            nomes = sorted(por_cat[cat])
            L.append(f"\n[{cat}] ({len(nomes)})")
            for nome, indet in nomes[:limite_cat]:
                extra = f"  (verificar: {'; '.join(indet)})" if indet else ""
                L.append(f"  - {nome}{extra}")
        return "\n".join(L), len(disp)


def bloco_overview(mundo, classe, nivel=None, deus=None, limite_cat=40):
    """Texto determinístico: poderes acessíveis a uma CLASSE (Stage C), agrupados
    por categoria. Para o LLM apresentar em 'que poderes um X pode pegar'."""
    ps = mundo.poderes_por_acesso(classe, nivel, deus)
    por_cat = {}
    for p in ps:
        por_cat.setdefault(p["categoria"], []).append(p)
    cab = f"PODERES ACESSÍVEIS À CLASSE {classe}"
    if nivel is not None:
        cab += f" (até nível {nivel})"
    if deus:
        cab += f", devoto de {deus}"
    L = [cab + f" — {len(ps)} no total:"]
    if any(p["categoria"] == "concedido" for p in mundo.poderes) and not deus:
        L.append("(Poderes concedidos não listados: dependem de qual deus o personagem cultua.)")
    for cat in sorted(por_cat):
        itens = sorted(por_cat[cat], key=lambda p: p["nome"])
        L.append(f"\n[{cat}] ({len(itens)})")
        for p in itens[:limite_cat]:
            nm = p["elegibilidade"].get("nivel_minimo")
            req = f"  (a partir do nível {nm})" if nm else ""
            L.append(f"  - {p['nome']}{req}")
    return "\n".join(L), len(ps)


# ---- CLI --------------------------------------------------------------------
DEMO = {"classe": "Paladino", "nivel": 6, "raca": "Humano", "deus": "Khalmyr",
        "atributos": {"For": 3, "Des": 1, "Con": 2, "Int": 1, "Sab": 2, "Car": 3},
        "pericias": ["Luta", "Diplomacia", "Intimidação"],
        "poderes": []}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    m = Mundo()
    if "--arvore" in sys.argv:
        nome = sys.argv[sys.argv.index("--arvore") + 1]
        Personagem(m, DEMO).arvore(nome)
        return
    if "--arquivo" in sys.argv:
        d = json.load(open(sys.argv[sys.argv.index("--arquivo") + 1], encoding="utf-8"))
    else:
        d = DEMO
    pj = Personagem(m, d)
    print(f"Personagem: {pj.classe} nível {pj.nivel}"
          f"{' ('+pj.caminho+')' if pj.caminho else ''}"
          f"{' devoto de '+pj.deus if pj.deus else ''}"
          f" | conjurador={pj.conjurador}")
    print(f"Atributos: {pj.atributos} | Perícias: {sorted(pj.pericias)}")
    disp = pj.disponiveis()
    print(f"\n=== {len(disp)} poderes disponíveis AGORA ===")
    por_cat = {}
    for p, indet in disp:
        por_cat.setdefault(p["categoria"], []).append((p["nome"], indet))
    for cat in sorted(por_cat):
        nomes = por_cat[cat]
        print(f"\n[{cat}] ({len(nomes)})")
        for nome, indet in sorted(nomes):
            extra = f"  (verificar: {'; '.join(indet)})" if indet else ""
            print(f"  • {nome}{extra}")


if __name__ == "__main__":
    main()
