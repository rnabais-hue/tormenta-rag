# -*- coding: utf-8 -*-
r"""Gera um visualizador HTML offline (dados/mestre_classes.html) para as 14 Classes (Cap. 1) e Regras do Mestre (Cap. 6).
Permite busca em tempo real, filtros por categoria (14 Classes, Ambientes, Perigos, Doenças, Campanhas) e visualização de tabelas.
"""
import io
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
DADOS_JSON = BASE / "dados" / "mestre_classes.json"
OUT_HTML = BASE / "dados" / "mestre_classes.html"


def gerar_html():
    banco = json.loads(DADOS_JSON.read_text(encoding="utf-8"))

    todos_itens = []

    # 1. As 14 Classes
    for c in banco["classes"]:
        todos_itens.append({
            "nome": f"Classe: {c['nome']}",
            "categoria": "Ficha de Classe (Cap. 1)",
            "cat_filtro": "classes",
            "detalhe": f"Caminho: {c['caminhos']} | PV: {c['pv_inicial']} (+{c['pv_por_nivel']}) | PM: {c['pm_inicial']} (+{c['pm_por_nivel']})",
            "corpo": (
                f"• Proficiências: {c['proficiencias']}\n"
                f"• Perícias Básicas: {c['pericias_basicas']}\n\n"
                f"• Habilidades Automáticas:\n  - " + "\n  - ".join(c["habilidades_principais"]) + "\n\n"
                f"• Progressão Nível a Nível (1º–20º):\n  {c['progressao_tabela']}"
            ),
            "pagina": c["pagina"],
        })

    # 2. Regras do Mestre
    for m in banco["mestre_regras"]:
        todos_itens.append({
            "nome": m["nome"],
            "categoria": f"Regras do Mestre ({m['categoria'].replace('_', ' ').title()})",
            "cat_filtro": m["categoria"],
            "detalhe": "Capítulo 6: O Mestre",
            "corpo": m["texto"],
            "pagina": m["pagina"],
        })

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tormenta20 — Classes (Cap. 1) & O Mestre (Cap. 6)</title>
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
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 20px; }}
  
  .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
  .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }}
  .card-title {{ font-size: 1.3rem; font-weight: bold; color: var(--text); }}
  .card-subtitle {{ font-size: 0.85rem; color: var(--gold); font-weight: 600; }}
  
  .badge {{ background: var(--badge-bg); color: var(--badge-text); font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; font-weight: 600; text-transform: uppercase; }}
  .badge.classes {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }}
  .badge.ambientes {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #34d399; }}
  .badge.perigos_armadilhas {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }}
  .badge.doencas_venenos {{ background: rgba(225, 29, 72, 0.2); color: #f43f5e; border: 1px solid #f43f5e; }}
  .badge.campanhas {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #c084fc; }}
  
  .card-body {{ font-size: 0.88rem; line-height: 1.55; white-space: pre-wrap; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🛡️ Tormenta20 — 14 Classes & O Mestre</h1>
    <button class="theme-toggle" onclick="toggleTheme()">🌓 Alternar Tema</button>
  </header>

  <div class="controls">
    <input type="text" id="search" class="search-box" placeholder="Buscar por classe, PV/PM, perícia, ambiente, queda, afogamento, armadilha, doença ou regra..." oninput="filtrar()">
    <div class="filter-row">
      <span class="filter-label">Filtros:</span>
      <button class="chip active" onclick="setCategoria('todas', this)">Todos ({len(todos_itens)})</button>
      <button class="chip" onclick="setCategoria('classes', this)">14 Classes de T20 (14)</button>
      <button class="chip" onclick="setCategoria('ambientes', this)">Ambientes & Queda (3)</button>
      <button class="chip" onclick="setCategoria('perigos_armadilhas', this)">Perigos & Armadilhas (1)</button>
      <button class="chip" onclick="setCategoria('doencas_venenos', this)">Doenças & Venenos (1)</button>
      <button class="chip" onclick="setCategoria('campanhas', this)">Campanhas & Perseguições (1)</button>
    </div>
  </div>

  <div class="counter" id="counter">Exibindo todos os registros</div>
  <div class="grid" id="cards-container"></div>
</div>

<script>
const DADOS = {json.dumps(todos_itens, ensure_ascii=False)};

let categoriaAtual = 'todas';

function renderCards() {{
  const container = document.getElementById('cards-container');
  container.innerHTML = '';
  const termo = document.getElementById('search').value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');

  let visiveis = 0;

  DADOS.forEach(item => {{
    const matchCat = (categoriaAtual === 'todas' || item.cat_filtro === categoriaAtual);
    const searchTxt = (item.nome + ' ' + item.categoria + ' ' + item.detalhe + ' ' + item.corpo).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
    const matchTermo = (!termo || searchTxt.includes(termo));

    if (matchCat && matchTermo) {{
      visiveis++;
      const div = document.createElement('div');
      div.className = 'card';
      div.innerHTML = `
        <div class="card-header">
          <div>
            <div class="card-title">${{item.nome}}</div>
            <div class="card-subtitle">${{item.detalhe}}</div>
          </div>
          <span class="badge ${{item.cat_filtro}}">${{item.categoria}} (pág. ${{item.pagina}})</span>
        </div>
        <div class="card-body">${{item.corpo}}</div>
      `;
      container.appendChild(div);
    }}
  }});

  document.getElementById('counter').innerText = `Exibindo ${{visiveis}} de ${{DADOS.length}} registros`;
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
    print(f"Visualizador HTML gerado com sucesso em {OUT_HTML} ({tam/1024:.1f} KB)")


if __name__ == "__main__":
    main()
