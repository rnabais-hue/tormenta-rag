# -*- coding: utf-8 -*-
r"""Stage A dos PODERES: explode as listas "Poder de <Classe>" (já extraídas em
dados/classes.json) em nós de poder individuais.

Cada poder de classe é um bullet "• Nome. Efeito [Pré-requisito: ...]".
Saída: um nó por poder com {nome, categoria="classe", classe, efeito,
pre_requisito(TEXTO), fonte, pagina}. Pré-requisito fica como TEXTO nesta fase
(estruturar em predicado é Stage B).

Lê dados/classes.json; escreve poderes_classe.json. Não toca no índice.
"""
import sys, io, json, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CLASSES = Path(__file__).parent / "dados" / "classes.json"
OUT = Path(__file__).parent / "dados" / "poderes_classe.json"


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def extrair_pre(efeito):
    """Separa 'Pré-requisito(s): X' (texto) do efeito. Devolve (efeito, pre|None)."""
    m = re.search(r"Pré-requisitos?:\s*([^.]+)", efeito)
    if not m:
        return efeito.strip(), None
    pre = m.group(1).strip()
    efeito = re.sub(r"\s*Pré-requisitos?:\s*[^.]+\.?", "", efeito).strip()
    return efeito, pre


def poderes_de_lista(efeito_lista, classe, pagina):
    """Explode o efeito de 'Poder de <Classe>' em nós. Um fragmento é um NOVO
    poder se o nome (antes do 1º ponto) tem <=6 palavras; senão é um sub-bullet
    de regra e é anexado ao poder anterior."""
    frags = [f.strip(" \t\n") for f in efeito_lista.split("•")]
    poderes = []
    for frag in frags[1:]:                         # frags[0] = intro
        if not frag:
            continue
        nome, _, efeito = frag.partition(".")
        nome = nome.strip()
        if len(nome.split()) > 6 or not efeito.strip():   # sub-bullet de regra
            if poderes:
                poderes[-1]["efeito"] += " • " + frag
            continue
        poderes.append({
            "id": f"poder:{slug(classe)}:{slug(nome)}",
            "tipo": "poder", "categoria": "classe", "classe": classe,
            "nome": nome, "efeito": efeito.strip(), "pre_requisito": None,
            "fonte": "nucleo", "pagina": pagina,
        })
    # extrai pré-requisito de cada poder (depois de mesclar sub-bullets)
    for p in poderes:
        p["efeito"], p["pre_requisito"] = extrair_pre(p["efeito"])
    return poderes


def main():
    classes = json.loads(CLASSES.read_text(encoding="utf-8"))
    poderes = []
    for c in classes:
        pod = next((h for h in c["habilidades"]
                    if h["nome"].lower().startswith("poder de")), None)
        if not pod:
            print(f"  ! {c['nome']}: sem 'Poder de ...'")
            continue
        novos = poderes_de_lista(pod["efeito"], c["nome"], c["pagina"])
        poderes.extend(novos)
        print(f"- {c['nome']:<11} {len(novos):>2} poderes de classe")
    OUT.write_text(json.dumps(poderes, ensure_ascii=False, indent=2), encoding="utf-8")
    com_pre = sum(1 for p in poderes if p["pre_requisito"])
    print(f"\nTotal: {len(poderes)} poderes de classe -> {OUT.name} "
          f"({com_pre} com pré-requisito)")


if __name__ == "__main__":
    main()
