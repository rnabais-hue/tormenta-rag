# -*- coding: utf-8 -*-
r"""Gera um visualizador HTML offline (dados/regras_jogo.html) para as Regras de Jogo e Parceiros de Tormenta20.
Permite busca em tempo real, filtros por categoria (Manobras, Ações, Táticas, Descanso, Dano, Parceiros, Habilidades)
e visualização interativa dos cards com fórmulas e regras.
"""
import io
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
DADOS_JSON = BASE / "dados" / "regras_jogo.json"
OUT_HTML = BASE / "dados" / "regras_jogo.html"


def gerar_html():
    banco = json.loads(DADOS_JSON.read_text(encoding="utf-8"))

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tormenta20 — Regras de Jogo & Parceiros (Capítulo 5)</title>
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
  .card-title {{ font-size: 1.25rem; font-weight: bold; color: var(--text); }}
  .badge {{ background: var(--badge-bg); color: var(--badge-text); font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; font-weight: 600; text-transform: uppercase; }}
  .badge.manobra {{ background: rgba(225, 29, 72, 0.2); color: #f43f5e; border: 1px solid #f43f5e; }}
  .badge.acao {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }}
  .badge.tatica {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }}
  .badge.parceiro {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #c084fc; }}
  .badge.descanso {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #34d399; }}
  
  .card-field {{ font-size: 0.9rem; line-height: 1.5; }}
  .card-field strong {{ color: var(--highlight); }}
  .formula-box {{ background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--accent); font-family: monospace; font-size: 0.85rem; }}
  
  .tier-list {{ display: flex; flex-direction: column; gap: 8px; margin-top: 6px; }}
  .tier-item {{ background: rgba(0,0,0,0.15); padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; border-left: 3px solid var(--purple); }}
  .tier-title {{ font-weight: bold; color: var(--purple); }}
  
  .table-box {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.85rem; }}
  .table-box th, .table-box td {{ border: 1px solid var(--border); padding: 6px 10px; text-align: left; }}
  .table-box th {{ background: rgba(0,0,0,0.2); color: var(--highlight); }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🛡️ Tormenta20 — Regras de Jogo & Parceiros</h1>
    <button class="theme-toggle" onclick="toggleTheme()">🌓 Alternar Tema</button>
  </header>

  <div class="controls">
    <input type="text" id="search" class="search-box" placeholder="Buscar por manobra, ação, regra, teste, bônus, CD ou parceiro..." oninput="filtrar()">
    <div class="filter-row">
      <span class="filter-label">Categoria:</span>
      <button class="chip active" onclick="setCategoria('todas', this)">Todas</button>
      <button class="chip" onclick="setCategoria('manobra', this)">Manobras de Combate</button>
      <button class="chip" onclick="setCategoria('acao', this)">Ações de Combate</button>
      <button class="chip" onclick="setCategoria('tatica', this)">Modificadores Táticos</button>
      <button class="chip" onclick="setCategoria('descanso', this)">Ferimentos & Descanso</button>
      <button class="chip" onclick="setCategoria('parceiro', this)">Parceiros / Aliados</button>
      <button class="chip" onclick="setCategoria('habilidade', this)">Habilidades Universais</button>
      <button class="chip" onclick="setCategoria('dano', this)">Tipos de Dano</button>
    </div>
  </div>

  <div class="counter" id="counter">Exibindo todos os cards</div>
  <div class="grid" id="cards-container"></div>
</div>

<script>
const DADOS = {json.dumps(banco, ensure_ascii=False)};

let categoriaAtual = 'todas';

function renderCards() {{
  const container = document.getElementById('cards-container');
  container.innerHTML = '';
  const termo = document.getElementById('search').value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');

  let itens = [];

  // Manobras
  DADOS.manobras.forEach(m => {{
    itens.push({{
      tipo: 'manobra',
      titulo: 'Manobra: ' + m.nome,
      badge: 'Manobra',
      corBadge: 'manobra',
      pagina: m.pagina,
      html: `
        <div class="formula-box"><strong>Teste:</strong> ${{m.teste}}</div>
        <div class="card-field"><strong>Ação:</strong> ${{m.tipo_acao}}</div>
        <div class="card-field"><strong>Alcance:</strong> ${{m.alcance}}</div>
        <div class="card-field">${{m.efeito}}</div>
      `,
      searchTxt: (m.nome + ' ' + m.teste + ' ' + m.efeito + ' manobra').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    }});
  }});

  // Ações
  DADOS.acoes.forEach(a => {{
    let exHtml = a.exemplos.map(e => `<div class="card-field"><strong>${{e.nome}}:</strong> ${{e.descricao}}</div>`).join('');
    itens.push({{
      tipo: 'acao',
      titulo: a.categoria,
      badge: 'Ação',
      corBadge: 'acao',
      pagina: a.pagina,
      html: `
        <div class="card-field">${{a.resumo}}</div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:6px;">${{exHtml}}</div>
      `,
      searchTxt: (a.categoria + ' ' + a.resumo + ' ' + a.exemplos.map(e => e.nome + ' ' + e.descricao).join(' ')).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    }});
  }});

  // Táticas
  DADOS.modificadores_taticos.forEach(t => {{
    itens.push({{
      tipo: 'tatica',
      titulo: 'Tática: ' + t.titulo,
      badge: 'Tática',
      corBadge: 'tatica',
      pagina: t.pagina,
      html: `
        <div class="card-field">${{t.resumo}}</div>
        <div class="card-field" style="white-space:pre-line;">${{t.regras}}</div>
      `,
      searchTxt: (t.titulo + ' ' + t.resumo + ' ' + t.regras).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    }});
  }});

  // Ferimentos & Descanso
  DADOS.ferimentos_descanso.forEach(f => {{
    let extra = '';
    if (f.tabela_descanso) {{
      extra = `
        <table class="table-box">
          <thead><tr><th>Condição</th><th>PV</th><th>PM</th><th>Exemplo</th></tr></thead>
          <tbody>
            ${{f.tabela_descanso.map(d => `<tr><td><strong>${{d.condicao}}</strong></td><td>${{d.recuperacao_pv}}</td><td>${{d.recuperacao_pm}}</td><td>${{d.exemplo}}</td></tr>`).join('')}}
          </tbody>
        </table>
      `;
    }}
    itens.push({{
      tipo: 'descanso',
      titulo: f.titulo,
      badge: 'Regras',
      corBadge: 'descanso',
      pagina: f.pagina,
      html: `
        <div class="card-field">${{f.resumo}}</div>
        ${{f.regras ? `<div class="card-field" style="white-space:pre-line;">${{f.regras}}</div>` : ''}}
        ${{extra}}
      `,
      searchTxt: (f.titulo + ' ' + f.resumo + ' ' + (f.regras || '') + (f.tabela_descanso ? JSON.stringify(f.tabela_descanso) : '')).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    }});
  }});

  // Parceiros
  DADOS.parceiros.forEach(p => {{
    itens.push({{
      tipo: 'parceiro',
      titulo: 'Parceiro: ' + p.nome,
      badge: 'Parceiro',
      corBadge: 'parceiro',
      pagina: p.pagina,
      html: `
        <div class="card-field"><em>${{p.descricao_papel}}</em></div>
        <div class="tier-list">
          <div class="tier-item"><span class="tier-title">Iniciante:</span> ${{p.iniciante}}</div>
          <div class="tier-item"><span class="tier-title">Veterano:</span> ${{p.veterano}}</div>
          <div class="tier-item"><span class="tier-title">Mestre:</span> ${{p.mestre}}</div>
        </div>
      `,
      searchTxt: (p.nome + ' ' + p.descricao_papel + ' ' + p.iniciante + ' ' + p.veterano + ' ' + p.mestre).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    }});
  }});

  // Habilidades Universais
  DADOS.habilidades_universais.forEach(h => {{
    itens.push({{
      tipo: 'habilidade',
      titulo: 'Habilidade Universal: ' + h.nome,
      badge: 'Habilidade',
      corBadge: 'acao',
      pagina: h.pagina,
      html: `<div class="card-field">${{h.descricao}}</div>`,
      searchTxt: (h.nome + ' ' + h.descricao).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    }});
  }});

  // Tipos de Dano
  DADOS.tipos_dano.forEach(d => {{
    itens.push({{
      tipo: 'dano',
      titulo: d.categoria,
      badge: 'Dano',
      corBadge: 'manobra',
      pagina: d.pagina,
      html: `
        <div class="card-field">${{d.descricao}}</div>
        <ul style="margin-left:20px;margin-top:6px;font-size:0.9rem;">
          ${{d.tipos.map(t => `<li>${{t}}</li>`).join('')}}
        </ul>
      `,
      searchTxt: (d.categoria + ' ' + d.descricao + ' ' + d.tipos.join(' ')).toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
    }});
  }});

  let visiveis = 0;
  itens.forEach(item => {{
    const matchCat = (categoriaAtual === 'todas' || item.tipo === categoriaAtual);
    const matchTermo = (!termo || item.searchTxt.includes(termo));

    if (matchCat && matchTermo) {{
      visiveis++;
      const div = document.createElement('div');
      div.className = 'card';
      div.innerHTML = `
        <div class="card-header">
          <div class="card-title">${{item.titulo}}</div>
          <span class="badge ${{item.corBadge}}">${{item.badge}} (pág. ${{item.pagina}})</span>
        </div>
        ${{item.html}}
      `;
      container.appendChild(div);
    }}
  }});

  document.getElementById('counter').innerText = `Exibindo ${{visiveis}} de ${{itens.length}} cards de regras`;
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
    print(f"Visualizador HTML de Regras gerado com sucesso em {OUT_HTML} ({tam/1024:.1f} KB)")


if __name__ == "__main__":
    main()
