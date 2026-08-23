# -*- coding: utf-8 -*-
r"""Gera dados/poderes_gerais.html — ferramenta de conferência (offline, dois
cliques) dos PODERES GERAIS (dados/poderes_gerais.json), no mesmo visual da
poderes_classe.html. Filtra por CATEGORIA (combate/destino/magia/concedido/
tormenta), por DEUS (nos concedidos) e por texto; destaca o pré-requisito.

Reaproveita o bloco <style> da poderes_classe.html (consistência automática) e
embute o JSON inline (autossuficiente). Rode: python gerar_poderes_gerais_html.py
"""
import json, re
from pathlib import Path

BASE = Path(__file__).parent / "dados"
SRC_CSS = BASE / "poderes_classe.html"
JSON_IN = BASE / "poderes_gerais.json"
OUT = BASE / "poderes_gerais.html"

CAT_LABEL = {"combate": "Combate", "destino": "Destino", "magia": "Magia",
             "concedido": "Concedido", "tormenta": "Tormenta"}

# CSS extra (badge de deus + realce de categoria) — anexado ao <style> reusado
CSS_EXTRA = """
  .gods{display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px}
  .god{font-family:"Cinzel",serif; font-size:.62rem; letter-spacing:.04em;
    color:var(--gold); border:1px solid var(--gold); border-radius:6px; padding:2px 7px}
  .cat{font-family:"Cinzel",serif; font-size:.6rem; letter-spacing:.08em; text-transform:uppercase;
    color:var(--accent); border:1px solid var(--accent-soft); border-radius:6px; padding:2px 7px; white-space:nowrap}
  #deusrow{display:none}
  #deusrow.show{display:flex}
"""


def main():
    css = SRC_CSS.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", css, re.S)
    style = m.group(1) if m else ""

    poderes = json.loads(JSON_IN.read_text(encoding="utf-8"))
    deuses = sorted({g for p in poderes for g in p.get("deuses", [])})
    n_pre = sum(1 for p in poderes if p["pre_requisito"])
    dados = json.dumps(poderes, ensure_ascii=False, indent=1)

    chips_cat = "".join(
        f'<button class="chip" data-cat="{c}" aria-pressed="false">{lbl}</button>'
        for c, lbl in CAT_LABEL.items())
    chips_deus = "".join(
        f'<button class="chip" data-deus="{d}" aria-pressed="false">{d}</button>'
        for d in deuses)

    html = f"""<title>Poderes Gerais de Tormenta20</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>{style}{CSS_EXTRA}</style>

<div class="wrap">
  <header>
    <div class="brand">
      <div class="kicker">Índice estruturado · Poderes · Stage A</div>
      <h1>Poderes Gerais de Tormenta20</h1>
      <p>Poderes do capítulo Perícias &amp; Poderes (págs 130–143), extraídos por tipografia em nós individuais. Confira nome, <strong>pré-requisito</strong> e efeito contra o livro. Filtre por categoria; nos <em>concedidos</em>, filtre por deus.</p>
    </div>
    <div class="hbtns">
      <span class="count" id="count"></span>
      <button class="toggle" id="theme" type="button">◐ Tema</button>
    </div>
  </header>

  <div class="toolbar">
    <div class="row1">
      <div class="search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input id="q" type="search" placeholder="Buscar poder…" autocomplete="off" aria-label="Buscar poder">
      </div>
      <label class="chk"><input type="checkbox" id="onlypreq"> só com pré-requisito</label>
    </div>
    <div class="chips" id="catrow"><button class="chip" data-cat="" aria-pressed="true">Todas</button>{chips_cat}</div>
    <div class="chips" id="deusrow"><button class="chip" data-deus="" aria-pressed="true">Todos os deuses</button>{chips_deus}</div>
  </div>

  <div class="cards" id="cards"></div>
  <footer>Fonte: Tormenta20 — Edição Jogo do Ano · uso pessoal para estudo · {len(poderes)} poderes gerais ({n_pre} com pré-requisito) · Stage A (pré-requisito como texto)</footer>
</div>

<script>
const PODERES = {dados};
const CAT_LABEL = {json.dumps(CAT_LABEL, ensure_ascii=False)};
const state = {{q:"", cat:"", deus:"", onlypreq:false}};

function syncDeusRow(){{
  document.getElementById("deusrow").classList.toggle("show", state.cat==="concedido");
}}
function bindChips(rowId, key){{
  document.querySelectorAll("#"+rowId+" .chip").forEach(c=>{{
    c.onclick=()=>{{
      state[key]=c.getAttribute("data-"+ (key==="cat"?"cat":"deus"));
      if(key==="cat"){{ state.deus=""; }}
      document.querySelectorAll("#"+rowId+" .chip").forEach(x=>x.setAttribute("aria-pressed","false"));
      c.setAttribute("aria-pressed","true");
      if(key==="cat"){{
        document.querySelectorAll("#deusrow .chip").forEach((x,i)=>x.setAttribute("aria-pressed", i===0?"true":"false"));
        syncDeusRow();
      }}
      render();
    }};
  }});
}}
bindChips("catrow","cat");
bindChips("deusrow","deus");

function filtered(){{
  const q=state.q.trim().toLowerCase();
  return PODERES.filter(p=>{{
    if(state.cat && p.categoria!==state.cat) return false;
    if(state.cat==="concedido" && state.deus && !(p.deuses||[]).includes(state.deus)) return false;
    if(state.onlypreq && !p.pre_requisito) return false;
    if(q && !(p.nome.toLowerCase().includes(q) || (p.pre_requisito||"").toLowerCase().includes(q)
              || (p.deuses||[]).join(" ").toLowerCase().includes(q))) return false;
    return true;
  }});
}}
function render(){{
  const items=filtered();
  document.getElementById("count").textContent=items.length+" de "+PODERES.length;
  const cards=document.getElementById("cards");
  if(!items.length){{ cards.innerHTML='<div class="empty">Nenhum poder encontrado.</div>'; return; }}
  cards.innerHTML=items.map(p=>`
    <div class="card">
      <div class="ch"><h3>${{p.nome}}</h3><span class="cat">${{CAT_LABEL[p.categoria]||p.categoria}}</span></div>
      ${{(p.deuses&&p.deuses.length)?`<div class="gods">${{p.deuses.map(g=>`<span class="god">${{g}}</span>`).join("")}}</div>`:""}}
      ${{p.pre_requisito?`<div class="preq"><b>Pré-req</b>${{p.pre_requisito}}</div>`:""}}
      <p>${{p.efeito}}</p>
    </div>`).join("");
}}
document.getElementById("q").addEventListener("input", e=>{{ state.q=e.target.value; render(); }});
document.getElementById("onlypreq").addEventListener("change", e=>{{ state.onlypreq=e.target.checked; render(); }});
const tbtn=document.getElementById("theme");
tbtn.onclick=()=>{{
  const cur=document.documentElement.getAttribute("data-theme");
  const now = cur==="dark" ? "light" : cur==="light" ? "dark"
    : (matchMedia("(prefers-color-scheme:dark)").matches ? "light" : "dark");
  document.documentElement.setAttribute("data-theme", now);
}};
syncDeusRow();
render();
</script>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"OK -> {OUT.name} ({len(poderes)} poderes, {len(deuses)} deuses, {len(html)} bytes)")


if __name__ == "__main__":
    main()
