# -*- coding: utf-8 -*-
r"""Ferramenta de conferência do ARSENAL MÁGICO (Heróis de Arton, Cap. 3):
Novas Magias Arcanas + Artefatos + Novos Itens Mágicos."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
OUT = BASE / "arsenal_magico_herois.html"


def esc(s):
    return html.escape(s or "")


def load(n):
    return json.loads((BASE / "dados" / n).read_text(encoding="utf-8"))


def main():
    mag = load("magias_herois.json")
    art = load("artefatos_herois.json")
    im = load("itens_magicos_herois.json")

    magias = "".join(f"""<section class="e"><h3>{esc(m['nome'])}
      <span class="tag">Arcana {m['circulo']} · {esc(m['escola'])}</span> <span class="pg">pág. {m['pagina']}</span></h3>
      <div class="sb">Execução: {esc(m['execucao'])} · Alcance: {esc(m['alcance'])} · {esc(m['alvo_tipo'])}: {esc(m['alvo'])} · Duração: {esc(m['duracao'])}{(' · Resistência: '+esc(m['resistencia'])) if m['resistencia'] else ''}</div>
      <div class="ef">{esc(m['descricao'])}</div>
      {''.join(f'<div class="apr"><b>{esc(a["custo"])}:</b> {esc(a["efeito"])}</div>' for a in m['aprimoramentos'])}</section>""" for m in mag["magias"])

    arte = "".join(f'<section class="e"><h3>{esc(a["nome"])} <span class="pg">pág. {a["pagina"]}</span></h3>'
                   f'<div class="ef">{esc(a["descricao"])}</div></section>' for a in art["artefatos"])

    # itens mágicos agrupados por categoria
    from collections import OrderedDict
    grupos = OrderedDict()
    for it in im["itens"]:
        grupos.setdefault(it["categoria"], []).append(it)
    itens = ""
    for cat, lst in grupos.items():
        cards = "".join(f'<section class="e2"><h4>{esc(i["nome"])} <span class="pg">pág. {i["pagina"]}</span></h4>'
                        f'<div class="ef">{esc(i["descricao"])}</div></section>' for i in lst)
        itens += f'<h3 class="sub">{esc(cat)} ({len(lst)})</h3>{cards}'
    mods = "".join(f'<section class="e"><h3>{esc(m["nome"])} <span class="pg">pág. {m["pagina"]}</span></h3>'
                   f'<div class="ef">{esc(m["efeito"])}</div></section>' for m in im["modulos"])

    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Arsenal Mágico (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#2a2140;border-bottom:2px solid #6b4fbb;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#c9b6ff;font-size:13px}}
 h2.grp{{margin:0;padding:13px 24px;background:#241b33;color:#d6b6ff;font-size:16px;position:sticky;top:52px}}
 h3.sub{{margin:0;padding:9px 24px;background:#1f1b28;color:#b8a0e0;font-size:14px}}
 .e{{border-bottom:1px solid #2c2a30;padding:12px 24px}} .e2{{border-bottom:1px solid #262430;padding:8px 24px 8px 36px}}
 h3{{margin:0 0 5px;color:#cfb6ff;font-size:15px}} h4{{margin:0 0 3px;color:#ecd9a0;font-size:13px}}
 .pg{{font-size:12px;color:#8a82a0;font-weight:400}} .tag{{font-size:11px;background:#4a3d6b;color:#d6c8ff;padding:1px 7px;border-radius:8px}}
 .sb{{font-size:12px;color:#a0c0d0;background:#181f24;padding:4px 8px;border-radius:4px;margin-bottom:5px}}
 .ef{{color:#cfcfd6;white-space:pre-wrap}}
 .apr{{font-size:13px;color:#cfe0c0;background:#1c241a;border-left:3px solid #6a8f4a;padding:3px 9px;margin-top:3px}}
</style></head><body>
<header><h1>Arsenal Mágico — Heróis de Arton (Cap. 3)</h1>
<div class="meta">fonte=herois-arton · {mag['total']} magias · {art['total']} artefatos · {im['total_itens']} itens mágicos + {im['total_modulos']} regras · conferência pré-integração</div></header>
<h2 class="grp">Novas Magias Arcanas ({mag['total']})</h2>
{magias}
<h2 class="grp">Artefatos ({art['total']})</h2>
{arte}
<h2 class="grp">Novos Itens Mágicos ({im['total_itens']} itens + {im['total_modulos']} regras)</h2>
{mods}
{itens}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({mag['total']} magias + {art['total']} artefatos + {im['total_itens']} itens, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
