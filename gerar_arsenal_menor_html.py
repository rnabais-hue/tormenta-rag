# -*- coding: utf-8 -*-
r"""Conferência do ARSENAL MENOR (Heróis de Arton, Cap. 3): Melhorias, Capangas,
Veículos, Bases (módulos + Cômodos + Mobílias)."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "arsenal_menor_herois.json"
OUT = BASE / "arsenal_menor_herois.html"
ROT = {"melhoria_item": "Novas Melhorias", "capanga": "Capangas", "veiculo": "Veículos",
       "comodo_base": "Cômodos (Bases)"}


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    byt = {}
    for e in d["entidades"]:
        byt.setdefault(e["tipo"], []).append(e)
    blocos = ""
    for tp, rot in ROT.items():
        lst = byt.get(tp, [])
        if not lst:
            continue
        cards = "".join(f'<section class="e"><h3>{esc(e["nome"])} <span class="pg">pág. {e["pagina"]}</span></h3>'
                        f'<div class="ef">{esc(e["descricao"])}</div></section>' for e in lst)
        blocos += f'<h2 class="grp">{esc(rot)} ({len(lst)})</h2>{cards}'
    mods = "".join(f'<section class="e"><h3>{esc(m["nome"])} <span class="pg">pág. {m["pagina"]}</span></h3>'
                   f'<div class="ef">{esc(m["efeito"])}</div></section>' for m in d["modulos"])
    mob = "".join(f'<tr><td class="k">{esc(m["nome"])}</td><td>{esc(m["beneficio"])}</td></tr>' for m in d["mobilias"])
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Arsenal Menor (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#40342a;border-bottom:2px solid #9b7b4f;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#e0cba9;font-size:13px}}
 h2.grp{{margin:0;padding:12px 24px;background:#281f1b;color:#ffcf9a;font-size:16px;position:sticky;top:52px}}
 .e{{border-bottom:1px solid #2c2a30;padding:11px 24px}}
 h3{{margin:0 0 4px;color:#ffd9a8;font-size:15px}} .pg{{font-size:12px;color:#a89282;font-weight:400}}
 .ef{{color:#cfcfd6;white-space:pre-wrap}}
 table{{border-collapse:collapse;width:calc(100% - 48px);margin:8px 24px;font-size:13px}}
 td{{border:1px solid #3a3640;padding:4px 8px;vertical-align:top}} td.k{{color:#ffc35a;font-weight:600;white-space:nowrap}}
</style></head><body>
<header><h1>Arsenal Menor — Heróis de Arton (Cap. 3)</h1>
<div class="meta">fonte=herois-arton · {d['total_entidades']} entidades + {d['total_modulos']} módulos + {d['total_mobilias']} mobílias · conferência pré-integração</div></header>
{blocos}
<h2 class="grp">Módulos procedurais ({d['total_modulos']})</h2>
{mods}
<h2 class="grp">Mobílias — Tabela 3-8 ({d['total_mobilias']})</h2>
<table>{mob}</table>
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total_entidades']} entidades + {d['total_modulos']} módulos + {d['total_mobilias']} mobílias, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
