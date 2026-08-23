# -*- coding: utf-8 -*-
r"""Gera a ferramenta de conferência visual offline dados/magias.html
a partir de dados/magias.json.
"""
import json
import sys
import io
from pathlib import Path

BASE = Path(__file__).parent
IN_JSON = BASE / "dados" / "magias.json"
OUT_HTML = BASE / "dados" / "magias.html"


def gerar_html():
    data = json.loads(IN_JSON.read_text(encoding="utf-8"))
    magias = data.get("magias", [])
    regras = data.get("regras", [])
    total = len(magias) + len(regras)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Magias de Tormenta20</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>
  :root {{
    --ground:#efe7d9; --surface:#fbf8f2; --surface-2:#f3ecdf;
    --ink:#241d1a; --ink-soft:#5c5049; --ink-faint:#8a7d72;
    --line:#e0d5c3; --line-strong:#cdbfa8;
    --accent:#9d2933; --accent-soft:#b8434c; --accent-ghost:#9d29331a;
    --gold:#a8823c; --preq:#7a5a1e; --preq-bg:#a8823c1f;
    --shadow:0 1px 2px #241d1a0f,0 8px 24px -12px #241d1a26;
  }}
  @media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
    --ground:#160f11; --surface:#211a1c; --surface-2:#2b2225;
    --ink:#ece3d6; --ink-soft:#b4a99b; --ink-faint:#847668;
    --line:#352a2d; --line-strong:#493a3d;
    --accent:#e0555f; --accent-soft:#ec6b74; --accent-ghost:#e0555f1f;
    --gold:#c99a4e; --preq:#d9b263; --preq-bg:#c99a4e22;
    --shadow:0 1px 2px #0006,0 12px 30px -14px #0009;
  }}}}
  :root[data-theme="dark"]{{
    --ground:#160f11; --surface:#211a1c; --surface-2:#2b2225;
    --ink:#ece3d6; --ink-soft:#b4a99b; --ink-faint:#847668;
    --line:#352a2d; --line-strong:#493a3d;
    --accent:#e0555f; --accent-soft:#ec6b74; --accent-ghost:#e0555f1f;
    --gold:#c99a4e; --preq:#d9b263; --preq-bg:#c99a4e22;
    --shadow:0 1px 2px #0006,0 12px 30px -14px #0009;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    background:var(--ground);color:var(--ink);
    font-family:'Spectral',Georgia,serif;font-size:16px;line-height:1.55;
    padding:2rem 1rem 4rem;min-height:100vh;
  }}
  .container{{max-width:1200px;margin:0 auto}}
  header{{margin-bottom:2rem;text-align:center}}
  h1{{
    font-family:'Cinzel',serif;font-size:2.2rem;font-weight:700;
    color:var(--accent);letter-spacing:.04em;margin-bottom:.3rem;
  }}
  .subtitle{{color:var(--ink-soft);font-size:1rem}}
  .controls{{
    display:flex;flex-direction:column;gap:.8rem;margin-bottom:2rem;
    background:var(--surface);border:1px solid var(--line);border-radius:12px;
    padding:1.2rem;box-shadow:var(--shadow);
  }}
  .search-row{{display:flex;gap:.8rem;align-items:center}}
  .search-box{{
    flex:1;padding:.7rem 1rem;font-size:1rem;font-family:inherit;
    background:var(--surface-2);border:1px solid var(--line);border-radius:8px;
    color:var(--ink);
  }}
  .search-box:focus{{outline:2px solid var(--accent);border-color:transparent}}
  .filter-group{{display:flex;gap:.4rem;flex-wrap:wrap;align-items:center}}
  .filter-label{{font-family:'Cinzel',serif;font-size:.85rem;font-weight:600;color:var(--ink-soft);margin-right:.4rem}}
  .pill{{
    padding:.3rem .75rem;font-size:.85rem;font-family:'Spectral',serif;
    border:1px solid var(--line);border-radius:20px;background:var(--surface-2);
    color:var(--ink);cursor:pointer;transition:.15s ease;
  }}
  .pill:hover{{border-color:var(--accent)}}
  .pill.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:1.2rem}}
  .card{{
    background:var(--surface);border:1px solid var(--line);border-radius:10px;
    padding:1.2rem;box-shadow:var(--shadow);display:flex;flex-direction:column;
    gap:.6rem;position:relative;
  }}
  .card-header{{display:flex;justify-content:space-between;align-items:flex-start;gap:.6rem}}
  .card-title{{font-family:'Cinzel',serif;font-size:1.2rem;font-weight:600;color:var(--accent)}}
  .badges{{display:flex;gap:.35rem;flex-wrap:wrap;align-items:center}}
  .badge{{
    font-size:.75rem;font-family:'Cinzel',serif;font-weight:600;
    padding:.15rem .45rem;border-radius:4px;background:var(--surface-2);
    border:1px solid var(--line-strong);color:var(--ink-soft);
  }}
  .badge.circulo{{background:var(--accent-ghost);border-color:var(--accent-soft);color:var(--accent)}}
  .badge.escola{{background:var(--preq-bg);border-color:var(--gold);color:var(--preq)}}
  .badge.tipo{{background:var(--surface-2);border-color:var(--line-strong);color:var(--ink-soft);text-transform:uppercase}}
  .stat-grid{{
    display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.4rem;
    font-size:.85rem;background:var(--surface-2);padding:.6rem .8rem;border-radius:6px;
    border:1px solid var(--line);
  }}
  .stat-item b{{color:var(--ink);font-weight:600}}
  .desc{{font-size:.95rem;color:var(--ink);text-align:justify}}
  .apr-block{{margin-top:.4rem;border-top:1px dashed var(--line-strong);padding-top:.5rem}}
  .apr-title{{font-family:'Cinzel',serif;font-size:.85rem;font-weight:600;color:var(--accent);margin-bottom:.3rem}}
  .apr-item{{font-size:.88rem;margin-bottom:.35rem;padding-left:.6rem;border-left:2px solid var(--accent-soft)}}
  .apr-cost{{font-weight:600;color:var(--accent)}}
  .card-footer{{margin-top:auto;font-size:.8rem;color:var(--ink-faint);text-align:right;padding-top:.4rem}}
  .stats-bar{{
    margin-bottom:1rem;color:var(--ink-soft);font-size:.9rem;
    display:flex;justify-content:space-between;align-items:center;
  }}
  .rule-card{{
    grid-column:1 / -1;background:var(--surface-2);border:1px solid var(--gold);
    border-radius:10px;padding:1.2rem;box-shadow:var(--shadow);
  }}
  .rule-title{{font-family:'Cinzel',serif;font-size:1.15rem;font-weight:700;color:var(--gold);margin-bottom:.4rem}}
  .rule-text{{font-size:.95rem;white-space:pre-line;color:var(--ink)}}
  .theme-toggle{{
    position:fixed;bottom:1rem;right:1rem;background:var(--surface);
    border:1px solid var(--line-strong);padding:.5rem .9rem;border-radius:30px;
    font-family:'Cinzel',serif;font-size:.85rem;color:var(--ink);cursor:pointer;
    box-shadow:var(--shadow);
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Magias de Tormenta20</h1>
    <div class="subtitle">Conferência Estruturada · Capítulo 4 (Edição Jogo do Ano)</div>
  </header>

  <div class="controls">
    <div class="search-row">
      <input type="text" id="q" class="search-box" placeholder="Buscar por magia, escola, efeito, aprimoramento...">
    </div>
    <div class="filter-group">
      <span class="filter-label">Círculo:</span>
      <button class="pill active" onclick="setCirculo(this, '')">Todos</button>
      <button class="pill" onclick="setCirculo(this, '1')">1º</button>
      <button class="pill" onclick="setCirculo(this, '2')">2º</button>
      <button class="pill" onclick="setCirculo(this, '3')">3º</button>
      <button class="pill" onclick="setCirculo(this, '4')">4º</button>
      <button class="pill" onclick="setCirculo(this, '5')">5º</button>
    </div>
    <div class="filter-group">
      <span class="filter-label">Tipo:</span>
      <button class="pill active" onclick="setTipo(this, '')">Todos</button>
      <button class="pill" onclick="setTipo(this, 'arcana')">Arcana</button>
      <button class="pill" onclick="setTipo(this, 'divina')">Divina</button>
      <button class="pill" onclick="setTipo(this, 'universal')">Universal</button>
    </div>
    <div class="filter-group">
      <span class="filter-label">Escola:</span>
      <button class="pill active" onclick="setEscola(this, '')">Todas</button>
      <button class="pill" onclick="setEscola(this, 'Abjuração')">Abjuração</button>
      <button class="pill" onclick="setEscola(this, 'Adivinhação')">Adivinhação</button>
      <button class="pill" onclick="setEscola(this, 'Convocação')">Convocação</button>
      <button class="pill" onclick="setEscola(this, 'Encantamento')">Encantamento</button>
      <button class="pill" onclick="setEscola(this, 'Evocação')">Evocação</button>
      <button class="pill" onclick="setEscola(this, 'Ilusão')">Ilusão</button>
      <button class="pill" onclick="setEscola(this, 'Necromancia')">Necromancia</button>
      <button class="pill" onclick="setEscola(this, 'Transmutação')">Transmutação</button>
    </div>
  </div>

  <div class="stats-bar">
    <span id="contagem">Mostrando {len(magias)} magias e {len(regras)} regras</span>
    <span>Total no banco: {total}</span>
  </div>

  <div class="grid" id="grid">
"""

    # Gerar cards de regras
    for r in regras:
        html += f"""
    <div class="card rule-card" data-tipo="regra" data-name="{r['titulo'].lower()}">
      <div class="rule-title">📜 {r['titulo']}</div>
      <div class="rule-text">{r['texto']}</div>
      <div class="card-footer">Capítulo 4: Magia · pág. {r['pagina']}</div>
    </div>
"""

    # Gerar cards de magias
    for m in magias:
        circ = f"{m['circulo']}º Círculo"
        pm = f"{m['custo_pm']} PM"
        
        apr_html = ""
        if m.get("aprimoramentos"):
            apr_items = "".join(
                f'<div class="apr-item"><span class="apr-cost">{a["custo"]}:</span> {a["efeito"]}</div>'
                for a in m["aprimoramentos"]
            )
            apr_html = f"""
      <div class="apr-block">
        <div class="apr-title">Aprimoramentos</div>
        {apr_items}
      </div>
"""

        res_html = f'<div class="stat-item"><b>Resistência:</b> {m["resistencia"]}</div>' if m.get("resistencia") else ""
        alvo_html = f'<div class="stat-item"><b>{m["alvo_tipo"] or "Alvo"}:</b> {m["alvo"]}</div>' if m.get("alvo") else ""

        html += f"""
    <div class="card" data-tipo="{m['tipo']}" data-circulo="{m['circulo']}" data-escola="{m['escola']}" data-name="{m['nome'].lower()} {m['descricao'].lower()}">
      <div class="card-header">
        <div class="card-title">{m['nome']}</div>
        <div class="badges">
          <span class="badge circulo">{circ} ({pm})</span>
          <span class="badge escola">{m['escola']}</span>
          <span class="badge tipo">{m['tipo']}</span>
        </div>
      </div>
      <div class="stat-grid">
        <div class="stat-item"><b>Execução:</b> {m['execucao']}</div>
        <div class="stat-item"><b>Alcance:</b> {m['alcance']}</div>
        {alvo_html}
        <div class="stat-item"><b>Duração:</b> {m['duracao']}</div>
        {res_html}
      </div>
      <div class="desc">{m['descricao']}</div>
      {apr_html}
      <div class="card-footer">Tormenta20 · pág. {m['pagina']}</div>
    </div>
"""

    html += """
  </div>
</div>

<button class="theme-toggle" onclick="toggleTheme()">🌓 Alternar Tema</button>

<script>
let selCirculo = '';
let selTipo = '';
let selEscola = '';

function setCirculo(btn, val) {
  document.querySelectorAll('.filter-group:nth-child(2) .pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  selCirculo = val;
  filtrar();
}

function setTipo(btn, val) {
  document.querySelectorAll('.filter-group:nth-child(3) .pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  selTipo = val;
  filtrar();
}

function setEscola(btn, val) {
  document.querySelectorAll('.filter-group:nth-child(4) .pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  selEscola = val;
  filtrar();
}

function filtrar() {
  const q = document.getElementById('q').value.toLowerCase().trim();
  const cards = document.querySelectorAll('.card');
  let visiveis = 0;

  cards.forEach(c => {
    const isRule = c.dataset.tipo === 'regra';
    const cTipo = c.dataset.tipo || '';
    const cCirc = c.dataset.circulo || '';
    const cEsc = c.dataset.escola || '';
    const cText = c.dataset.name || '';

    let match = true;

    if (isRule) {
      if (selCirculo || selTipo || selEscola) match = false;
      if (q && !cText.includes(q)) match = false;
    } else {
      if (selCirculo && cCirc !== selCirculo) match = false;
      if (selTipo && cTipo !== selTipo && cTipo !== 'universal') match = false;
      if (selEscola && cEsc !== selEscola) match = false;
      if (q && !cText.includes(q)) match = false;
    }

    if (match) {
      c.style.display = 'flex';
      visiveis++;
    } else {
      c.style.display = 'none';
    }
  });

  document.getElementById('contagem').textContent = `Mostrando ${visiveis} itens`;
}

document.getElementById('q').addEventListener('input', filtrar);

function toggleTheme() {
  const root = document.documentElement;
  const current = root.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  localStorage.setItem('t20_theme', next);
}

const savedTheme = localStorage.getItem('t20_theme');
if (savedTheme) {
  document.documentElement.setAttribute('data-theme', savedTheme);
}
</script>
</body>
</html>
"""

    OUT_HTML.write_text(html, encoding="utf-8")
    return OUT_HTML


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    out = gerar_html()
    print(f"HTML de conferência gerado com sucesso em {out} ({out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
