# -*- coding: utf-8 -*-
r"""
Derivação: ATRIBUTO-CHAVE por classe (camada de inferência com evidência, §11).

Problema (README §10/§11): as classes do núcleo NÃO trazem um campo "Atributo
Principal" no stat block (só PV/PM/Perícias/Proficiências). Logo, "qual o atributo
do paladino?" não tinha resposta explícita no chunk de visão geral e o LLM chutava
(puxava um chunk genérico do Cap. 5).

A verdade do livro:
  - Os CONJURADORES e o PALADINO TÊM o atributo-chave DEFINIDO no texto de uma
    habilidade real de classe — via "atributo-chave para lançar magias é X" (Bardo,
    Clérigo, Druida), via o Caminho (Arcanista: Bruxo/Mago = Inteligência,
    Feiticeiro = Carisma) ou via "soma seu X no total de PM" (Paladino: Carisma,
    em Abençoado; reforçado por Golpe Divino usar Carisma).
  - As 8 classes MARCIAIS restantes NÃO imprimem um atributo-chave. Para elas o
    honesto é dizer isso — e, opcionalmente, oferecer um palpite DERIVADO (contagem
    de menções de atributo nas habilidades) SEMPRE rotulado como inferência, nunca
    como regra.

Regra de ouro (§11): derivar COM EVIDÊNCIA (auditável) e não confundir inferência
com regra impressa. As habilidades "Poder de X" são LISTAS de poderes (ruído) e
são excluídas da análise.

Uso:
  python derivar_atributo_chave.py            # grava o campo atributo_chave em classes.json
  python derivar_atributo_chave.py --dry      # só mostra, não grava
"""

import argparse
import json
import re
import sys
import io
import collections
from pathlib import Path

BASE = Path(__file__).parent
ARQ_CLASSES = BASE / "dados" / "classes.json"

ATTRS = ["Força", "Destreza", "Constituição", "Inteligência", "Sabedoria", "Carisma"]
_ABREV = {"For": "Força", "Des": "Destreza", "Con": "Constituição",
          "Int": "Inteligência", "Sab": "Sabedoria", "Car": "Carisma"}
_A = "(Força|Destreza|Constituição|Inteligência|Sabedoria|Carisma)"

# Sinais do LIVRO (dentro de uma habilidade real de classe):
_RE_CHAVE = re.compile(r"atributo-chave\b.{0,25}?(?:é|para lançar magias é)\s+" + _A, re.I)
_RE_PM = re.compile(r"soma (?:seu|sua) " + _A + r"\b.{0,45}(?:pontos de mana|total de PM|no seu total)", re.I)
_RE_CAMINHO = re.compile(r"atributo-chave.{0,45}Caminho", re.I)
# Para o Arcanista: cada bullet do Caminho ("• Bruxo ... atributo-chave ... é X")
_RE_BULLET = re.compile(r"[•\-]\s*(Bruxo|Mago|Feiticeiro)\b(.*?)(?=[•\-]\s*(?:Bruxo|Mago|Feiticeiro)\b|$)", re.S)
_RE_BULLET_ATTR = re.compile(r"atributo-chave.{0,20}?(?:é|para magias é)\s+" + _A, re.I)


def _habs_reais(classe):
    """Habilidades de classe EXCETO as listas 'Poder de X' (ruído)."""
    return [h for h in classe.get("habilidades", []) if not h["nome"].startswith("Poder de")]


def _caminho_arcanista(classe):
    """Mapa caminho→atributo do Arcanista, lido dos bullets de 'Caminho do Arcanista'."""
    for h in _habs_reais(classe):
        if "Caminho" in h["nome"]:
            out = {}
            for cam, corpo in _RE_BULLET.findall(h["efeito"]):
                m = _RE_BULLET_ATTR.search(corpo)
                if m:
                    out[cam] = m.group(1)
            if out:
                return out, h["nome"]
    return None, None


def _inferir(classe):
    """Palpite por contagem de menções de atributo nas habilidades reais (evidência)."""
    cnt = collections.Counter()
    pats = {a: re.compile(r"\b(" + re.escape(a) + r"|" +
                          re.escape(next(k for k, v in _ABREV.items() if v == a)) + r")\b")
            for a in ATTRS}
    for h in _habs_reais(classe):
        for a, p in pats.items():
            n = len(p.findall(h["efeito"]))
            if n:
                cnt[a] += n
    if not cnt:
        return None
    top, n = cnt.most_common(1)[0]
    return {"atributo": top, "contagem": dict(cnt.most_common())}


def derivar(classe):
    ev = []
    attrs = set()
    # Arcanista: por Caminho
    mapa, hcam = _caminho_arcanista(classe)
    if mapa:
        return {
            "definido_no_livro": True,
            "atributo": "por Caminho",
            "opcoes": mapa,                      # {'Bruxo':'Inteligência', ...}
            "evidencia": [f"{hcam}: o atributo-chave é definido pelo Caminho — "
                          + ", ".join(f"{k} = {v}" for k, v in mapa.items())],
        }
    # Demais: atributo-chave explícito ou 'soma X no PM' em habilidade real
    for h in _habs_reais(classe):
        for m in _RE_CHAVE.finditer(h["efeito"]):
            attrs.add(m.group(1)); ev.append(f"{h['nome']}: “atributo-chave … é {m.group(1)}”")
        for m in _RE_PM.finditer(h["efeito"]):
            attrs.add(m.group(1)); ev.append(f"{h['nome']}: soma {m.group(1)} no total de PM")
    if len(attrs) == 1:
        return {"definido_no_livro": True, "atributo": next(iter(attrs)),
                "evidencia": ev}
    # Não definido no livro → inferência rotulada
    return {"definido_no_livro": False, "atributo": None,
            "nota": "O livro não define um atributo-chave para esta classe.",
            "inferido": _inferir(classe)}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="não grava, só mostra")
    args = ap.parse_args()

    classes = json.loads(ARQ_CLASSES.read_text(encoding="utf-8"))
    for c in classes:
        c["atributo_chave"] = derivar(c)

    for c in classes:
        ac = c["atributo_chave"]
        if ac["definido_no_livro"]:
            alvo = ac.get("atributo")
            if alvo == "por Caminho":
                alvo = "por Caminho (" + ", ".join(f"{k}={v}" for k, v in ac["opcoes"].items()) + ")"
            print(f"[livro]  {c['nome']:12} → {alvo}")
        else:
            inf = ac.get("inferido") or {}
            print(f"[—]      {c['nome']:12} → não impresso (inferido: {inf.get('atributo')})")

    if not args.dry:
        ARQ_CLASSES.write_text(json.dumps(classes, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nGravado atributo_chave em {ARQ_CLASSES.name} ({len(classes)} classes).")
    else:
        print("\n(dry-run — nada gravado)")


if __name__ == "__main__":
    main()
