# -*- coding: utf-8 -*-
r"""Gera a ferramenta de conferência visual offline dados/ameacas.html
a partir de dados/ameacas.json.
"""
import json
import sys
import io
from pathlib import Path

BASE = Path(__file__).parent
IN_JSON = BASE / "dados" / "ameacas.json"
OUT_HTML = BASE / "dados" / "ameacas.html"


def gerar_html():
    data = json.loads(IN_JSON.read_text(encoding="utf-8"))
    criaturas = data.get("criaturas", [])
    regras = data.get("regras", [])
    total = len(criaturas)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Bestiário de Tormenta20 (Ameaças)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700;800&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap">
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
    font-family:'Spectral',Georgia,serif;font-size:15px;line-height:1.5;
    padding:2rem 1rem 4rem;min-height:100vh;
  }}
  .wrap{{max-width:1250px;margin:0 auto}}
  header{{margin-bottom:2rem;text-align:center;position:relative}}
  h1{{font-family:'Cinzel',serif;font-size:2.4rem;letter-spacing:.04em;color:var(--accent);font-weight:800}}
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
    flex:1;min-width:280px;background:var(--surface-2);border:1px solid var(--line-strong);
    color:var(--ink);padding:.6rem 1rem;border-radius:8px;font-family:inherit;font-size:1rem;
  }}
  .search-input:focus{{outline:none;border-color:var(--accent)}}
  .filter-row{{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-bottom:.6rem}}
  .filter-label{{font-size:.8rem;color:var(--ink-faint);text-transform:uppercase;letter-spacing:.05em;min-width:70px}}
  .chip{{
    background:var(--surface-2);border:1px solid var(--line);color:var(--ink-soft);
    padding:.25rem .65rem;border-radius:16px;font-size:.8rem;cursor:pointer;user-select:none;
    transition:all .15s ease;
  }}
  .chip:hover{{border-color:var(--accent);color:var(--accent)}}
  .chip.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:1.25rem}}
  
  .card{{
    background:var(--surface);border:1px solid var(--line);border-radius:10px;
    padding:1.2rem;box-shadow:var(--shadow);display:flex;flex-direction:column;
    transition:transform .15s ease,border-color .15s ease;
  }}
  .card:hover{{transform:translateY(-2px);border-color:var(--accent-soft)}}
  .card-head{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.4rem;gap:.5rem}}
  .card-title{{font-family:'Cinzel',serif;font-size:1.3rem;font-weight:700;color:var(--accent);line-height:1.2}}
  .card-nd{{
    font-family:'Cinzel',serif;font-size:.9rem;font-weight:800;
    padding:.2rem .6rem;background:var(--accent-ghost);border:1px solid var(--accent-soft);
    border-radius:4px;color:var(--accent);white-space:nowrap;
  }}
  .card-subhead{{font-style:italic;color:var(--ink-soft);font-size:.85rem;margin-bottom:.6rem}}
  .stat-grid{{
    display:grid;grid-template-columns:repeat(4,1fr);gap:.4rem;background:var(--surface-2);
    padding:.5rem;border-radius:6px;margin-bottom:.6rem;border:1px solid var(--line);font-size:.85rem;
  }}
  .stat-item{{text-align:center}}
  .stat-item strong{{display:block;font-size:.7rem;text-transform:uppercase;color:var(--ink-faint)}}
  
  .card-section{{margin-bottom:.5rem;font-size:.85rem}}
  .card-section strong{{color:var(--accent);font-family:'Cinzel',serif;font-size:.8rem;text-transform:uppercase}}
  .hab-item{{margin-bottom:.4rem;padding-left:.5rem;border-left:2px solid var(--gold)}}
  .hab-item strong{{color:var(--ink);font-weight:600}}
  
  .attr-row{{
    display:flex;justify-content:space-between;background:var(--surface-2);
    padding:.3rem .5rem;border-radius:4px;font-size:.8rem;font-family:'Cinzel',serif;font-weight:600;margin-bottom:.5rem;
  }}
  .card-foot{{
    display:flex;justify-content:space-between;align-items:center;font-size:.75rem;
    color:var(--ink-faint);border-top:1px solid var(--line);padding-top:.4rem;margin-top:auto;
  }}
  .counter{{font-size:.9rem;color:var(--ink-faint);margin-bottom:1rem;text-align:right}}
  
  .regra-bloco{{
    grid-column:1 / -1;background:var(--surface-2);border:1px solid var(--gold);
    border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;box-shadow:var(--shadow);
  }}
  .regra-bloco h2{{font-family:'Cinzel',serif;font-size:1.3rem;color:var(--gold);margin-bottom:.5rem}}
  .regra-bloco p{{font-size:.9rem;color:var(--ink-soft);line-height:1.6;white-space:pre-line}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <button class="theme-toggle" onclick="toggleTheme()">Modo Claro/Escuro</button>
    <h1>Bestiário de Tormenta20</h1>
    <div class="subtitle">Capítulo 7: Ameaças — {total} Criaturas & Estatísticas Estruturadas</div>
  </header>

  <div class="panel">
    <div class="search-row">
      <input type="text" id="search" class="search-input" placeholder="Buscar por criatura, ND, grupo, ataque, habilidade, defesa ou perícia..." oninput="filtrar()">
    </div>
    <div class="filter-row">
      <span class="filter-label">Grupo:</span>
      <span class="chip active" data-filter="grupo" data-val="todos" onclick="setFilter('grupo','todos')">Todos ({total})</span>
      <span class="chip" data-filter="grupo" data-val="Masmorras" onclick="setFilter('grupo','Masmorras')">Masmorras (11)</span>
      <span class="chip" data-filter="grupo" data-val="Ermos" onclick="setFilter('grupo','Ermos')">Ermos (18)</span>
      <span class="chip" data-filter="grupo" data-val="Puristas" onclick="setFilter('grupo','Puristas')">Puristas (7)</span>
      <span class="chip" data-filter="grupo" data-val="Reino dos Mortos" onclick="setFilter('grupo','Reino dos Mortos')">Mortos-Vivos (8)</span>
      <span class="chip" data-filter="grupo" data-val="Duyshidakk" onclick="setFilter('grupo','Duyshidakk')">Duyshidakk (8)</span>
      <span class="chip" data-filter="grupo" data-val="Sszzaazitas" onclick="setFilter('grupo','Sszzaazitas')">Sszzaazitas (9)</span>
      <span class="chip" data-filter="grupo" data-val="Trolls nobres" onclick="setFilter('grupo','Trolls nobres')">Trolls (5)</span>
      <span class="chip" data-filter="grupo" data-val="Dragões" onclick="setFilter('grupo','Dragões')">Dragões (7)</span>
      <span class="chip" data-filter="grupo" data-val="Tormenta" onclick="setFilter('grupo','Tormenta')">Tormenta (7)</span>
    </div>
    <div class="filter-row">
      <span class="filter-label">Faixa ND:</span>
      <span class="chip active" data-filter="nd" data-val="todos" onclick="setFilter('nd','todos')">Todos</span>
      <span class="chip" data-filter="nd" data-val="baixo" onclick="setFilter('nd','baixo')">Iniciante (ND 1/4–1)</span>
      <span class="chip" data-filter="nd" data-val="medio" onclick="setFilter('nd','medio')">Veterano (ND 2–4)</span>
      <span class="chip" data-filter="nd" data-val="alto" onclick="setFilter('nd','alto')">Campeão (ND 5–9)</span>
      <span class="chip" data-filter="nd" data-val="epico" onclick="setFilter('nd','epico')">Lendário (ND 10–20)</span>
    </div>
  </div>

  <div class="counter" id="count">Mostrando {total} de {total} criaturas</div>

  <div class="grid" id="grid">
"""

    for r in regras:
        html += f"""
    <div class="regra-bloco">
      <h2>{r['titulo']}</h2>
      <p>{r['texto']}</p>
    </div>"""

    for c in criaturas:
        nome = c["nome"]
        grupo = c["grupo"]
        nd = c["nd"]
        tipo = c["tipo_criatura"]
        subtipo = f" ({c['subtipo']})" if c.get("subtipo") else ""
        tamanho = c["tamanho"]
        papel = f" • {c['papel']}" if c.get("papel") != "Normal" else ""
        
        defesa = c["defesa"]
        pv = c["pv"]
        pm = c["pm"]
        pm_str = f" • PM {pm}" if pm > 0 else ""
        desl = c["deslocamento"]
        ini = c["iniciativa"]
        per = c["percepcao"]
        sent = c["sentidos"]
        fort = c["fortitude"]
        ref = c["reflexos"]
        von = c["vontade"]
        res = f"<br><strong>Resistências:</strong> {c['resistencias']}" if c.get("resistencias") else ""
        
        cac = f"<div class='card-section'><strong>Corpo a Corpo:</strong> {c['corpo_a_corpo']}</div>" if c.get("corpo_a_corpo") else ""
        dist = f"<div class='card-section'><strong>À Distância:</strong> {c['distancia']}</div>" if c.get("distancia") else ""
        
        habs_html = ""
        if c.get("habilidades"):
            habs_html = "<div class='card-section'><strong>Habilidades:</strong>"
            for h in c["habilidades"]:
                habs_html += f"<div class='hab-item'><strong>{h['nome']}:</strong> {h['descricao']}</div>"
            habs_html += "</div>"
            
        atrs = c.get("atributos", {})
        attr_html = ""
        if atrs:
            attr_html = f"""<div class='attr-row'>
              <span>FOR {atrs.get('for', '-')}</span>
              <span>DES {atrs.get('des', '-')}</span>
              <span>CON {atrs.get('con', '-')}</span>
              <span>INT {atrs.get('int', '-')}</span>
              <span>SAB {atrs.get('sab', '-')}</span>
              <span>CAR {atrs.get('car', '-')}</span>
            </div>"""
            
        peric = f"<div class='card-section'><strong>Perícias:</strong> {c['pericias']}</div>" if c.get("pericias") else ""
        equip = f"<div class='card-section'><strong>Equipamento:</strong> {c['equipamento']}</div>" if c.get("equipamento") else ""
        tes = f"<div class='card-section'><strong>Tesouro:</strong> {c['tesouro']}</div>" if c.get("tesouro") else ""
        
        # Categorizar ND para filtro
        nd_cat = "baixo"
        if nd in ["1/4", "1/2", "1"]: nd_cat = "baixo"
        elif nd in ["2", "3", "4"]: nd_cat = "medio"
        elif nd in ["5", "6", "7", "8", "9"]: nd_cat = "alto"
        else: nd_cat = "epico"

        html += f"""
    <div class="card" data-nome="{nome.lower()}" data-grupo="{grupo}" data-nd="{nd}" data-ndcat="{nd_cat}" data-tipo="{tipo.lower()}" data-all="{nome.lower()} {grupo.lower()} {tipo.lower()} {c.get('corpo_a_corpo', '').lower()} {c.get('distancia', '').lower()} {c.get('resistencias', '').lower()}">
      <div class="card-head">
        <div class="card-title">{nome}</div>
        <span class="card-nd">ND {nd}</span>
      </div>
      <div class="card-subhead">{tipo}{subtipo} {tamanho}{papel} • {grupo}</div>
      <div class="stat-grid">
        <div class="stat-item"><strong>Defesa</strong>{defesa}</div>
        <div class="stat-item"><strong>PV / PM</strong>{pv}{pm_str}</div>
        <div class="stat-item"><strong>Inic / Per</strong>{ini} / {per}</div>
        <div class="stat-item"><strong>Fort/Ref/Von</strong>{fort}/{ref}/{von}</div>
      </div>
      <div class="card-section"><strong>Deslocamento:</strong> {desl} • <strong>Sentidos:</strong> {sent}{res}</div>
      {cac}
      {dist}
      {habs_html}
      {attr_html}
      {peric}
      {equip}
      {tes}
      <div class="card-foot">
        <span>Capítulo 7: Ameaças</span>
        <span>Pág. {c['pagina']}</span>
      </div>
    </div>"""

    html += """
  </div>
</div>

<script>
let currentGrupo = 'todos';
let currentND = 'todos';

function setFilter(tipo, val) {
  if (tipo === 'grupo') currentGrupo = val;
  if (tipo === 'nd') currentND = val;

  document.querySelectorAll(`.chip[data-filter="${tipo}"]`).forEach(c => {
    c.classList.toggle('active', c.getAttribute('data-val') === val);
  });
  filtrar();
}

function filtrar() {
  const q = document.getElementById('search').value.toLowerCase().trim();
  const cards = document.querySelectorAll('.card');
  let visiveis = 0;

  cards.forEach(c => {
    const grupo = c.getAttribute('data-grupo');
    const ndcat = c.getAttribute('data-ndcat');
    const allTxt = c.getAttribute('data-all');

    let matchGrupo = (currentGrupo === 'todos' || grupo === currentGrupo);
    let matchND = (currentND === 'todos' || ndcat === currentND);
    let matchQ = (!q || allTxt.includes(q));

    if (matchGrupo && matchND && matchQ) {
      c.style.display = 'flex';
      visiveis++;
    } else {
      c.style.display = 'none';
    }
  });

  const regras = document.querySelectorAll('.regra-bloco');
  regras.forEach(r => {
    if (q || currentGrupo !== 'todos' || currentND !== 'todos') {
      r.style.display = 'none';
    } else {
      r.style.display = 'block';
    }
  });

  document.getElementById('count').textContent = `Mostrando ${visiveis} de ${cards.length} criaturas`;
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
