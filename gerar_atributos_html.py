# -*- coding: utf-8 -*-
r"""Gera dados/atributos.html — ferramenta de conferência (offline) do início do
Capítulo 1: os 6 ATRIBUTOS (com perícias governadas), os 9 PASSOS de criação e o
método "Definindo atributos" (Pontos/Rolagens + tabela de custo).

Lê dados/atributos.json e dados/criacao_personagem.json; reaproveita o <style> da
poderes_classe.html e embute o JSON inline. Rode: python gerar_atributos_html.py
"""
import json, re
from pathlib import Path

BASE = Path(__file__).parent / "dados"
SRC_CSS = BASE / "poderes_classe.html"
OUT = BASE / "atributos.html"

CSS_EXTRA = """
  .cat{font-family:"Cinzel",serif; font-size:.6rem; letter-spacing:.08em; text-transform:uppercase;
    color:var(--accent); border:1px solid var(--accent-soft); border-radius:6px; padding:2px 7px}
  .sec{font-family:"Cinzel",serif; font-weight:600; font-size:1.05rem; color:var(--ink);
    margin:26px 0 12px; padding-bottom:6px; border-bottom:2px solid var(--line-strong)}
  ol.passos{margin:0; padding-left:0; list-style:none; counter-reset:p}
  ol.passos li{counter-increment:p; position:relative; padding:10px 0 10px 44px; border-bottom:1px solid var(--line)}
  ol.passos li::before{content:counter(p); position:absolute; left:0; top:9px; width:30px; height:30px;
    display:grid; place-items:center; font-family:"Cinzel",serif; font-weight:700; color:#fff;
    background:var(--accent); border-radius:50%}
  ol.passos b{font-family:"Cinzel",serif; font-weight:600; color:var(--ink)}
  ol.passos p{margin:3px 0 0; color:var(--ink-soft); font-size:.9rem}
  .tags{display:flex; flex-wrap:wrap; gap:5px; margin-top:8px}
  .tag{font-size:.78rem; color:var(--accent); border:1px solid var(--accent-soft); border-radius:6px; padding:2px 8px}
  .defbox{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:16px; box-shadow:var(--shadow)}
  .defbox p{margin:0 0 10px; color:var(--ink-soft); font-size:.92rem; line-height:1.55}
  table{border-collapse:collapse; width:100%; margin-top:8px; font-size:.9rem}
  th,td{text-align:left; padding:7px 10px; border-bottom:1px solid var(--line)}
  th{font-family:"Cinzel",serif; font-size:.62rem; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-faint)}
  td:first-child{font-weight:600; color:var(--ink)}
"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    css = SRC_CSS.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", css, re.S)
    style = m.group(1) if m else ""

    atributos = json.loads((BASE / "atributos.json").read_text(encoding="utf-8"))
    criacao = json.loads((BASE / "criacao_personagem.json").read_text(encoding="utf-8"))

    passos_html = "".join(
        f"<li><b>{esc(p['titulo'])}</b><p>{esc(p['descricao'])}</p></li>"
        for p in criacao["passos"])
    attr_html = "".join(
        f'<div class="card"><div class="ch"><h3>{esc(a["nome"])}</h3>'
        f'<span class="cat">{esc(a["abrev"])}</span></div>'
        f'<p style="color:var(--ink-soft);font-size:.92rem;margin:0 0 6px">{esc(a["descricao"])}</p>'
        f'<div class="tags">' + "".join(f'<span class="tag">{esc(p)}</span>'
                                        for p in a["pericias_governadas"]) + "</div></div>"
        for a in atributos)
    linhas = "".join(
        f"<tr><td>{esc(r.get('atributo',''))}</td><td>{esc(r.get('custo',''))}</td>"
        f"<td>{esc(r.get('rolagem',''))}</td></tr>" for r in criacao["tabela_custo"])
    definindo = esc(criacao["definindo_atributos"]).replace("\n", "<br>")

    html = f"""<title>Construção de Personagem — Tormenta20</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>{style}{CSS_EXTRA}</style>

<div class="wrap">
  <header>
    <div class="brand">
      <div class="kicker">Índice estruturado · Capítulo 1</div>
      <h1>Construção de Personagem</h1>
      <p>Os 6 atributos (com as perícias que governam), os 9 passos de criação e o método de definição de atributos (págs 22–23). Confira contra o livro.</p>
    </div>
    <div class="hbtns"><button class="toggle" id="theme" type="button">◐ Tema</button></div>
  </header>

  <div class="sec">Os 9 passos</div>
  <ol class="passos">{passos_html}</ol>

  <div class="sec">Os 6 atributos e as perícias que governam</div>
  <div class="cards">{attr_html}</div>

  <div class="sec">Definindo seus atributos</div>
  <div class="defbox">
    <p>{definindo}</p>
    <table><thead><tr><th>Atributo</th><th>Custo (pontos)</th><th>Rolagem (4d6)</th></tr></thead>
    <tbody>{linhas}</tbody></table>
  </div>

  <footer>Fonte: Tormenta20 — Edição Jogo do Ano · uso pessoal para estudo · Capítulo 1, págs 22–23</footer>
</div>

<script>
document.getElementById("theme").onclick=()=>{{
  const cur=document.documentElement.getAttribute("data-theme");
  const now = cur==="dark" ? "light" : cur==="light" ? "dark"
    : (matchMedia("(prefers-color-scheme:dark)").matches ? "light" : "dark");
  document.documentElement.setAttribute("data-theme", now);
}};
</script>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"OK -> {OUT.name} ({len(atributos)} atributos, {len(criacao['passos'])} passos, "
          f"{len(criacao['tabela_custo'])} linhas de tabela, {len(html)} bytes)")


if __name__ == "__main__":
    main()
