# -*- coding: utf-8 -*-
r"""Conferência das CLASSES DIVINAS (Deuses de Arton, Cap. 1): variantes Sacerdote/
Druida/Paladino por deus + a nova classe Frade."""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
OUT = BASE / "classes_divinas_deuses.html"


def esc(s):
    return html.escape(s or "")


def main():
    dv = json.loads((BASE / "dados" / "devotos_deuses.json").read_text(encoding="utf-8"))
    fr = json.loads((BASE / "dados" / "frade_deuses.json").read_text(encoding="utf-8"))
    blocos = ""
    for classe in ("Sacerdote", "Druida", "Paladino"):
        lst = [v for v in dv["variantes"] if v["classe"] == classe]
        cards = "".join(f'<section class="v"><h3>{esc(v["nome"])} <span class="pg">pág. {v["pagina"]}</span></h3>'
                        + "".join(f'<div class="h"><b>{esc(h["nome"])}.</b> {esc(h["efeito"])}</div>'
                                  for h in v["habilidades"]) + "</section>" for v in lst)
        blocos += f'<h2 class="grp">{esc(classe)} de … ({len(lst)})</h2>{cards}'
    car = fr["caracteristicas"]
    frade = (f'<section class="v"><h3>Frade <span class="pg">nova classe · pág. {fr["pagina"]}</span></h3>'
             f'<div class="res">{esc(fr["resumo"])}</div>'
             f'<div class="c">PV: {esc(car["pv"])} · PM: {esc(car["pm"])} · Perícias: {esc(car["pericias"])} · '
             f'Proficiências: {esc(car["proficiencias"])}</div>'
             + "".join(f'<div class="h"><b>{esc(h["nome"])}.</b> {esc(h["efeito"][:2000])}</div>'
                       for h in fr["habilidades"]) + "</section>")
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Classes Divinas (Deuses de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#3a2f21;border-bottom:2px solid #b8922f;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#e0cf9a;font-size:13px}}
 h2.grp{{margin:0;padding:12px 24px;background:#28211b;color:#ffd97a;font-size:16px;position:sticky;top:52px}}
 .v{{border-bottom:1px solid #2c2a30;padding:12px 24px}}
 h3{{margin:0 0 5px;color:#ffe0a0;font-size:15px}} .pg{{font-size:12px;color:#a89460;font-weight:400}}
 .res{{color:#cfcfd6;margin-bottom:6px}} .c{{font-size:12px;color:#c0b48a;background:#201c14;padding:5px 9px;border-radius:4px;margin-bottom:6px}}
 .h{{color:#cfcfd6;margin-bottom:4px}} .h b{{color:#fff}}
</style></head><body>
<header><h1>Classes Divinas — Deuses de Arton (Cap. 1)</h1>
<div class="meta">fonte=deuses-arton · {dv['total']} variantes ({', '.join(f'{k} {v}' for k,v in dv['por_classe'].items())}) + classe Frade · conferência pré-integração</div></header>
{blocos}
<h2 class="grp">Nova Classe: Frade</h2>
{frade}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({dv['total']} variantes + Frade, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
