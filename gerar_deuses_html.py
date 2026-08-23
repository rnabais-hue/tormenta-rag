# -*- coding: utf-8 -*-
r"""Gera dados/deuses.html — ferramenta de conferência (offline) dos 20 DEUSES
(dados/deuses.json), no visual das demais. Filtra por ENERGIA (Positiva/Negativa/
Qualquer) e por texto (nome/devotos/poderes/crenças); mostra energia, arma,
símbolo, crenças, devotos, poderes concedidos e obrigações.

Reaproveita o <style> da poderes_classe.html e embute o JSON inline.
Rode: python gerar_deuses_html.py
"""
import json, re
from pathlib import Path

BASE = Path(__file__).parent / "dados"
SRC_CSS = BASE / "poderes_classe.html"
JSON_IN = BASE / "deuses.json"
OUT = BASE / "deuses.html"

CSS_EXTRA = """
  .cat{font-family:"Cinzel",serif; font-size:.6rem; letter-spacing:.08em; text-transform:uppercase;
    color:var(--accent); border:1px solid var(--accent-soft); border-radius:6px; padding:2px 7px; white-space:nowrap}
  .resumo{margin:0 0 10px; color:var(--ink-soft); font-size:.9rem; font-style:italic}
  .kv{margin:0 0 7px; font-size:.9rem; color:var(--ink)}
  .kv b{font-family:"Cinzel",serif; font-size:.58rem; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-faint); margin-right:6px; display:block; margin-bottom:1px}
  .tags{display:flex; flex-wrap:wrap; gap:5px; margin:2px 0 9px}
  .tag{font-size:.78rem; color:var(--ink-soft); border:1px solid var(--line-strong); border-radius:6px; padding:2px 8px}
  .tag.dev{color:var(--accent); border-color:var(--accent-soft)}
  .tag.pod{color:var(--gold); border-color:var(--gold)}
  .en{font-family:"Cinzel",serif; font-size:.58rem; letter-spacing:.06em; text-transform:uppercase; border-radius:6px; padding:2px 8px}
  .en.pos{color:#2f7d54; border:1px solid #2f7d54}
  .en.neg{color:var(--accent); border:1px solid var(--accent-soft)}
  .en.qua{color:var(--gold); border:1px solid var(--gold)}
"""


def main():
    css = SRC_CSS.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", css, re.S)
    style = m.group(1) if m else ""

    deuses = json.loads(JSON_IN.read_text(encoding="utf-8"))
    dados = json.dumps(deuses, ensure_ascii=False, indent=1)

    html = f"""<title>Deuses de Tormenta20</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>{style}{CSS_EXTRA}</style>

<div class="wrap">
  <header>
    <div class="brand">
      <div class="kicker">Índice estruturado · Deuses</div>
      <h1>Deuses de Tormenta20</h1>
      <p>Os 20 deuses do Panteão (págs 102–111), extraídos por tipografia. Cada um traz <strong>energia</strong>, arma, símbolo, crenças, <strong>devotos</strong> (quem pode segui-lo), <strong>poderes concedidos</strong> e obrigações. Filtre por energia.</p>
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
        <input id="q" type="search" placeholder="Buscar deus, devoto, poder…" autocomplete="off" aria-label="Buscar">
      </div>
    </div>
    <div class="chips" id="enrow">
      <button class="chip" data-en="" aria-pressed="true">Todas energias</button>
      <button class="chip" data-en="Positiva" aria-pressed="false">Positiva</button>
      <button class="chip" data-en="Negativa" aria-pressed="false">Negativa</button>
      <button class="chip" data-en="Qualquer" aria-pressed="false">Qualquer</button>
    </div>
  </div>

  <div class="cards" id="cards"></div>
  <footer>Fonte: Tormenta20 — Edição Jogo do Ano · uso pessoal para estudo · {len(deuses)} deuses</footer>
</div>

<script>
const DEUSES = {dados};
const state = {{q:"", en:""}};
const ENC = {{Positiva:"pos", Negativa:"neg", Qualquer:"qua"}};

document.querySelectorAll("#enrow .chip").forEach(c=>{{
  c.onclick=()=>{{
    state.en=c.getAttribute("data-en");
    document.querySelectorAll("#enrow .chip").forEach(x=>x.setAttribute("aria-pressed","false"));
    c.setAttribute("aria-pressed","true"); render();
  }};
}});

function matchText(d, q){{
  if(d.nome.toLowerCase().includes(q)) return true;
  for(const k of ["crencas","obrigacoes","arma_preferida","simbolo"])
    if((d[k]||"").toLowerCase().includes(q)) return true;
  return (d.devotos||[]).concat(d.poderes_concedidos||[]).some(x=>x.toLowerCase().includes(q));
}}
function filtered(){{
  const q=state.q.trim().toLowerCase();
  return DEUSES.filter(d=>{{
    if(state.en && d.energia!==state.en) return false;
    if(q && !matchText(d, q)) return false;
    return true;
  }});
}}
function render(){{
  const items=filtered();
  document.getElementById("count").textContent=items.length+" de "+DEUSES.length;
  const cards=document.getElementById("cards");
  if(!items.length){{ cards.innerHTML='<div class="empty">Nenhum deus encontrado.</div>'; return; }}
  cards.innerHTML=items.map(d=>{{
    const dev=(d.devotos||[]).map(x=>`<span class="tag dev">${{x}}</span>`).join("");
    const pod=(d.poderes_concedidos||[]).map(x=>`<span class="tag pod">${{x}}</span>`).join("");
    const en=d.energia?`<span class="en ${{ENC[d.energia]||''}}">${{d.energia}}</span>`:"";
    return `
    <div class="card">
      <div class="ch"><h3>${{d.nome}}</h3><span class="cat">Deus · pág ${{d.pagina}}</span></div>
      ${{d.resumo?`<p class="resumo">${{d.resumo}}</p>`:""}}
      <div class="kv"><b>Energia · Arma</b>${{en}} &nbsp; ${{d.arma_preferida||"—"}}</div>
      <div class="kv"><b>Símbolo</b>${{d.simbolo||"—"}}</div>
      <div class="kv"><b>Crenças e objetivos</b>${{d.crencas||"—"}}</div>
      <div class="kv"><b>Devotos (quem pode seguir)</b></div>
      <div class="tags">${{dev||'<span class="tag">—</span>'}}</div>
      <div class="kv"><b>Poderes concedidos</b></div>
      <div class="tags">${{pod||'<span class="tag">—</span>'}}</div>
      <div class="kv"><b>Obrigações &amp; restrições</b>${{d.obrigacoes||"—"}}</div>
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
    print(f"OK -> {OUT.name} ({len(deuses)} deuses, {len(html)} bytes)")


if __name__ == "__main__":
    main()
