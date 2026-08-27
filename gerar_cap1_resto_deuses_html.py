# -*- coding: utf-8 -*-
r"""Conferência do RESTO do Cap. 1 (Deuses de Arton): Magias Divinas, Poderes
Concedidos, Equipamentos Religiosos + Itens Litúrgicos."""
import sys, io, json, html
from pathlib import Path
from collections import OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
OUT = BASE / "cap1_resto_deuses.html"


def esc(s):
    return html.escape(s or "")


def load(n):
    return json.loads((BASE / "dados" / n).read_text(encoding="utf-8"))


def main():
    mag = load("magias_deuses.json")
    pod = load("poderes_concedidos_deuses.json")
    itr = load("itens_religiosos_deuses.json")
    magias = "".join(f'<section class="e"><h3>{esc(m["nome"])} <span class="tag">{esc(m["arcana_divina"].capitalize())} {m["circulo"]} · {esc(m["escola"])}</span> <span class="pg">pág. {m["pagina"]}</span></h3>'
                     f'<div class="ef">{esc(m["descricao"])}</div>'
                     + "".join(f'<div class="apr"><b>{esc(a["custo"])}:</b> {esc(a["efeito"])}</div>' for a in m["aprimoramentos"])
                     + "</section>" for m in mag["magias"])
    poderes = "".join(f'<section class="e"><h3>{esc(p["nome"])} <span class="tag">{esc(", ".join(p["deuses"]) or "—")}</span> <span class="pg">pág. {p["pagina"]}</span></h3>'
                      f'<div class="ef">{esc(p["efeito"])}</div></section>' for p in pod["poderes"])
    grupos = OrderedDict()
    for i in itr["itens"]:
        grupos.setdefault(i["categoria"], []).append(i)
    itens = ""
    for cat, lst in grupos.items():
        itens += f'<h3 class="sub">{esc(cat)} ({len(lst)})</h3>' + "".join(
            f'<section class="e2"><h4>{esc(i["nome"])} <span class="pg">pág. {i["pagina"]}</span></h4>'
            f'<div class="ef">{esc(i["descricao"])}</div></section>' for i in lst)
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Resto do Cap. 1 (Deuses de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#2f2140;border-bottom:2px solid #7f4fbb;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#c8b0e8;font-size:13px}}
 h2.grp{{margin:0;padding:13px 24px;background:#231b33;color:#cfb0ff;font-size:16px;position:sticky;top:52px}}
 h3.sub{{margin:0;padding:9px 24px;background:#1e1a28;color:#b0a0d8;font-size:14px}}
 .e{{border-bottom:1px solid #2c2a30;padding:11px 24px}} .e2{{border-bottom:1px solid #262430;padding:8px 24px 8px 36px}}
 h3{{margin:0 0 4px;color:#d8bfff;font-size:15px}} h4{{margin:0 0 3px;color:#e0c8f0;font-size:13px}}
 .pg{{font-size:12px;color:#8a82a0;font-weight:400}} .tag{{font-size:11px;background:#4a3d6b;color:#d6c8ff;padding:1px 7px;border-radius:8px}}
 .ef{{color:#cfcfd6;white-space:pre-wrap}}
 .apr{{font-size:13px;color:#cfe0c0;background:#1c241a;border-left:3px solid #6a8f4a;padding:3px 9px;margin-top:3px}}
</style></head><body>
<header><h1>Resto do Cap. 1 — Deuses de Arton</h1>
<div class="meta">fonte=deuses-arton · {mag['total']} magias divinas · {pod['total']} poderes concedidos · {itr['total']} itens religiosos · conferência pré-integração</div></header>
<h2 class="grp">Magias Divinas ({mag['total']})</h2>
{magias}
<h2 class="grp">Novos Poderes Concedidos ({pod['total']})</h2>
{poderes}
<h2 class="grp">Equipamentos Religiosos + Itens Litúrgicos ({itr['total']})</h2>
{itens}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({mag['total']}+{pod['total']}+{itr['total']}, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
