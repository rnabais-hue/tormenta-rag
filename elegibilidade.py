# -*- coding: utf-8 -*-
"""
Stage C da família RELACIONAL de Poderes (ver README §11).

Deriva, para cada poder, um descritor de ELEGIBILIDADE — a dimensão de ACESSO
que os predicados do Stage B não capturam (categoria→quem acessa, conjuração,
devoção→deuses→devotos) — mais alguns FLAGS derivados dos predicados.

Regras de acesso por categoria:
    classe    -> só a própria classe
    combate   -> geral (qualquer classe)
    destino   -> geral (qualquer classe)
    tormenta  -> geral (tema Tormenta; qualquer classe)
    magia     -> conjuradores (classes com habilidade "Magias")
    concedido -> devoção: elegível quem PODE ser devoto de algum deus que concede
                 (join via poder.deuses -> deuses.json.devotos)

Campo gravado em cada poder:
    elegibilidade = {
      acesso: "classe"|"geral"|"tormenta"|"conjurador"|"devocao",
      classes: [...],            # classes que acessam pela REGRA DE ACESSO
      requer_conjuracao: bool,
      requer_devocao: bool,
      deuses: [...],             # (concedido) deuses que concedem
      caminhos: [...],           # (arcanista) caminho exigido pelo predicado, se houver
      # flags derivados dos predicados (Stage B):
      nivel_minimo: int|null,    # maior nível exigido (classe própria ou personagem)
      atributos_minimos: {attr:valor},
    }

Depende de: pre_requisito_estruturado (rode estruturar_prereqs.py antes).
Rode:  python elegibilidade.py            (grava + audita)
       python elegibilidade.py --audit    (só audita)
"""
import json, sys, re, unicodedata, io

ARQ_CLASSE = "dados/poderes_classe.json"
ARQ_GERAIS = "dados/poderes_gerais.json"
ARQ_CLASSES = "dados/classes.json"
ARQ_DEUSES = "dados/deuses.json"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def base_dev(s):
    """Normaliza p/ casar devoto: sem acento + dobra plural 'ões'→'ão' (igual perguntar.py)."""
    return norm(s).replace("oes", "ao")


def casa_devoto(nome, devoto):
    a, b = base_dev(nome), base_dev(devoto)
    return len(a) >= 3 and (b.startswith(a) or a.startswith(b))


def devotos_amplo(deus):
    txt = norm(" ".join(deus.get("devotos") or []))
    return bool(re.search(r"quaisquer|todas as classes|aventureiros", txt))


def carregar():
    dc = json.load(open(ARQ_CLASSE, encoding="utf-8"))
    dg = json.load(open(ARQ_GERAIS, encoding="utf-8"))
    classes = json.load(open(ARQ_CLASSES, encoding="utf-8"))
    deuses = json.load(open(ARQ_DEUSES, encoding="utf-8"))
    return dc, dg, classes, deuses


def flags_derivados(poder):
    """Extrai nível mínimo e atributos mínimos dos predicados (grupos AND simples)."""
    nivel_min = None
    attrs = {}
    caminhos = []
    for g in poder.get("pre_requisito_estruturado", []):
        ou = g["ou"]
        if len(ou) != 1:                     # grupo OR: ambíguo p/ mínimo — ignora
            for a in ou:
                if a["tipo"] == "caminho":
                    caminhos.append(a["nome"])
            continue
        a = ou[0]
        if a["tipo"] == "atributo":
            attrs[a["attr"]] = max(attrs.get(a["attr"], 0), a["valor"])
        elif a["tipo"] == "nivel_classe":
            # nível na PRÓPRIA classe do poder (ou personagem via outro ramo)
            if a["classe"] == norm(poder.get("classe", "")) or not poder.get("classe"):
                nivel_min = max(nivel_min or 0, a["nivel"])
        elif a["tipo"] == "nivel_personagem":
            nivel_min = max(nivel_min or 0, a["nivel"])
        elif a["tipo"] == "caminho":
            caminhos.append(a["nome"])
    return nivel_min, attrs, sorted(set(caminhos))


