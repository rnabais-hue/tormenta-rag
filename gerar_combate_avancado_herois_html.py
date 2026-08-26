# -*- coding: utf-8 -*-
r"""Ferramenta de conferência do COMBATE AVANÇADO (Heróis de Arton, Cap. 4)."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "combate_avancado_herois.json"
OUT = BASE / "combate_avancado_herois.html"


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    regras = "".join(f"""<section class="rg">
  <h2>{esc(r['nome'])} <span class="pg">pág. {r['pagina']}</span></h2>
  <div class="ef">{esc(r['efeito'])}</div>
</section>""" for r in d["regras"])
    tabelas = ""
    for tb in d["tabelas"]:
        rows = "".join(f'<tr><td class="k">{esc(ln["faixa"])}</td><td>{esc(ln["efeito"])}</td></tr>'
                       for ln in tb["linhas"])
        tabelas += (f'<section class="tb"><h2>Tabela: {esc(tb["nome"])} '
                    f'<span class="pg">pág. {tb["pagina"]} · {tb["total_linhas"]} linhas</span></h2>'
                    f'<table>{rows}</table></section>')
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Combate Avançado (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#402a21;border-bottom:2px solid #9b6b4f;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#e0c0a9;font-size:13px}}
 .intro{{padding:14px 24px;color:#cfcfd6;border-bottom:1px solid #33313c;white-space:pre-wrap}}
 h3.grp{{margin:0;padding:12px 24px;background:#281f1b;color:#ffcaa0;font-size:15px}}
 .rg{{border-bottom:1px solid #2c2a30;padding:14px 24px}}
 h2{{margin:0 0 6px;color:#ffd0b0;font-size:16px}} .pg{{font-size:12px;color:#a89282;font-weight:400}}
 .ef{{color:#cfcfd6;white-space:pre-wrap}}
 .tb{{padding:14px 24px;border-bottom:1px solid #33313c}}
 table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:6px}}
 td{{border:1px solid #3a3640;padding:4px 8px;vertical-align:top}}
 td.k{{color:#ffc35a;font-weight:600;white-space:nowrap;width:1%}}
</style></head><body>
<header><h1>Combate Avançado — Heróis de Arton (Cap. 4)</h1>
<div class="meta">fonte=herois-arton · {d['total_regras']} regras + {d['total_tabelas']} tabelas · pág. {d['pagina']}+ · conferência pré-integração</div></header>
<div class="intro"><b>Introdução:</b> {esc(d['introducao'])}</div>
<h3 class="grp">Regras Opcionais de Combate ({d['total_regras']})</h3>
{regras}
<h3 class="grp">Tabelas ({d['total_tabelas']})</h3>
{tabelas}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total_regras']} regras + {d['total_tabelas']} tabelas, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
