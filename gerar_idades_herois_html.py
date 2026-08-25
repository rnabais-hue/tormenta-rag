# -*- coding: utf-8 -*-
r"""Ferramenta de conferência das IDADES VARIADAS (Heróis de Arton, Cap. 4).

Faixas etárias (nome + idade + modificadores + traços) e mazelas de "O Peso da Idade".
"""
import sys, io, json, html
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "dados" / "idades_herois.json"
OUT = BASE / "idades_herois.html"


def esc(s):
    return html.escape(s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    faixas = ""
    for f in d["faixas"]:
        mods = ", ".join(f"{k} {v:+d}" for k, v in f["modificadores"].items()) or "nenhum"
        tracos = "".join(f'<div class="tr"><b>{esc(t["nome"])}.</b> {esc(t["efeito"])}</div>'
                         for t in f["tracos"]) or '<div class="tr none">—</div>'
        faixas += f"""<section class="fx">
  <h2>{esc(f['nome'])} <span class="idade">{esc(f['idade'])}</span> <span class="pg">pág. {f['pagina']}</span></h2>
  <div class="mods"><b>Modificadores:</b> {esc(mods)}</div>
  <div class="res">{esc(f['resumo'])}</div>
  {tracos}
</section>"""
    mazelas = "".join(f'<section class="mz"><h3>{esc(m["nome"])} <span class="pg">pág. {m["pagina"]}</span></h3>'
                      f'<div class="ef">{esc(m["efeito"])}</div></section>' for m in d["mazelas"])
    extra = "".join(
        f'<section class="box"><h2>{esc(s["titulo"])} <span class="pg">pág. {s["pagina"]}</span></h2>'
        f'<div class="res">{esc(s["texto"])}</div></section>' for s in d.get("regras_extra", []))
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Idades Variadas (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#3a2a40;border-bottom:2px solid #7b4f9b;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#c9a9e0;font-size:13px}}
 .intro,.box{{padding:14px 24px;color:#cfcfd6;border-bottom:1px solid #33313c;white-space:pre-wrap}}
 .box h2{{color:#a0d0ff}}
 h3.grp{{margin:0;padding:12px 24px;background:#241b28;color:#d6b6ff;font-size:15px}}
 .fx{{border-bottom:1px solid #2c2a30;padding:14px 24px}}
 h2{{margin:0 0 6px;color:#d8bfff;font-size:16px}}
 .idade{{font-size:13px;color:#9a86c0}} .pg{{font-size:12px;color:#8a82a0;font-weight:400}}
 .mods{{color:#ffd6a0;margin-bottom:6px}} .mods b{{color:#fff}}
 .res{{color:#cfcfd6;margin-bottom:8px;white-space:pre-wrap}}
 .tr{{background:#20242c;border-left:3px solid #6a8f9f;padding:5px 10px;margin-bottom:4px;color:#cfe0e6}}
 .tr b{{color:#fff}} .tr.none{{border-color:#444;color:#888}}
 .mz{{padding:8px 24px;border-bottom:1px solid #262430}}
 .mz h3{{margin:0 0 3px;color:#ffbcbc;font-size:14px;background:none;padding:0}}
 .mz .ef{{color:#cfcfd6}}
</style></head><body>
<header><h1>Idades Variadas — Heróis de Arton (Cap. 4)</h1>
<div class="meta">fonte=herois-arton · {d['total_faixas']} faixas + {d['total_mazelas']} mazelas · pág. {d['pagina']}+ · conferência pré-integração</div></header>
<div class="intro"><b>Introdução (regras gerais + O Peso da Idade + Envelhecendo):</b> {esc(d['introducao'])}</div>
<h3 class="grp">Faixas Etárias ({d['total_faixas']})</h3>
{faixas}
<h3 class="grp">O Peso da Idade — Mazelas ({d['total_mazelas']})</h3>
{mazelas}
{extra}
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"{OUT.name} gerado ({d['total_faixas']} faixas + {d['total_mazelas']} mazelas, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
