# -*- coding: utf-8 -*-
r"""Ferramenta de conferência do subsistema DOMÍNIOS (Heróis de Arton, Cap. 4)."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "dominios_herois.json"
OUT = BASE / "dominios_herois.html"


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    mods = "".join(f'<section class="rg"><h2>{esc(m["nome"])} <span class="pg">pág. {m["pagina"]}</span></h2>'
                   f'<div class="ef">{esc(m["efeito"])}</div></section>' for m in d["modulos"])
    cons = "".join(f'<section class="cn"><h3>{esc(c["nome"])} <span class="pg">pág. {c["pagina"]}</span></h3>'
                   f'<div class="ef">{esc(c["descricao"])}</div></section>' for c in d["construcoes"])
    tab = ""
    if d.get("tabela_unidades"):
        t = d["tabela_unidades"]
        rows = "".join("<tr>" + "".join(f"<td>{esc(cell.split(': ',1)[-1])}</td>" for cell in ln.split(" | ")) + "</tr>"
                       for ln in t["linhas"])
        head = "".join(f"<th>{esc(c)}</th>" for c in t["colunas"])
        tab = (f'<section class="tb"><h2>{esc(t["nome"])} <span class="pg">pág. {t["pagina"]}</span></h2>'
               f'<table><tr>{head}</tr>{rows}</table></section>')
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Domínios (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#213a40;border-bottom:2px solid #4f8f9b;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#a9dbe0;font-size:13px}}
 h3.grp{{margin:0;padding:12px 24px;background:#1b2528;color:#a0e6ff;font-size:15px}}
 .rg,.cn{{border-bottom:1px solid #2c2a30;padding:12px 24px}}
 h2{{margin:0 0 6px;color:#bfeaff;font-size:16px}} .cn h3{{margin:0 0 4px;color:#ffd88a;font-size:14px;background:none;padding:0}}
 .pg{{font-size:12px;color:#82a0a8;font-weight:400}}
 .ef{{color:#cfcfd6;white-space:pre-wrap}}
 .tb{{padding:14px 24px}} table{{border-collapse:collapse;width:100%;font-size:12px;margin-top:6px}}
 th,td{{border:1px solid #3a3640;padding:4px 7px;text-align:left}} th{{color:#a0e6ff}}
</style></head><body>
<header><h1>Domínios — Heróis de Arton (Cap. 4)</h1>
<div class="meta">fonte=herois-arton · {d['total_modulos']} módulos + {d['total_construcoes']} construções + tabela de unidades · pág. {d['pagina']}+ · conferência pré-integração</div></header>
<h3 class="grp">Módulos de Regra ({d['total_modulos']})</h3>
{mods}
<h3 class="grp">Construções ({d['total_construcoes']})</h3>
{cons}
<h3 class="grp">Unidades Militares</h3>
{tab}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total_modulos']} módulos + {d['total_construcoes']} construções, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
