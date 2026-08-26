# -*- coding: utf-8 -*-
r"""Ferramenta de conferência dos MÓDULOS MENORES do Cap. 4 (Heróis de Arton):
Regras Mais Soltas, Culinária Avançada (+ pratos e ingredientes) e Exploração de Masmorras."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "regras_soltas_herois.json"
OUT = BASE / "regras_soltas_herois.html"
ROT = {"regras_soltas": "Regras Mais Soltas", "culinaria": "Culinária Avançada",
       "exploracao_masmorras": "Exploração de Masmorras"}


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    blocos = ""
    for sub, rot in ROT.items():
        mods = [m for m in d["modulos"] if m["subtipo"] == sub]
        if not mods:
            continue
        cards = "".join(f'<section class="rg"><h2>{esc(m["nome"])} <span class="pg">pág. {m["pagina"]}</span></h2>'
                        f'<div class="ef">{esc(m["efeito"])}</div></section>' for m in mods)
        blocos += f'<h3 class="grp">{esc(rot)} ({len(mods)} módulos)</h3>{cards}'
    pratos = "".join(f'<section class="ent"><h3>{esc(p["nome"])} <span class="pg">pág. {p["pagina"]}</span></h3>'
                     f'<div class="ef">{esc(p["descricao"])}</div></section>' for p in d["pratos"])
    ingr = "".join(f'<section class="ent"><h3>{esc(i["nome"])} <span class="pg">pág. {i["pagina"]}</span></h3>'
                   f'<div class="ef">{esc(i["descricao"])}</div></section>' for i in d["ingredientes"])
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Regras Opcionais menores (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#2a4021;border-bottom:2px solid #6b9b4f;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#c0e0a9;font-size:13px}}
 h3.grp{{margin:0;padding:12px 24px;background:#1f281b;color:#c0ffa0;font-size:15px}}
 .rg,.ent{{border-bottom:1px solid #2c2a30;padding:12px 24px}}
 h2{{margin:0 0 6px;color:#d0ffb0;font-size:16px}} .ent h3{{margin:0 0 4px;color:#ffd88a;font-size:14px;background:none;padding:0}}
 .pg{{font-size:12px;color:#8aa082;font-weight:400}}
 .ef{{color:#cfcfd6;white-space:pre-wrap}}
</style></head><body>
<header><h1>Regras Opcionais — módulos menores (Heróis de Arton, Cap. 4)</h1>
<div class="meta">fonte=herois-arton · {d['total_modulos']} módulos + {d['total_pratos']} pratos + {d['total_ingredientes']} ingredientes · conferência pré-integração</div></header>
{blocos}
<h3 class="grp">Culinária — Pratos Especiais ({d['total_pratos']})</h3>
{pratos}
<h3 class="grp">Culinária — Ingredientes ({d['total_ingredientes']})</h3>
{ingr}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total_modulos']} módulos + {d['total_pratos']} pratos + {d['total_ingredientes']} ingredientes, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
