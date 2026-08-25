# -*- coding: utf-8 -*-
r"""Ferramenta de conferência das COMPLICAÇÕES (Heróis de Arton, Cap. 4).

Lê dados/complicacoes_herois.json e gera complicacoes_herois.html (offline).
Agrupa por categoria (Gerais / de Classe), mostra a classe e a marca de voto (†).
"""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "complicacoes_herois.json"
OUT = BASE / "complicacoes_herois.html"


def esc(s):
    return html.escape(s or "")


def card(c):
    cl = f'<span class="cls">{esc(c["classe"])}</span>' if c.get("classe") else ""
    vt = '<span class="voto" title="complicação de código/voto (viola → perde PM)">†&nbsp;voto</span>' if c.get("voto") else ""
    return f"""<section class="cp">
  <h2>{esc(c['nome'])} {cl}{vt} <span class="pg">pág. {c['pagina']}</span></h2>
  <div class="ef">{esc(c['efeito'])}</div>
</section>"""


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    gerais = [c for c in d["complicacoes"] if c["categoria"] == "geral"]
    classe = [c for c in d["complicacoes"] if c["categoria"] == "classe"]
    extra = "".join(
        f'<section class="box"><h2>{esc(s["titulo"])} <span class="pg">pág. {s["pagina"]}</span></h2>'
        f'<div class="ef">{esc(s["texto"])}</div></section>'
        for s in d.get("regras_extra", []))
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Complicações (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#40212a;border-bottom:2px solid #9b4f6b;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#e0a9b9;font-size:13px}}
 .intro,.box{{padding:14px 24px;color:#cfcfd6;border-bottom:1px solid #33313c;white-space:pre-wrap}}
 h3.grp{{margin:0;padding:12px 24px;background:#241b1e;color:#ffb6ca;font-size:15px;position:sticky;top:52px}}
 .cp{{border-bottom:1px solid #2c2a30;padding:12px 24px}}
 h2{{margin:0 0 6px;color:#ffc0cf;font-size:16px}} .pg{{font-size:12px;color:#a0828a;font-weight:400}}
 .ef{{color:#cfcfd6;white-space:pre-wrap}}
 .cls{{font-size:12px;background:#4a3d6b;color:#d6c8ff;padding:1px 7px;border-radius:8px;margin-left:4px}}
 .voto{{font-size:12px;background:#5a3a1a;color:#ffd6a0;padding:1px 7px;border-radius:8px;margin-left:4px}}
 .box h2{{color:#a0d0ff}}
</style></head><body>
<header><h1>Complicações — Heróis de Arton (Cap. 4)</h1>
<div class="meta">fonte=herois-arton · {d['total']} complicações ({d['n_gerais']} gerais + {d['n_classe']} de classe) · pág. {d['pagina']}+ · conferência pré-integração</div></header>
<div class="intro"><b>Introdução:</b> {esc(d['introducao'])}</div>
<h3 class="grp">Complicações Gerais ({len(gerais)})</h3>
{''.join(card(c) for c in gerais)}
<h3 class="grp">Complicações de Classe ({len(classe)})</h3>
{''.join(card(c) for c in classe)}
{extra}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total']} complicações, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
