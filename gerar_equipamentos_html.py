# -*- coding: utf-8 -*-
r"""Gera a ferramenta de conferência visual offline dados/equipamentos.html
a partir de dados/equipamentos.json.
"""
import sys, io, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

IN_JSON = Path(__file__).parent / "dados" / "equipamentos.json"
OUT_HTML = Path(__file__).parent / "dados" / "equipamentos.html"


def gerar_html():
    with open(IN_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    armas = data.get("armas", [])
    armaduras = data.get("armaduras_escudos", [])
    gerais = data.get("itens_gerais", [])
    melhorias = data.get("melhorias_superiores", [])
    materiais = data.get("materiais_especiais", [])
    regras = data.get("regras_procedurais", [])

    total = len(armas) + len(armaduras) + len(gerais) + len(melhorias) + len(materiais) + len(regras)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Equipamentos de Tormenta20</title>
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
  *{{box-sizing:border-box}}
  body{{margin:0; background:var(--ground); color:var(--ink);
    font-family:"Spectral",Georgia,serif; font-size:16px; line-height:1.55; -webkit-font-smoothing:antialiased}}
  .wrap{{max-width:1160px; margin:0 auto; padding:clamp(16px,3vw,34px)}}
  header{{display:flex; flex-wrap:wrap; align-items:flex-end; gap:14px 20px; justify-content:space-between;
    border-bottom:2px solid var(--line-strong); padding-bottom:18px; margin-bottom:20px}}
  .brand h1{{font-family:"Cinzel",serif; font-weight:700; letter-spacing:.02em;
    font-size:clamp(1.4rem,3.4vw,2.15rem); margin:0; line-height:1.05; text-wrap:balance}}
  .brand .kicker{{font-family:"Cinzel",serif; letter-spacing:.26em; text-transform:uppercase;
    font-size:.62rem; color:var(--accent); font-weight:600; margin-bottom:.35em}}
  .brand p{{margin:.5em 0 0; color:var(--ink-soft); max-width:60ch; font-size:.92rem}}
  .hbtns{{display:flex; align-items:center; gap:10px}}
  .count{{font-family:"Cinzel",serif; font-size:.72rem; letter-spacing:.1em; text-transform:uppercase;
    color:var(--ink-faint); border:1px solid var(--line-strong); border-radius:999px; padding:6px 12px; white-space:nowrap}}
  .toggle{{font-family:"Spectral",serif; background:var(--surface); color:var(--ink-soft); cursor:pointer;
    border:1px solid var(--line-strong); border-radius:999px; padding:7px 14px; font-size:.85rem}}
  .toggle:hover{{color:var(--accent); border-color:var(--accent)}}
  .toolbar{{display:flex; flex-direction:column; gap:12px; margin-bottom:24px}}
  .row1{{display:flex; flex-wrap:wrap; gap:12px; align-items:center}}
  .search{{position:relative; flex:1 1 240px; min-width:200px}}
  .search input{{width:100%; font-family:"Spectral",serif; font-size:1rem; color:var(--ink);
    background:var(--surface); border:1px solid var(--line-strong); border-radius:10px; padding:11px 14px 11px 14px}}
  .chips{{display:flex; flex-wrap:wrap; gap:6px}}
  .chip{{font-family:"Cinzel",serif; font-weight:600; font-size:.72rem; letter-spacing:.03em; cursor:pointer;
    padding:7px 14px; border-radius:999px; border:1px solid var(--line-strong); background:var(--surface);
    color:var(--ink-soft); transition:.15s}}
  .chip:hover{{border-color:var(--accent); color:var(--accent)}}
  .chip.active{{background:var(--accent); color:#fff; border-color:var(--accent)}}
  .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(330px, 1fr)); gap:18px}}
  .card{{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:18px 20px;
    box-shadow:var(--shadow); display:flex; flex-direction:column; gap:12px; transition:.15s}}
  .card:hover{{border-color:var(--line-strong)}}
  .chead{{display:flex; justify-content:space-between; align-items:baseline; gap:8px; border-bottom:1px solid var(--line); padding-bottom:8px}}
  .cname{{font-family:"Cinzel",serif; font-size:1.15rem; font-weight:700; color:var(--accent); margin:0}}
  .cprice{{font-family:"Cinzel",serif; font-size:.85rem; font-weight:700; color:var(--gold); white-space:nowrap}}
  .badges{{display:flex; flex-wrap:wrap; gap:5px}}
  .badge{{font-size:.72rem; font-family:"Cinzel",serif; text-transform:uppercase; letter-spacing:.04em;
    padding:3px 8px; border-radius:6px; background:var(--surface-2); border:1px solid var(--line); color:var(--ink-soft)}}
  .badge-acc{{background:var(--accent-ghost); border-color:var(--accent-soft); color:var(--accent)}}
  .badge-gold{{background:var(--preq-bg); border-color:var(--gold); color:var(--preq)}}
  .stat-row{{display:flex; flex-wrap:wrap; gap:10px 14px; font-size:.85rem; background:var(--surface-2);
    padding:8px 12px; border-radius:8px; border:1px solid var(--line)}}
  .stat-item{{display:flex; gap:4px; align-items:baseline}}
  .stat-label{{font-family:"Cinzel",serif; font-size:.7rem; color:var(--ink-faint); text-transform:uppercase}}
  .stat-val{{font-weight:600; color:var(--ink)}}
  .cdesc{{font-size:.9rem; color:var(--ink-soft); line-height:1.5; margin:0; flex-grow:1}}
  .cfoot{{font-size:.75rem; color:var(--ink-faint); display:flex; justify-content:space-between; margin-top:auto; padding-top:6px}}
  .empty{{grid-column:1/-1; text-align:center; padding:40px 20px; color:var(--ink-faint)}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <div class="kicker">Tormenta20 — Edição Jogo do Ano</div>
      <h1>Equipamentos & Itens</h1>
      <p>Capítulo 3 completo: Armas, Armaduras, Escudos, Itens Gerais, Melhorias, Materiais Especiais e Regras.</p>
    </div>
    <div class="hbtns">
      <span class="count" id="countDisplay">{total} Itens</span>
      <button class="toggle" onclick="toggleTheme()">🌓 Tema</button>
    </div>
  </header>

  <div class="toolbar">
    <div class="row1">
      <div class="search">
        <input type="text" id="searchInput" placeholder="Buscar por nome, categoria, efeito ou stats..." oninput="filtrar()">
      </div>
    </div>
    <div class="chips" id="catChips">
      <button class="chip active" onclick="setCategory('todas', this)">Todos ({total})</button>
      <button class="chip" onclick="setCategory('arma', this)">Armas ({len(armas)})</button>
      <button class="chip" onclick="setCategory('armadura', this)">Armaduras & Escudos ({len(armaduras)})</button>
      <button class="chip" onclick="setCategory('item_geral', this)">Itens Gerais ({len(gerais)})</button>
      <button class="chip" onclick="setCategory('melhoria_superior', this)">Melhorias ({len(melhorias)})</button>
      <button class="chip" onclick="setCategory('material_especial', this)">Materiais Especiais ({len(materiais)})</button>
      <button class="chip" onclick="setCategory('regra_equipamento', this)">Regras ({len(regras)})</button>
    </div>
  </div>

  <div class="grid" id="grid">
"""

    # 1. Armas
    for a in armas:
        is_mun = a.get("categoria") == "municao"
        html += f"""
    <div class="card" data-cat="arma" data-name="{a['nome'].lower()}" data-text="{(a.get('descricao','') + ' ' + a.get('proficiencia','') + ' ' + a.get('empunhadura','')).lower()}">
      <div class="chead">
        <h3 class="cname">{a['nome']}</h3>
        <span class="cprice">{a.get('preco','—')}</span>
      </div>
      <div class="badges">
        <span class="badge badge-acc">{'Munição' if is_mun else 'Arma ' + a.get('proficiencia','')}</span>
        <span class="badge">{a.get('empunhadura','')}</span>
        <span class="badge">{a.get('espacos','1')} esp.</span>
      </div>
      """
        if not is_mun:
            html += f"""
      <div class="stat-row">
        <div class="stat-item"><span class="stat-label">Dano:</span><span class="stat-val">{a.get('dano','—')}</span></div>
        <div class="stat-item"><span class="stat-label">Crítico:</span><span class="stat-val">{a.get('critico','—')}</span></div>
        <div class="stat-item"><span class="stat-label">Alcance:</span><span class="stat-val">{a.get('alcance','—')}</span></div>
        <div class="stat-item"><span class="stat-label">Tipo:</span><span class="stat-val">{a.get('tipo_dano','—')}</span></div>
      </div>
      """
        html += f"""
      <p class="cdesc">{a.get('descricao') or '—'}</p>
      <div class="cfoot"><span>Página {a.get('pagina', 150)}</span><span>Capítulo 3</span></div>
    </div>
    """

    # 2. Armaduras e Escudos
    for ar in armaduras:
        html += f"""
    <div class="card" data-cat="armadura" data-name="{ar['nome'].lower()}" data-text="{(ar.get('descricao','') + ' ' + ar.get('subcategoria','')).lower()}">
      <div class="chead">
        <h3 class="cname">{ar['nome']}</h3>
        <span class="cprice">{ar.get('preco','—')}</span>
      </div>
      <div class="badges">
        <span class="badge badge-acc">{ar.get('subcategoria','Armadura')}</span>
        <span class="badge">{ar.get('espacos','2')} esp.</span>
      </div>
      <div class="stat-row">
        <div class="stat-item"><span class="stat-label">Defesa:</span><span class="stat-val">{ar.get('defesa','—')}</span></div>
        <div class="stat-item"><span class="stat-label">Penalidade:</span><span class="stat-val">{ar.get('penalidade','0')}</span></div>
      </div>
      <p class="cdesc">{ar.get('descricao') or '—'}</p>
      <div class="cfoot"><span>Página {ar.get('pagina', 159)}</span><span>Capítulo 3</span></div>
    </div>
    """

    # 3. Itens Gerais
    for g in gerais:
        html += f"""
    <div class="card" data-cat="item_geral" data-name="{g['nome'].lower()}" data-text="{(g.get('descricao','') + ' ' + g.get('subcategoria','')).lower()}">
      <div class="chead">
        <h3 class="cname">{g['nome']}</h3>
        <span class="cprice">{g.get('preco','—')}</span>
      </div>
      <div class="badges">
        <span class="badge badge-gold">{g.get('subcategoria','Geral')}</span>
        <span class="badge">{g.get('espacos','—')} esp.</span>
      </div>
      <p class="cdesc">{g.get('descricao') or '—'}</p>
      <div class="cfoot"><span>Página {g.get('pagina', 162)}</span><span>Capítulo 3</span></div>
    </div>
    """

    # 4. Melhorias
    for m in melhorias:
        html += f"""
    <div class="card" data-cat="melhoria_superior" data-name="{m['nome'].lower()}" data-text="{(m.get('descricao_completa','') + ' ' + m.get('aplica_a','')).lower()}">
      <div class="chead">
        <h3 class="cname">{m['nome']}</h3>
        <span class="cprice">Superior</span>
      </div>
      <div class="badges">
        <span class="badge badge-acc">Melhoria</span>
        <span class="badge">Aplica-se: {m.get('aplica_a','Geral')}</span>
      </div>
      <p class="cdesc">{m.get('descricao_completa') or m.get('efeito_resumido','')}</p>
      <div class="cfoot"><span>Página {m.get('pagina', 171)}</span><span>Capítulo 3</span></div>
    </div>
    """

    # 5. Materiais Especiais
    for mat in materiais:
        html += f"""
    <div class="card" data-cat="material_especial" data-name="{mat['nome'].lower()}" data-text="{(mat.get('descricao','') + ' ' + mat.get('efeito_arma','') + ' ' + mat.get('efeito_armadura_escudo','')).lower()}">
      <div class="chead">
        <h3 class="cname">{mat['nome']}</h3>
        <span class="cprice">Material Especial</span>
      </div>
      <p class="cdesc"><strong>Descrição:</strong> {mat.get('descricao','')}</p>
      <p class="cdesc"><strong>Em Armas:</strong> {mat.get('efeito_arma','—')}</p>
      <p class="cdesc"><strong>Em Armaduras/Escudos:</strong> {mat.get('efeito_armadura_escudo','—')}</p>
      <p class="cdesc"><strong>Em Esotéricos:</strong> {mat.get('efeito_esoterico','—')}</p>
      <div class="cfoot"><span>Página {mat.get('pagina', 172)}</span><span>Capítulo 3</span></div>
    </div>
    """

    # 6. Regras
    for r in regras:
        html += f"""
    <div class="card" data-cat="regra_equipamento" data-name="{r['titulo'].lower()}" data-text="{r.get('texto','').lower()}">
      <div class="chead">
        <h3 class="cname">{r['titulo']}</h3>
        <span class="cprice">Regra</span>
      </div>
      <p class="cdesc">{r.get('texto','')}</p>
      <div class="cfoot"><span>Página {r.get('pagina', 146)}</span><span>Capítulo 3</span></div>
    </div>
    """

    html += """
  </div>
</div>

<script>
let currentCat = 'todas';

function setCategory(cat, el) {
  currentCat = cat;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  filtrar();
}

function filtrar() {
  const q = document.getElementById('searchInput').value.toLowerCase().trim();
  const cards = document.querySelectorAll('.card');
  let visible = 0;

  cards.forEach(c => {
    const cat = c.getAttribute('data-cat');
    const name = c.getAttribute('data-name');
    const text = c.getAttribute('data-text');

    const matchCat = (currentCat === 'todas' || cat === currentCat);
    const matchSearch = (!q || name.includes(q) || text.includes(q));

    if (matchCat && matchSearch) {
      c.style.display = 'flex';
      visible++;
    } else {
      c.style.display = 'none';
    }
  });

  document.getElementById('countDisplay').innerText = visible + ' Itens';
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
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

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[SUCESSO] Gerado {OUT_HTML} ({len(html)} bytes)")


if __name__ == "__main__":
    gerar_html()
