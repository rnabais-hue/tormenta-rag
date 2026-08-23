# -*- coding: utf-8 -*-
r"""Gera a ferramenta de conferência visual offline dados/condicoes.html
a partir de dados/condicoes.json.
"""
import json
import sys
import io
from pathlib import Path

BASE = Path(__file__).parent
IN_JSON = BASE / "dados" / "condicoes.json"
OUT_HTML = BASE / "dados" / "condicoes.html"


def gerar_html():
    data = json.loads(IN_JSON.read_text(encoding="utf-8"))
    condicoes = data.get("condicoes", [])
    regra_geral = data.get("regra_geral", {})
    total = len(condicoes)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Condições de Tormenta20</title>
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
  .wrap{{max-width:1100px;margin:0 auto}}
  header{{margin-bottom:2rem;text-align:center;position:relative}}
  h1{{font-family:'Cinzel',serif;font-size:2.2rem;letter-spacing:.04em;color:var(--accent);font-weight:700}}
  .subtitle{{color:var(--ink-soft);font-size:1rem;margin-top:.3rem}}
  .theme-toggle{{
    position:absolute;top:0;right:0;background:var(--surface);border:1px solid var(--line-strong);
    color:var(--ink);padding:.4rem .8rem;border-radius:6px;cursor:pointer;font-family:inherit;font-size:.85rem;
  }}
  .panel{{
    background:var(--surface);border:1px solid var(--line);border-radius:12px;
    padding:1.25rem 1.5rem;box-shadow:var(--shadow);margin-bottom:2rem;
  }}
  .search-row{{display:flex;gap:.75rem;margin-bottom:1rem;flex-wrap:wrap}}
  .search-input{{
    flex:1;min-width:260px;background:var(--surface-2);border:1px solid var(--line-strong);
    color:var(--ink);padding:.6rem 1rem;border-radius:8px;font-family:inherit;font-size:1rem;
  }}
  .search-input:focus{{outline:none;border-color:var(--accent)}}
  .filter-row{{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}}
  .filter-label{{font-size:.85rem;color:var(--ink-faint);text-transform:uppercase;letter-spacing:.05em;margin-right:.25rem}}
  .chip{{
    background:var(--surface-2);border:1px solid var(--line);color:var(--ink-soft);
    padding:.3rem .75rem;border-radius:20px;font-size:.85rem;cursor:pointer;user-select:none;
    transition:all .15s ease;
  }}
  .chip:hover{{border-color:var(--accent);color:var(--accent)}}
  .chip.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:1.25rem}}
  .card{{
    background:var(--surface);border:1px solid var(--line);border-radius:10px;
    padding:1.2rem;box-shadow:var(--shadow);display:flex;flex-direction:column;
    transition:transform .15s ease,border-color .15s ease;
  }}
  .card:hover{{transform:translateY(-2px);border-color:var(--accent-soft)}}
  .card-head{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.5rem;gap:.5rem}}
  .card-title{{font-family:'Cinzel',serif;font-size:1.25rem;font-weight:700;color:var(--accent)}}
  .badge{{
    font-family:'Cinzel',serif;font-size:.75rem;padding:.2rem .5rem;border-radius:4px;
    background:var(--surface-2);border:1px solid var(--line-strong);color:var(--ink-soft);font-weight:600;
  }}
  .badge.mental{{background:#5c3a7a22;border-color:#5c3a7a66;color:#7a4b9e}}
  .badge.movimento{{background:#1e5a7a22;border-color:#1e5a7a66;color:#2979a8}}
  .badge.sentidos{{background:#7a5a1e22;border-color:#7a5a1e66;color:#a8823c}}
  .badge.metabolismo{{background:#2e6b3e22;border-color:#2e6b3e66;color:#3b8c50}}
  .badge.medo{{background:#8c232322;border-color:#8c232366;color:#b83030}}
  .badge.cansaço{{background:#8a5e3c22;border-color:#8a5e3c66;color:#a87449}}
  .badge.veneno{{background:#597a1e22;border-color:#597a1e66;color:#77a329}}
  .badge.metamorfose{{background:#7a1e6b22;border-color:#7a1e6b66;color:#a82993}}
  .badge.piora{{background:#9d293322;border-color:#9d293366;color:var(--accent)}}
  .card-piora{{
    font-size:.85rem;color:var(--accent);margin-bottom:.6rem;
    padding:.3rem .6rem;background:var(--accent-ghost);border-radius:4px;border-left:3px solid var(--accent);
  }}
  .card-desc{{font-size:.95rem;color:var(--ink);flex:1;margin-bottom:.75rem;text-align:justify}}
  .card-foot{{display:flex;justify-content:space-between;align-items:center;font-size:.8rem;color:var(--ink-faint);border-top:1px solid var(--line);padding-top:.5rem;margin-top:auto}}
  .counter{{font-size:.9rem;color:var(--ink-faint);margin-bottom:1rem;text-align:right}}
  .regra-geral{{
    grid-column:1 / -1;background:var(--surface-2);border:1px solid var(--gold);
    border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;box-shadow:var(--shadow);
  }}
  .regra-geral h2{{font-family:'Cinzel',serif;font-size:1.3rem;color:var(--gold);margin-bottom:.5rem}}
  .regra-geral p{{font-size:.95rem;color:var(--ink-soft);line-height:1.6;white-space:pre-line}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <button class="theme-toggle" onclick="toggleTheme()">Modo Claro/Escuro</button>
    <h1>Condições de Tormenta20</h1>
    <div class="subtitle">Apêndice: Lista de Condições (págs. 400–401) — {total} Condições Estruturadas</div>
  </header>

  <div class="panel">
    <div class="search-row">
      <input type="text" id="search" class="search-input" placeholder="Buscar por condição, efeito, tipo ou regra..." oninput="filtrar()">
    </div>
    <div class="filter-row">
      <span class="filter-label">Tipo de Efeito:</span>
      <span class="chip active" data-tipo="todos" onclick="setTipo('todos')">Todos ({total})</span>
      <span class="chip" data-tipo="Mental" onclick="setTipo('Mental')">Mental</span>
      <span class="chip" data-tipo="Movimento" onclick="setTipo('Movimento')">Movimento</span>
      <span class="chip" data-tipo="Sentidos" onclick="setTipo('Sentidos')">Sentidos</span>
      <span class="chip" data-tipo="Metabolismo" onclick="setTipo('Metabolismo')">Metabolismo</span>
      <span class="chip" data-tipo="Cansaço" onclick="setTipo('Cansaço')">Cansaço</span>
      <span class="chip" data-tipo="Medo" onclick="setTipo('Medo')">Medo</span>
      <span class="chip" data-tipo="Veneno" onclick="setTipo('Veneno')">Veneno</span>
      <span class="chip" data-tipo="Metamorfose" onclick="setTipo('Metamorfose')">Metamorfose</span>
      <span class="chip" data-tipo="Geral" onclick="setTipo('Geral')">Gerais</span>
      <span class="chip" data-tipo="escalam" onclick="setTipo('escalam')" style="margin-left:auto;border-color:var(--accent);color:var(--accent)">Escalam ⬆</span>
    </div>
  </div>

  <div class="counter" id="count">Mostrando {total} de {total} condições</div>

  <div class="regra-geral" id="bloco-regra">
    <h2>{regra_geral.get('titulo', 'Regras Gerais de Condições')}</h2>
    <p>{regra_geral.get('texto', '')}</p>
  </div>

  <div class="grid" id="grid">
"""

    for c in condicoes:
        nome = c["nome"]
        tipo = c["tipo_efeito"]
        piora = c["piora_para"]
        desc = c["descricao"]
        pag = c["pagina"]
        tipo_slug = tipo.lower()
        
        badge_cls = f"badge {tipo_slug}" if tipo != "Geral" else "badge"
        
        piora_html = f'<div class="card-piora"><strong>Piora para:</strong> {piora}</div>' if piora else ""
        
        html += f"""
    <div class="card" data-nome="{nome.lower()}" data-tipo="{tipo}" data-piora="{piora.lower()}" data-desc="{desc.lower()}">
      <div class="card-head">
        <div class="card-title">{nome}</div>
        <span class="{badge_cls}">{tipo}</span>
      </div>
      {piora_html}
      <div class="card-desc">{desc}</div>
      <div class="card-foot">
        <span>Apêndice</span>
        <span>Pág. {pag}</span>
      </div>
    </div>"""

    html += """
  </div>
</div>

<script>
let currentTipo = 'todos';

function setTipo(tipo) {
  currentTipo = tipo;
  document.querySelectorAll('.chip').forEach(c => {
    c.classList.toggle('active', c.getAttribute('data-tipo') === tipo);
  });
  filtrar();
}

function filtrar() {
  const q = document.getElementById('search').value.toLowerCase().trim();
  const cards = document.querySelectorAll('.card');
  let visiveis = 0;

  cards.forEach(c => {
    const nome = c.getAttribute('data-nome');
    const tipo = c.getAttribute('data-tipo');
    const piora = c.getAttribute('data-piora');
    const desc = c.getAttribute('data-desc');

    let matchTipo = false;
    if (currentTipo === 'todos') matchTipo = true;
    else if (currentTipo === 'escalam') matchTipo = piora.length > 0;
    else matchTipo = (tipo === currentTipo);

    let matchQ = true;
    if (q) {
      matchQ = nome.includes(q) || desc.includes(q) || tipo.toLowerCase().includes(q) || piora.includes(q);
    }

    if (matchTipo && matchQ) {
      c.style.display = 'flex';
      visiveis++;
    } else {
      c.style.display = 'none';
    }
  });

  const regra = document.getElementById('bloco-regra');
  if (q || currentTipo !== 'todos') {
    regra.style.display = 'none';
  } else {
    regra.style.display = 'block';
  }

  document.getElementById('count').textContent = `Mostrando ${visiveis} de ${cards.length} condições`;
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

const saved = localStorage.getItem('theme');
if (saved) document.documentElement.setAttribute('data-theme', saved);
</script>
</body>
</html>"""

    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML de conferência gerado com sucesso em {OUT_HTML} ({round(len(html)/1024, 1)} KB)")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    gerar_html()


if __name__ == "__main__":
    main()
