# -*- coding: utf-8 -*-
r"""Ferramenta de CONFERÊNCIA do bestiário de Ameaças de Arton.

Lê dados/ameacas_arton.json e gera dados/ameacas_arton.html (offline, dois cliques).
Foco em CONFERIR contra o PDF: cada criatura é um card com o stat block completo, e os
campos SUSPEITOS (ND ausente, sem atributos, Defesa/PV vazios, nome curto/estranho)
ficam sinalizados em vermelho — para achar os resíduos de extração rápido. Filtros por
grupo, busca por texto e um botão "só com problemas".
"""
import html
import io
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
IN = BASE / "dados" / "ameacas_arton.json"
OUT = BASE / "dados" / "ameacas_arton.html"


def problemas(c):
    """Lista de flags de suspeita para conferência."""
    p = []
    if c.get("nd") in (None, "", "?"):
        p.append("ND")
    if not c.get("atributos"):
        p.append("sem atributos")
    if not c.get("defesa"):
        p.append("sem Defesa")
    if not c.get("pv"):
        p.append("sem PV")
    nome = c.get("nome", "")
    if len(nome) < 4 or " " not in nome and len(nome) < 6:
        p.append("nome?")
    if any(w in nome for w in ["Esqueleto Fantasma", "Fantasma Hidra"]):
        p.append("nome contaminado?")
    return p


