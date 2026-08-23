# -*- coding: utf-8 -*-
r"""Gera dados/origens.html — ferramenta de conferência (offline) das 35 ORIGENS
(dados/origens.json), no visual das demais. Filtra por PERÍCIA concedida e por
texto (nome/itens/poderes/poder único); mostra itens, perícias, poderes e o poder
único de cada origem.

Reaproveita o <style> da poderes_classe.html e embute o JSON inline.
Rode: python gerar_origens_html.py
"""
import json, re
from pathlib import Path

BASE = Path(__file__).parent / "dados"
SRC_CSS = BASE / "poderes_classe.html"
JSON_IN = BASE / "origens.json"
OUT = BASE / "origens.html"

CSS_EXTRA = """
  .cat{font-family:"Cinzel",serif; font-size:.6rem; letter-spacing:.08em; text-transform:uppercase;
    color:var(--accent); border:1px solid var(--accent-soft); border-radius:6px; padding:2px 7px; white-space:nowrap}
  .resumo{margin:0 0 10px; color:var(--ink-soft); font-size:.9rem; font-style:italic}
  .kv{margin:0 0 8px; font-size:.9rem; color:var(--ink)}
  .kv b{font-family:"Cinzel",serif; font-size:.6rem; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-faint); margin-right:6px}
  .tags{display:flex; flex-wrap:wrap; gap:5px; margin:2px 0 10px}
  .tag{font-size:.78rem; color:var(--ink-soft); border:1px solid var(--line-strong); border-radius:6px; padding:2px 8px}
  .tag.per{color:var(--accent); border-color:var(--accent-soft)}
  .tag.pod{color:var(--gold); border-color:var(--gold)}
  .pu{border-top:1px solid var(--line); padding-top:9px; margin-top:2px}
  .pu b{font-family:"Cinzel",serif; font-weight:600; font-size:.9rem; color:var(--ink)}
  .pu .badge{font-family:"Cinzel",serif; font-size:.55rem; letter-spacing:.06em; text-transform:uppercase;
    color:var(--preq); background:var(--preq-bg); border-radius:6px; padding:1px 6px; margin-left:6px}
  .pu p{margin:3px 0 0; color:var(--ink-soft); font-size:.88rem; line-height:1.5}
"""


def main():
    css = SRC_CSS.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", css, re.S)
    style = m.group(1) if m else ""

    origens = json.loads(JSON_IN.read_text(encoding="utf-8"))
    dados = json.dumps(origens, ensure_ascii=False, indent=1)
    pericias = sorted({p for o in origens for p in o.get("pericias", [])})
    chips = "".join(
        f'<button class="chip" data-per="{p}" aria-pressed="false">{p}</button>'
        for p in pericias)

    html = f"""<title>Origens de Tormenta20</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>{style}{CSS_EXTRA}</style>

<div class="wrap">
  <header>
    <div class="brand">
      <div class="kicker">Índice estruturado · Origens</div>
      <h1>Origens de Tormenta20</h1>
      <p>As 35 origens do núcleo (págs 91–101), extraídas por tipografia. Cada uma traz <strong>itens</strong>, as <strong>perícias</strong> e <strong>poderes</strong> concedidos e seu <strong>poder único</strong>. Filtre por perícia concedida.</p>
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
        <input id="q" type="search" placeholder="Buscar origem, item, poder…" autocomplete="off" aria-label="Buscar">
      </div>
    </div>
    <div class="chips" id="perrow"><button class="chip" data-per="" aria-pressed="true">Todas as perícias</button>{chips}</div>
  </div>

  <div class="cards" id="cards"></div>
  <footer>Fonte: Tormenta20 — Edição Jogo do Ano · uso pessoal para estudo · {len(origens)} origens</footer>
</div>

<script>
const ORIGENS = {dados};
const state = {{q:"", per:""}};

document.querySelectorAll("#perrow .chip").forEach(c=>{{
  c.onclick=()=>{{
    state.per=c.getAttribute("data-per");
    document.querySelectorAll("#perrow .chip").forEach(x=>x.setAttribute("aria-pressed","false"));
    c.setAttribute("aria-pressed","true"); render();
  }};
}});

function matchText(o, q){{
  if(o.nome.toLowerCase().includes(q)) return true;
  if((o.itens||"").toLowerCase().includes(q)) return true;
  if((o.beneficios||"").toLowerCase().includes(q)) return true;
  const pu=o.poder_unico||{{}};
  if((pu.nome||"").toLowerCase().includes(q) || (pu.efeito||"").toLowerCase().includes(q)) return true;
  return (o.poderes||[]).concat(o.pericias||[]).some(x=>x.toLowerCase().includes(q));
}}
function filtered(){{
  const q=state.q.trim().toLowerCase();
  return ORIGENS.filter(o=>{{
    if(state.per && !(o.pericias||[]).includes(state.per)) return false;
    if(q && !matchText(o, q)) return false;
    return true;
  }});
}}
function render(){{
  const items=filtered();
  document.getElementById("count").textContent=items.length+" de "+ORIGENS.length;
  const cards=document.getElementById("cards");
  if(!items.length){{ cards.innerHTML='<div class="empty">Nenhuma origem encontrada.</div>'; return; }}
  cards.innerHTML=items.map(o=>{{
    const per=(o.pericias||[]).map(p=>`<span class="tag per">${{p}}</span>`).join("");
    const pod=(o.poderes||[]).map(p=>`<span class="tag pod">${{p}}</span>`).join("");
    const pu=o.poder_unico;
    const puHtml = pu ? `<div class="pu"><b>${{pu.nome}}</b><span class="badge">Poder único</span><p>${{pu.efeito}}</p></div>` : "";
    return `
    <div class="card">
      <div class="ch"><h3>${{o.nome}}</h3><span class="cat">Origem · pág ${{o.pagina}}</span></div>
      ${{o.resumo?`<p class="resumo">${{o.resumo}}</p>`:""}}
      <div class="kv"><b>Itens</b>${{o.itens||"—"}}</div>
      ${{(per||pod)?`<div class="tags">${{per}}${{pod}}</div>`:`<div class="kv"><b>Benefícios</b>${{o.beneficios||"—"}}</div>`}}
      ${{puHtml}}
    </div>`;
  }}).join("");
}}
document.getElementById("q").addEventListener("input", e=>{{ state.q=e.target.value; render(); }});
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
    print(f"OK -> {OUT.name} ({len(origens)} origens, {len(pericias)} perícias no filtro, {len(html)} bytes)")


if __name__ == "__main__":
    main()
