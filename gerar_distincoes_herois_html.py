# -*- coding: utf-8 -*-
r"""Ferramenta de CONFERÊNCIA HTML das Distinções (Cap. 2) de Heróis de Arton.
Lê dados/distincoes_herois.json e gera HTML para revisão antes da integração.
Poderes com efeito curto (<40c) são destacados. NÃO toca no índice.
"""
import sys, io, json, html
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = Path(__file__).parent
d = json.load(open(BASE / "dados" / "distincoes_herois.json", encoding="utf-8"))
esc = html.escape

cards = []
tot_pod = 0
tot_curto = 0
for x in d["distincoes"]:
    pods = []
    for p in x["poderes"]:
        tot_pod += 1
        curto = len(p["efeito"]) < 40
        if curto:
            tot_curto += 1
        tag = f' <span class="tag">{esc(p["tag"])}</span>' if p.get("tag") else ""
        cls = ' class="pod curto"' if curto else ' class="pod"'
        pods.append(f'<div{cls}><b>{esc(p["nome"])}</b>{tag}'
                    f'<div class="ef">{esc(p["efeito"]) or "⚠ efeito não capturado"}</div></div>')
    marca = x["marca"]
    marca_html = ""
    if marca.get("nome"):
        marca_html = (f'<div class="marca"><b>Marca — {esc(marca["nome"])}:</b> '
                      f'{esc(marca["efeito"])}</div>')
    cards.append(f'''<section class="dist">
      <h2>{esc(x["nome"])} <span class="pg">pág. {x["pagina"]} · {len(x["poderes"])} poderes</span></h2>
      <div class="conc">{esc(x["conceito"])}</div>
      <div class="adm"><b>Admissão:</b> {esc(x["admissao"])}</div>
      {marca_html}
      <div class="pods">{"".join(pods)}</div>
    </section>''')

doc = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência — Distinções (Heróis de Arton)</title>
<style>
 body{{font:14px/1.55 system-ui,sans-serif;margin:0;background:#1a1a1e;color:#e8e8ea}}
 header{{padding:16px 24px;background:#2a2140;border-bottom:2px solid #6b4fbb;position:sticky;top:0}}
 header h1{{margin:0;font-size:19px}} header .meta{{color:#b9a9e0;font-size:13px}}
 .dist{{border-bottom:1px solid #33313c;padding:18px 24px}}
 h2{{margin:0 0 8px;color:#c9b6ff;font-size:17px}} .pg{{font-size:12px;color:#8a82a0;font-weight:400}}
 .conc{{color:#cfcfd6;margin-bottom:8px;white-space:pre-wrap}}
 .adm{{color:#c9d4c0;background:#20241c;border-left:3px solid #6a8f4a;padding:6px 10px;margin-bottom:8px}}
 .marca{{color:#e0d0b0;background:#2a2418;border-left:3px solid #b08a3a;padding:6px 10px;margin-bottom:10px}}
 .pods{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:8px}}
 .pod{{background:#232329;border:1px solid #35353d;border-radius:7px;padding:8px 10px}}
 .pod.curto{{border-color:#a05555;background:#2a2020}}
 .pod b{{color:#fff}} .ef{{font-size:13px;color:#cfcfd4;margin-top:4px;white-space:pre-wrap}}
 .tag{{font-size:11px;background:#4a3d6b;color:#d6c8ff;padding:1px 6px;border-radius:8px;margin-left:4px}}
</style></head><body>
<header><h1>Distinções — Heróis de Arton (Cap. 2)</h1>
<div class="meta">fonte=herois-arton · {len(d["distincoes"])} distinções · {tot_pod} poderes ·
 {tot_curto} com efeito curto (destacados em vermelho) · conferência pré-integração</div></header>
{"".join(cards)}
</body></html>'''

OUT = BASE / "distincoes_herois.html"
OUT.write_text(doc, encoding="utf-8")
print(f"[OK] {len(d['distincoes'])} distinções, {tot_pod} poderes ({tot_curto} curtos) -> {OUT}")