def card(c):
    at = c.get("atributos") or {}
    atr = " ".join(f"{k.capitalize()} {at.get(k, '?')}" for k in ("for", "des", "con", "int", "sab", "car")) if at else ""
    probs = problemas(c)
    cls = "card prob" if probs else "card"
    flag = ("<div class='flags'>" + " ".join(f"<span class='flag'>{html.escape(x)}</span>" for x in probs) + "</div>") if probs else ""

    def linha(rot, val):
        if not val:
            return ""
        return f"<div class='ln'><b>{rot}</b> {html.escape(str(val))}</div>"

    habs = ""
    for h in c.get("habilidades", []):
        habs += f"<div class='hab'><b>{html.escape(h.get('nome',''))}</b> {html.escape(h.get('descricao',''))}</div>"

    return f"""<div class="{cls}" data-grupo="{html.escape(c.get('grupo',''))}" data-txt="{html.escape((c.get('nome','')+' '+c.get('grupo','')).lower())}" data-prob="{1 if probs else 0}">
      <div class="hd"><span class="nm">{html.escape(c.get('nome','?'))}</span>
        <span class="nd">ND {html.escape(str(c.get('nd','?')))}</span></div>
      <div class="sub">{html.escape(c.get('tipo_criatura',''))} {html.escape(c.get('subtipo') and '('+c['subtipo']+')' or '')} {html.escape(c.get('tamanho',''))} · {html.escape(c.get('papel',''))} · pág {html.escape(str(c.get('pagina','')))}</div>
      {flag}
      <div class="grid">
        {linha('Iniciativa', c.get('iniciativa'))}{linha('Percepção', (c.get('percepcao','')+' '+(c.get('sentidos') or '')).strip())}
        {linha('Defesa', c.get('defesa'))}{linha('Resist.', ', '.join(x for x in [f"Fort {c.get('fortitude')}", f"Ref {c.get('reflexos')}", f"Von {c.get('vontade')}"] if c.get('fortitude')) + (('; '+c['resistencias']) if c.get('resistencias') else ''))}
        {linha('PV', c.get('pv'))}{linha('PM', c.get('pm'))}
        {linha('Deslocamento', c.get('deslocamento'))}
        {linha('Corpo a corpo', c.get('corpo_a_corpo'))}{linha('À distância', c.get('distancia'))}
        {linha('Atributos', atr)}
        {linha('Perícias', c.get('pericias'))}{linha('Equipamento', c.get('equipamento'))}{linha('Tesouro', c.get('tesouro'))}
      </div>
      {('<div class=habs>'+habs+'</div>') if habs else ''}
    </div>"""


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    d = json.loads(IN.read_text(encoding="utf-8"))
    crias = d["criaturas"]
    grupos = sorted({c.get("grupo", "") for c in crias})
    n_prob = sum(1 for c in crias if problemas(c))
    chips = "".join(f"<button class='chip' data-g=\"{html.escape(g)}\">{html.escape(g)}</button>" for g in grupos)
    cards = "\n".join(card(c) for c in crias)

    doc = f"""<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Conferência — Ameaças de Arton ({len(crias)} criaturas)</title>
<style>
:root{{--bg:#f6f5f2;--fg:#1b1a17;--card:#fff;--mut:#6b6a66;--bd:#e0ddd6;--nd:#7a5b2e;--prob:#c0392b;--flagbg:#fdecea}}
@media(prefers-color-scheme:dark){{:root{{--bg:#171613;--fg:#eae7df;--card:#211f1b;--mut:#9a978f;--bd:#33302a;--nd:#c8a15a;--prob:#e57368;--flagbg:#3a201d}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,Segoe UI,Roboto,sans-serif}}
header{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--bd);padding:12px 16px;z-index:5}}
h1{{font-size:16px;margin:0 0 8px}}.muted{{color:var(--mut)}}
input,button{{font:inherit}}#q{{padding:7px 10px;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--fg);width:min(320px,60vw)}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}}
.chip{{padding:4px 9px;border:1px solid var(--bd);border-radius:20px;background:var(--card);color:var(--fg);cursor:pointer}}
.chip.on{{background:var(--nd);color:#fff;border-color:var(--nd)}}
#only{{padding:4px 9px;border:1px solid var(--prob);border-radius:20px;background:var(--card);color:var(--prob);cursor:pointer}}
#only.on{{background:var(--prob);color:#fff}}
main{{padding:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;align-items:start}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px 14px}}
.card.prob{{border-color:var(--prob)}}
.hd{{display:flex;justify-content:space-between;align-items:baseline;gap:8px}}
.nm{{font-weight:700;font-size:15px}}.nd{{color:var(--nd);font-weight:700;white-space:nowrap}}
.sub{{color:var(--mut);font-size:12px;margin:2px 0 8px}}
.flags{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px}}
.flag{{background:var(--flagbg);color:var(--prob);border:1px solid var(--prob);border-radius:6px;padding:1px 6px;font-size:11px;font-weight:600}}
.grid{{display:flex;flex-direction:column;gap:3px}}.ln{{font-size:13px}}.ln b{{color:var(--mut);font-weight:600}}
.habs{{margin-top:8px;border-top:1px dashed var(--bd);padding-top:6px;display:flex;flex-direction:column;gap:4px}}
.hab{{font-size:12.5px}}.hab b{{color:var(--nd)}}
</style></head><body>
<header>
  <h1>Conferência — Ameaças de Arton <span class=muted>({len(crias)} criaturas · <span style="color:var(--prob)">{n_prob} com sinalização</span>)</span></h1>
  <input id=q placeholder="buscar por nome ou grupo…" autocomplete=off>
  <button id=only>só com problemas</button>
  <div class=chips>{chips}</div>
</header>
<main id=lista>
{cards}
</main>
<script>
const q=document.getElementById('q'),only=document.getElementById('only'),cards=[...document.querySelectorAll('.card')],chips=[...document.querySelectorAll('.chip')];
let g=null, po=false;
function ap(){{const t=q.value.trim().toLowerCase();cards.forEach(c=>{{
  const okt=!t||c.dataset.txt.includes(t), okg=!g||c.dataset.grupo===g, okp=!po||c.dataset.prob==='1';
  c.style.display=(okt&&okg&&okp)?'':'none';}});}}
q.oninput=ap;
only.onclick=()=>{{po=!po;only.classList.toggle('on',po);ap();}};
chips.forEach(ch=>ch.onclick=()=>{{const v=ch.dataset.g;if(g===v){{g=null;ch.classList.remove('on');}}else{{g=v;chips.forEach(x=>x.classList.remove('on'));ch.classList.add('on');}}ap();}});
</script>
</body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"OK: {OUT}  ({len(crias)} criaturas, {n_prob} com sinalização)")


if __name__ == "__main__":
    main()