def classes_devoto(deus, todas):
    """Classes (das 14) que podem ser devotas deste deus."""
    if devotos_amplo(deus):
        return set(todas)
    out = {"Clérigo"}                        # clérigos seguem qualquer deus
    for c in todas:
        if any(casa_devoto(c, dv) for dv in (deus.get("devotos") or [])):
            out.add(c)
    return out


def main():
    audit = "--audit" in sys.argv
    dc, dg, classes, deuses = carregar()

    TODAS = [c["nome"] for c in classes]                       # 14 classes
    CONJ = [c["nome"] for c in classes
            if "Magias" in {h["nome"] for h in c.get("habilidades", [])}]
    deus_por_nome = {norm(d["nome"]): d for d in deuses}

    resumo = {}
    for p in (dc + dg):
        cat = p["categoria"]
        nivel_min, attrs, caminhos = flags_derivados(p)
        el = {"acesso": None, "classes": [], "requer_conjuracao": False,
              "requer_devocao": False, "deuses": [],
              "caminhos": caminhos, "nivel_minimo": nivel_min,
              "atributos_minimos": attrs}

        if cat == "classe":
            el["acesso"] = "classe"
            el["classes"] = [p["classe"]]
        elif cat in ("combate", "destino"):
            el["acesso"] = "geral"
            el["classes"] = list(TODAS)
        elif cat == "tormenta":
            el["acesso"] = "tormenta"
            el["classes"] = list(TODAS)
        elif cat == "magia":
            el["acesso"] = "conjurador"
            el["requer_conjuracao"] = True
            el["classes"] = list(CONJ)
        elif cat == "concedido":
            el["acesso"] = "devocao"
            el["requer_devocao"] = True
            el["deuses"] = list(p.get("deuses") or [])
            acc = set()
            for dn in el["deuses"]:
                d = deus_por_nome.get(norm(dn))
                if d:
                    acc |= classes_devoto(d, TODAS)
            el["classes"] = [c for c in TODAS if c in acc]      # ordem canônica
        else:
            el["acesso"] = "outro"
            el["classes"] = list(TODAS)

        p["elegibilidade"] = el
        resumo[cat] = resumo.get(cat, 0) + 1

    print("Poderes com elegibilidade derivada por categoria:")
    for k in sorted(resumo):
        print(f"  {k:11} {resumo[k]}")
    print(f"Conjuradores: {CONJ}")

    # amostras auditáveis
    print("\n--- amostras ---")
    amostra = {"classe": "Golpe Divino", "combate": "Esquiva", "magia": "Magia Acelerada",
               "concedido": "Afinidade com a Tormenta", "tormenta": "Corpo Aberrante",
               "destino": "Vontade de Ferro"}
    idx = {p["nome"]: p for p in (dc + dg)}
    for cat, nome in amostra.items():
        p = idx.get(nome)
        if p:
            e = p["elegibilidade"]
            print(f"  [{cat}] {nome}: acesso={e['acesso']} classes={e['classes']}"
                  f" conj={e['requer_conjuracao']} devo={e['requer_devocao']}"
                  f" deuses={e['deuses']} nivel_min={e['nivel_minimo']} attrs={e['atributos_minimos']}")

    # sanidade: concedido de deus amplo deve dar todas as 14
    afin = idx.get("Afinidade com a Tormenta")
    if afin:
        assert len(afin["elegibilidade"]["classes"]) == len(TODAS), "Aharadak deveria ser amplo"
        print("\nOK: concedido de Aharadak (amplo) elegível a todas as 14 classes.")

    if not audit:
        json.dump(dc, open(ARQ_CLASSE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        json.dump(dg, open(ARQ_GERAIS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("\nGravado.")
    else:
        print("\n[--audit] nada gravado.")


if __name__ == "__main__":
    main()
