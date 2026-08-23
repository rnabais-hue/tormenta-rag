# -*- coding: utf-8 -*-
r"""Gera dados/pericias.html — ferramenta de conferência (offline, dois cliques)
das 29 PERÍCIAS (dados/pericias.json), no mesmo visual das demais ferramentas.
Filtra por ATRIBUTO-chave e pelas flags (só treinada / penalidade de armadura),
busca por texto e lista os USOS de cada perícia.

Reaproveita o bloco <style> da poderes_classe.html e embute o JSON inline.
Rode: python gerar_pericias_html.py
"""
import json, re
from pathlib import Path

BASE = Path(__file__).parent / "dados"
SRC_CSS = BASE / "poderes_classe.html"
JSON_IN = BASE / "pericias.json"
OUT = BASE / "pericias.html"

ATRIBS = ["Força", "Destreza", "Constituição", "Inteligência", "Sabedoria", "Carisma"]

CSS_EXTRA = """
  .cat{font-family:"Cinzel",serif; font-size:.6rem; letter-spacing:.08em; text-transform:uppercase;
    color:var(--accent); border:1px solid var(--accent-soft); border-radius:6px; padding:2px 7px; white-space:nowrap}
  .flags{display:flex; flex-wrap:wrap; gap:5px; margin:2px 0 8px}
  .flag{font-family:"Cinzel",serif; font-size:.58rem; letter-spacing:.05em; text-transform:uppercase;
    color:var(--gold); border:1px solid var(--gold); border-radius:6px; padding:2px 7px}
  .resumo{margin:0 0 10px; color:var(--ink-soft); font-size:.92rem; font-style:italic}
  .usos{list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px}
  .uso b{font-family:"Cinzel",serif; font-weight:600; font-size:.86rem; color:var(--ink)}
  .uso .cd{font-family:"Cinzel",serif; font-size:.6rem; letter-spacing:.04em; color:var(--preq);
    background:var(--preq-bg); border-radius:6px; padding:1px 6px; margin-left:6px}
  .uso p{margin:2px 0 0; color:var(--ink-soft); font-size:.88rem; line-height:1.5}
  .nousos{color:var(--ink-faint); font-style:italic; font-size:.85rem}
"""


def main():
    css = SRC_CSS.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", css, re.S)
    style = m.group(1) if m else ""

    pericias = json.loads(JSON_IN.read_text(encoding="utf-8"))
    dados = json.dumps(pericias, ensure_ascii=False, indent=1)
    chips_attr = "".join(
        f'<button class="chip" data-attr="{a}" aria-pressed="false">{a}</button>'
        for a in ATRIBS)

    html = f"""<title>Perícias de Tormenta20</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>{style}{CSS_EXTRA}</style>

<div class="wrap">
  <header>
    <div class="brand">
      <div class="kicker">Índice estruturado · Perícias</div>
      <h1>Perícias de Tormenta20</h1>
      <p>As 29 perícias do núcleo (págs 121–129), extraídas por tipografia. Cada uma traz o <strong>atributo-chave</strong>, as flags (só treinada / penalidade de armadura) e seus <strong>usos</strong>. Filtre por atributo e confira contra o livro.</p>
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
        <input id="q" type="search" placeholder="Buscar perícia ou uso…" autocomplete="off" aria-label="Buscar">
      </div>
      <label class="chk"><input type="checkbox" id="onlytr"> só treinada</label>
      <label class="chk"><input type="checkbox" id="onlyarm"> penalidade de armadura</label>
    </div>
    <div class="chips" id="attrrow"><button class="chip" data-attr="" aria-pressed="true">Todos os atributos</button>{chips_attr}</div>
  </div>

  <div class="cards" id="cards"></div>
  <footer>Fonte: Tormenta20 — Edição Jogo do Ano · uso pessoal para estudo · {len(pericias)} perícias</footer>
</div>

<script>
const PERICIAS = {dados};
const state = {{q:"", attr:"", onlytr:false, onlyarm:false}};

document.querySelectorAll("#attrrow .chip").forEach(c=>{{
  c.onclick=()=>{{
    state.attr=c.getAttribute("data-attr");
    document.querySelectorAll("#attrrow .chip").forEach(x=>x.setAttribute("aria-pressed","false"));
    c.setAttribute("aria-pressed","true"); render();
  }};
}});

function matchText(p, q){{
  if(p.nome.toLowerCase().includes(q)) return true;
  return (p.usos||[]).some(u=>u.nome.toLowerCase().includes(q) || (u.efeito||"").toLowerCase().includes(q));
}}
function filtered(){{
  const q=state.q.trim().toLowerCase();
  return PERICIAS.filter(p=>{{
    if(state.attr && p.atributo!==state.attr) return false;
    if(state.onlytr && !p.so_treinada) return false;
    if(state.onlyarm && !p.penalidade_armadura) return false;
    if(q && !matchText(p, q)) return false;
    return true;
  }});
}}
function render(){{
  const items=filtered();
  document.getElementById("count").textContent=items.length+" de "+PERICIAS.length;
  const cards=document.getElementById("cards");
  if(!items.length){{ cards.innerHTML='<div class="empty">Nenhuma perícia encontrada.</div>'; return; }}
  cards.innerHTML=items.map(p=>{{
    const flags=[];
    if(p.so_treinada) flags.push("Só treinada");
    if(p.penalidade_armadura) flags.push("Penalidade de armadura");
    const usos = (p.usos&&p.usos.length)
      ? `<ul class="usos">${{p.usos.map(u=>`<li class="uso"><b>${{u.nome}}</b>${{u.cd?`<span class="cd">CD ${{u.cd}}${{u.apenas_treinado?" · treinado":""}}</span>`:(u.apenas_treinado?`<span class="cd">treinado</span>`:"")}}<p>${{u.efeito}}</p></li>`).join("")}}</ul>`
      : `<div class="nousos">Sem usos nomeados (mecânica no resumo).</div>`;
    return `
    <div class="card">
      <div class="ch"><h3>${{p.nome}}</h3><span class="cat">${{p.atributo}}</span></div>
      ${{flags.length?`<div class="flags">${{flags.map(f=>`<span class="flag">${{f}}</span>`).join("")}}</div>`:""}}
      ${{p.resumo?`<p class="resumo">${{p.resumo}}</p>`:""}}
      ${{usos}}
    </div>`;
  }}).join("");
}}
document.getElementById("q").addEventListener("input", e=>{{ state.q=e.target.value; render(); }});
document.getElementById("onlytr").addEventListener("change", e=>{{ state.onlytr=e.target.checked; render(); }});
document.getElementById("onlyarm").addEventListener("change", e=>{{ state.onlyarm=e.target.checked; render(); }});
document.getElementById("theme").onclick=()=>{{
  const cur=document.documentElement.getAttribute("data-theme");
  const now = cur==="dark" ? "light" : cur==="light" ? "dark"
    : (matchMedia("(prefers-color-scheme:dark)").matches ? "light" : "dark");
  document.documentElement.setAttribute("data-theme", now);
}};
render();
</script>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"OK -> {OUT.name} ({len(pericias)} perícias, {len(html)} bytes)")


if __name__ == "__main__":
    main()
