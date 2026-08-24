# -*- coding: utf-8 -*-
r"""Gera um visualizador HTML offline (dados/mundo_arton.html) para o Mundo de Arton de Tormenta20.
Permite busca em tempo real, filtros por categoria (Reinos do Reinado, Potências, Além do Reinado, Ermos, Ilhas, Lugares Lendários)
e visualização rica dos cards geopolíticos e linha do tempo de Arton.
"""
import io
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
DADOS_JSON = BASE / "dados" / "mundo_arton.json"
OUT_HTML = BASE / "dados" / "mundo_arton.html"


def gerar_html():
    banco = json.loads(DADOS_JSON.read_text(encoding="utf-8"))

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tormenta20 — O Mundo de Arton (Geografia, Reinos e Lore)</title>
<style>
  :root {{
    --bg: #0f172a;
    --card-bg: #1e293b;
    --border: #334155;
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --accent: #e11d48;
    --accent-hover: #be123c;
    --badge-bg: #374151;
    --badge-text: #e2e8f0;
    --highlight: #38bdf8;
    --gold: #f59e0b;
    --green: #10b981;
    --purple: #a855f7;
  }}
  [data-theme="light"] {{
    --bg: #f8fafc;
    --card-bg: #ffffff;
    --border: #cbd5e1;
    --text: #0f172a;
    --text-muted: #64748b;
    --accent: #e11d48;
    --accent-hover: #be123c;
    --badge-bg: #e2e8f0;
    --badge-text: #1e293b;
    --highlight: #0284c7;
    --gold: #d97706;
    --green: #059669;
    --purple: #7c3aed;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  body {{ background-color: var(--bg); color: var(--text); padding: 24px; transition: background-color 0.2s; }}
  .container {{ max-width: 1300px; margin: 0 auto; }}
  header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }}
  h1 {{ font-size: 1.8rem; color: var(--accent); display: flex; align-items: center; gap: 10px; }}
  .theme-toggle {{ background: var(--card-bg); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }}
  
  .controls {{ display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }}
  .search-box {{ width: 100%; padding: 12px 18px; border-radius: 8px; border: 1px solid var(--border); background: var(--card-bg); color: var(--text); font-size: 1rem; }}
  .filter-row {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
  .filter-label {{ font-size: 0.85rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-right: 4px; }}
  .chip {{ background: var(--card-bg); border: 1px solid var(--border); color: var(--text); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; cursor: pointer; transition: all 0.15s; }}
  .chip:hover, .chip.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
  
  .counter {{ font-size: 0.9rem; color: var(--text-muted); margin-bottom: 16px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px; }}
  
  .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
  .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }}
  .card-title {{ font-size: 1.3rem; font-weight: bold; color: var(--text); }}
  .card-subtitle {{ font-size: 0.85rem; color: var(--gold); font-style: italic; }}
  
  .badge {{ background: var(--badge-bg); color: var(--badge-text); font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; font-weight: 600; text-transform: uppercase; }}
  .badge.reinado {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }}
  .badge.potencia {{ background: rgba(225, 29, 72, 0.2); color: #f43f5e; border: 1px solid #f43f5e; }}
  .badge.alem {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #34d399; }}
  .badge.ermos {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }}
  .badge.ilhas {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #c084fc; }}
  .badge.lendario {{ background: rgba(236, 72, 153, 0.2); color: #f472b6; border: 1px solid #f472b6; }}
  
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: rgba(0,0,0,0.15); padding: 10px; border-radius: 8px; font-size: 0.85rem; }}
  .info-item strong {{ color: var(--highlight); display: block; font-size: 0.75rem; text-transform: uppercase; }}
  
  .card-section {{ font-size: 0.88rem; line-height: 1.5; }}
  .card-section strong {{ color: var(--highlight); }}
  .hook-box {{ background: rgba(225, 29, 72, 0.08); border-left: 3px solid var(--accent); padding: 8px 12px; border-radius: 4px; font-size: 0.85rem; }}
  
  .timeline-section {{ margin-top: 40px; padding-top: 24px; border-top: 1px solid var(--border); }}
  .timeline-title {{ font-size: 1.4rem; color: var(--gold); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
  .timeline-list {{ display: flex; flex-direction: column; gap: 12px; }}
  .timeline-item {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; display: flex; gap: 16px; align-items: center; }}
  .timeline-year {{ font-weight: bold; color: var(--accent); min-width: 110px; font-size: 1rem; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🗺️ Tormenta20 — O Mundo de Arton</h1>
    <button class="theme-toggle" onclick="toggleTheme()">🌓 Alternar Tema</button>
  </header>

  <div class="controls">
    <input type="text" id="search" class="search-box" placeholder="Buscar por reino, capital, regente, deus, cidade ou gancho de aventura..." oninput="filtrar()">
    <div class="filter-row">
      <span class="filter-label">Filtros:</span>
      <button class="chip active" onclick="setCategoria('todas', this)">Todas as Regiões</button>
      <button class="chip" onclick="setCategoria('Reino do Reinado', this)">Reinos do Reinado</button>
      <button class="chip" onclick="setCategoria('Grande Potência', this)">Grandes Potências</button>
      <button class="chip" onclick="setCategoria('Além do Reinado', this)">Além do Reinado</button>
      <button class="chip" onclick="setCategoria('Ermos e Montanhas', this)">Ermos & Montanhas</button>
      <button class="chip" onclick="setCategoria('Ilhas e Mares', this)">Ilhas & Mares</button>
      <button class="chip" onclick="setCategoria('Lugar Lendário', this)">Lugares Lendários</button>
    </div>
  </div>

  <div class="counter" id="counter">Exibindo todas as regiões</div>
  <div class="grid" id="cards-container"></div>

  <div class="timeline-section">
    <h2 class="timeline-title">⏳ Linha do Tempo e Marcos Históricos de Arton</h2>
    <div class="timeline-list">
      {"" .join([f'<div class="timeline-item"><div class="timeline-year">{m["ano"]}</div><div>{m["evento"]}</div></div>' for m in banco["linha_do_tempo"]])}
    </div>
  </div>
</div>

<script>
const DADOS = {json.dumps(banco, ensure_ascii=False)};

let categoriaAtual = 'todas';

function getBadgeClass(tipo) {{
  if (tipo === 'Reino do Reinado') return 'reinado';
  if (tipo === 'Grande Potência') return 'potencia';
  if (tipo === 'Além do Reinado') return 'alem';
  if (tipo === 'Ermos e Montanhas') return 'ermos';
  if (tipo === 'Ilhas e Mares') return 'ilhas';
  if (tipo === 'Lugar Lendário') return 'lendario';
  return 'reinado';
}}

function renderCards() {{
  const container = document.getElementById('cards-container');
  container.innerHTML = '';
  const termo = document.getElementById('search').value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');

  let visiveis = 0;

  DADOS.regioes.forEach(r => {{
    const matchCat = (categoriaAtual === 'todas' || r.tipo_regiao === categoriaAtual);
    const searchTxt = (r.nome + ' ' + r.capital + ' ' + r.regente_lider + ' ' + r.divindades_principais.join(' ') + ' ' + r.locais_destaque.join(' ') + ' ' + r.cultura_sociedade + ' ' + r.ganchos_aventura).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
    const matchTermo = (!termo || searchTxt.includes(termo));

    if (matchCat && matchTermo) {{
      visiveis++;
      const div = document.createElement('div');
      div.className = 'card';
      div.innerHTML = `
        <div class="card-header">
          <div>
            <div class="card-title">${{r.nome}}</div>
            <div class="card-subtitle">${{r.titulo_descritivo}}</div>
          </div>
          <span class="badge ${{getBadgeClass(r.tipo_regiao)}}">${{r.tipo_regiao}} (pág. ${{r.pagina}})</span>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <strong>Capital / Sede</strong>
            ${{r.capital}}
          </div>
          <div class="info-item">
            <strong>Regente / Líder</strong>
            ${{r.regente_lider}}
          </div>
          <div class="info-item" style="grid-column: span 2;">
            <strong>Divindades Principais</strong>
            ${{r.divindades_principais.join(', ')}}
          </div>
        </div>

        <div class="card-section">
          <strong>Pontos de Interesse:</strong> ${{r.locais_destaque.join(' • ')}}
        </div>

        <div class="card-section">
          <strong>Cultura & Sociedade:</strong> ${{r.cultura_sociedade}}
        </div>

        <div class="hook-box">
          <strong>⚔️ Ganchos de Aventura:</strong> ${{r.ganchos_aventura}}
        </div>
      `;
      container.appendChild(div);
    }}
  }});

  document.getElementById('counter').innerText = `Exibindo ${{visiveis}} de ${{DADOS.regioes.length}} regiões/reinos`;
}}

function filtrar() {{
  renderCards();
}}

function setCategoria(cat, el) {{
  categoriaAtual = cat;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  renderCards();
}}

function toggleTheme() {{
  const b = document.body;
  if (b.getAttribute('data-theme') === 'light') {{
    b.removeAttribute('data-theme');
  }} else {{
    b.setAttribute('data-theme', 'light');
  }}
}}

renderCards();
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    return len(html)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    tam = gerar_html()
    print(f"Visualizador HTML do Mundo de Arton gerado com sucesso em {OUT_HTML} ({tam/1024:.1f} KB)")


if __name__ == "__main__":
    main()
