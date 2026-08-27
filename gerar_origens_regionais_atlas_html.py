# -*- coding: utf-8 -*-
r"""Conferência das ORIGENS REGIONAIS (Atlas de Arton, Apêndice)."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "origens_regionais_atlas.json"
OUT = BASE / "origens_regionais_atlas.html"


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    cards = "".join(f"""<section class="o">
  <h3>{esc(o['nome'])} <span class="reg">{esc(o['regiao'] or '—')}</span> <span class="pg">pág. {o['pagina']}</span></h3>
  <div class="it"><b>Itens:</b> {esc(o['itens'])}</div>
  <div class="be"><b>Benefício:</b> {esc(o['beneficio'])}</div>
  {('<div class="pe">perícias: ' + esc(', '.join(o['pericias'])) + '</div>') if o['pericias'] else ''}
</section>""" for o in sorted(d["origens"], key=lambda o: o["nome"]))
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Origens Regionais (Atlas de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#2a3a2a;border-bottom:2px solid #4f9b6b;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#a9e0bb;font-size:13px}}
 .intro{{padding:14px 24px;color:#cfcfd6;border-bottom:1px solid #33313c;white-space:pre-wrap}}
 .o{{border-bottom:1px solid #2c2a30;padding:11px 24px}}
 h3{{margin:0 0 5px;color:#b6ffca;font-size:15px}}
 .reg{{font-size:12px;background:#2a4a3a;color:#a0e0c0;padding:1px 8px;border-radius:8px}}
 .pg{{font-size:12px;color:#82a08a;font-weight:400}}
 .it{{color:#d0d0c0;margin-bottom:3px}} .be{{color:#cfcfd6}} .it b,.be b{{color:#fff}}
 .pe{{font-size:12px;color:#9ac0aa;margin-top:3px}}
</style></head><body>
<header><h1>Origens Regionais — Atlas de Arton (Apêndice)</h1>
<div class="meta">fonte=atlas-arton · {d['total']} origens · págs 472–483 · conferência pré-integração</div></header>
<div class="intro"><b>Introdução:</b> {esc(d['introducao'])}</div>
{cards}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total']} origens, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
