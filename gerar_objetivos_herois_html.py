# -*- coding: utf-8 -*-
r"""Ferramenta de conferência dos OBJETIVOS HEROICOS (Heróis de Arton, Cap. 4)."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "objetivos_herois.json"
OUT = BASE / "objetivos_herois.html"


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    cards = "".join(f"""<section class="ob">
  <h2>{esc(o['nome'])} <span class="pg">pág. {o['pagina']}</span></h2>
  <div class="desc">{esc(o['descricao'])}</div>
  <div class="f ben"><b>Benefício:</b> {esc(o['beneficio'])}</div>
  <div class="f pen"><b>Penalidade:</b> {esc(o['penalidade'])}</div>
  <div class="f con"><b>Conclusão:</b> {esc(o['conclusao'])}</div>
</section>""" for o in d["objetivos"])
    extra = "".join(
        f'<section class="box"><h2>{esc(s["titulo"])} <span class="pg">pág. {s["pagina"]}</span></h2>'
        f'<div class="desc">{esc(s["texto"])}</div></section>'
        for s in d.get("regras_extra", []))
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Objetivos Heroicos (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#2a3540;border-bottom:2px solid #4f7b9b;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#a9cbe0;font-size:13px}}
 .intro,.box{{padding:14px 24px;color:#cfcfd6;border-bottom:1px solid #33313c;white-space:pre-wrap}}
 .box h2{{color:#a0d0ff}}
 .ob{{border-bottom:1px solid #2c2a30;padding:14px 24px}}
 h2{{margin:0 0 6px;color:#bfe0ff;font-size:16px}} .pg{{font-size:12px;color:#82a0a8;font-weight:400}}
 .desc{{color:#cfcfd6;margin-bottom:8px;white-space:pre-wrap}}
 .f{{padding:5px 10px;margin-bottom:4px;border-left:3px solid;border-radius:3px}}
 .ben{{background:#1c2a1c;border-color:#6a9f4a;color:#cfe0c0}}
 .pen{{background:#2a1c1c;border-color:#9f4a4a;color:#e0c0c0}}
 .con{{background:#241f2c;border-color:#8a6abb;color:#d6c8ee}}
 .f b{{color:#fff}}
</style></head><body>
<header><h1>Objetivos Heroicos — Heróis de Arton (Cap. 4)</h1>
<div class="meta">fonte=herois-arton · {d['total']} objetivos · pág. {d['pagina']}+ · conferência pré-integração</div></header>
<div class="intro"><b>Introdução (regras gerais):</b> {esc(d['introducao'])}</div>
{cards}
{extra}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total']} objetivos, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
