# -*- coding: utf-8 -*-
r"""Ferramenta de conferência dos PAPÉIS NO GRUPO (Heróis de Arton, Cap. 4).

Lê dados/papeis_grupo_herois.json e gera papeis_grupo_herois.html (offline, dois
cliques) para cruzar cada papel com a página do livro antes de integrar ao índice.
"""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "papeis_grupo_herois.json"
OUT = BASE / "papeis_grupo_herois.html"


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    cards = []
    for p in d["papeis"]:
        cards.append(f"""<section class="pl">
  <h2>{esc(p['nome'])} <span class="pg">pág. {p['pagina']}</span></h2>
  <div class="desc">{esc(p['descricao'])}</div>
  <div class="benef"><b>Benefício:</b> {esc(p['beneficio'])}</div>
</section>""")
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Papéis no Grupo (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#21402a;border-bottom:2px solid #4f9b6b;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#a9e0b9;font-size:13px}}
 .intro{{padding:14px 24px;color:#cfcfd6;border-bottom:1px solid #33313c;white-space:pre-wrap}}
 .pl{{border-bottom:1px solid #33313c;padding:16px 24px}}
 h2{{margin:0 0 8px;color:#b6ffca;font-size:17px}} .pg{{font-size:12px;color:#82a08a;font-weight:400}}
 .desc{{color:#cfcfd6;margin-bottom:8px;white-space:pre-wrap}}
 .benef{{color:#e0d0b0;background:#2a2418;border-left:3px solid #b08a3a;padding:6px 10px}}
 .benef b{{color:#fff}}
</style></head><body>
<header><h1>Papéis no Grupo — Heróis de Arton (Cap. 4)</h1>
<div class="meta">fonte=herois-arton · {d['total']} papéis · pág. {d['pagina']}+ · conferência pré-integração</div></header>
<div class="intro"><b>Introdução:</b> {esc(d['introducao'])}</div>
{''.join(cards)}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({len(d['papeis'])} papéis, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
