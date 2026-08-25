# -*- coding: utf-8 -*-
r"""Ferramenta de CONFERÊNCIA HTML dos Novos Equipamentos de Heróis de Arton
(Cap. 3 - Arsenal). Lê dados/equipamentos_herois.json e gera um HTML estático
para revisão visual antes da integração ao índice. NÃO toca no FAISS.
"""
import sys, io, json, html
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = Path(__file__).parent
IN = BASE / "dados" / "equipamentos_herois.json"
OUT = BASE / "equipamentos_herois.html"

d = json.load(open(IN, encoding="utf-8"))
esc = html.escape


def card(it, campos):
    linhas = "".join(
        f'<span class="f"><b>{esc(k)}:</b> {esc(str(it.get(v,"—")))}</span>'
        for k, v in campos if it.get(v))
    desc = esc(it.get("descricao", "") or "")
    return (f'<div class="card"><div class="nome">{esc(it["nome"])}</div>'
            f'<div class="stats">{linhas}</div>'
            f'<div class="desc">{desc}</div></div>')


secs = []
armas = d.get("armas", [])
secs.append(("Armas ({})".format(len(armas)), "".join(
    card(a, [("Prof","proficiencia"),("Empunhadura","empunhadura"),("Preço","preco"),
             ("Dano","dano"),("Crít","critico"),("Alcance","alcance"),
             ("Tipo","tipo_dano"),("Espaços","espacos")]) for a in armas)))

munis = d.get("municoes", [])
secs.append(("Munições especiais ({})".format(len(munis)), "".join(
    card(m, [("Preço","preco"),("Espaços","espacos")]) for m in munis)))

arms = d.get("armaduras_escudos", [])
secs.append(("Armaduras & Escudos ({})".format(len(arms)), "".join(
    card(a, [("Subcat","subcategoria"),("Preço","preco"),("Bônus Def","bonus_defesa"),
             ("Penalidade","penalidade"),("Espaços","espacos")]) for a in arms)))

gerais = d.get("itens_gerais", [])
secs.append(("Itens Gerais ({})".format(len(gerais)), "".join(
    card(g, [("Subcat","subcategoria"),("Preço","preco"),("Espaços","espacos")])
    for g in sorted(gerais, key=lambda x: (x["subcategoria"], x["nome"])))))

habs = d.get("habilidades_arma", [])
secs.append(("Novas Habilidades de Arma ({})".format(len(habs)), "".join(
    card(h, []) for h in habs)))

total = len(armas) + len(munis) + len(arms) + len(gerais) + len(habs)
corpo = "".join(f'<h2>{esc(t)}</h2><div class="grid">{c}</div>' for t, c in secs)

htmldoc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Novos Equipamentos (Heróis de Arton)</title>
<style>
 body{{font:14px/1.5 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#2a2140;border-bottom:2px solid #6b4fbb}}
 header h1{{margin:0;font-size:20px}} header .meta{{color:#b9a9e0;font-size:13px}}
 h2{{padding:8px 24px;margin:24px 0 0;color:#c9b6ff;border-bottom:1px solid #3a3550}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;padding:16px 24px}}
 .card{{background:#232329;border:1px solid #35353d;border-radius:8px;padding:12px}}
 .nome{{font-weight:700;font-size:15px;color:#fff;margin-bottom:6px}}
 .stats{{display:flex;flex-wrap:wrap;gap:4px 12px;margin-bottom:8px}}
 .f{{font-size:12px;color:#a9c8e0}} .f b{{color:#7fb0d8}}
 .desc{{font-size:13px;color:#d0d0d4;white-space:pre-wrap}}
</style></head><body>
<header><h1>Novos Equipamentos — Heróis de Arton (Cap. 3: Arsenal)</h1>
<div class="meta">fonte=herois-arton · {total} registros · Bases FORA do Cap 3 (por ora) · conferência pré-integração</div></header>
{corpo}
</body></html>"""

OUT.write_text(htmldoc, encoding="utf-8")
print(f"[OK] {total} registros -> {OUT}")
