# -*- coding: utf-8 -*-
r"""
Interface web local de TESTES do RAG de Tormenta20 — só biblioteca padrão
(sem instalar nada). Carrega o índice + embedder UMA vez e sobe um servidor
em http://127.0.0.1:8000.

Uso:
  python interface.py           # abre em http://127.0.0.1:8000
  python interface.py -p 8080   # outra porta

A resposta é enviada em STREAMING (tokens fluindo): você vê o texto aparecer e
a conexão não é derrubada durante a geração lenta na CPU ('Failed to fetch').

Toda pergunta é registrada em logs/consultas.jsonl; cada resultado pode ser
marcado OK/Problema com nota em logs/avaliacoes.jsonl. Erros do servidor vão
para logs/servidor.log.

Pré-requisitos: ingestao.py já rodado e Ollama no ar (qwen3:8b).
"""

import argparse
import json
import traceback
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from perguntar import (
    carregar, consultar, buscar, montar_prompt, iter_ollama,
    fontes_de_hits, registrar_log, LOG_DIR, MODELO_LLM, TOP_K,
)

BASE = Path(__file__).parent
LOG_AVALIACOES = LOG_DIR / "avaliacoes.jsonl"
LOG_SERVIDOR = LOG_DIR / "servidor.log"

# carregado uma vez na subida do servidor
INDEX = CHUNKS = MODEL = META = None


def log_servidor(msg):
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_SERVIDOR, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')}  {msg}\n")


PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAG Tormenta20 — Testes</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto;
         padding: 1.5rem; line-height: 1.5; }
  h1 { font-size: 1.3rem; }
  textarea { width: 100%; font-size: 1rem; padding: .6rem; box-sizing: border-box; }
  .linha { display: flex; gap: .5rem; align-items: center; margin: .5rem 0; flex-wrap: wrap; }
  button { font-size: 1rem; padding: .5rem .9rem; cursor: pointer; }
  #resposta { white-space: pre-wrap; background: rgba(127,127,127,.1);
              padding: 1rem; border-radius: 8px; margin-top: 1rem; min-height: 1rem; }
  .fonte { border-left: 3px solid #888; padding: .3rem .6rem; margin: .4rem 0;
           font-size: .9rem; }
  .score { font-variant-numeric: tabular-nums; color: #888; }
  .previa { color: #999; font-size: .85rem; }
  #status { color: #888; font-style: italic; }
  .aval button { padding: .35rem .7rem; }
</style></head><body>
<h1>RAG Tormenta20 — bancada de testes</h1>
<p id="meta"></p>
<textarea id="q" rows="3" placeholder="Digite uma pergunta de regra... (Ctrl+Enter envia)"></textarea>
<div class="linha">
  <label>top-k: <input id="k" type="number" value="__TOPK__" min="1" max="20" style="width:4rem"></label>
  <button id="btn" onclick="perguntar()">Perguntar</button>
  <span id="status"></span>
</div>
<div id="resposta"></div>
<div id="fontes"></div>
<div class="linha aval" id="aval" style="display:none">
  <span>Este resultado:</span>
  <button onclick="avaliar('ok')">✓ OK</button>
  <button onclick="avaliar('problema')">✗ Problema</button>
  <input id="nota" placeholder="nota opcional (o que faltou / o que errou)" style="flex:1;min-width:12rem">
</div>
<script>
let ultima = null;
fetch('/meta').then(r=>r.json()).then(m=>{
  document.getElementById('meta').textContent =
    `${m.n_chunks} chunks · embedder ${m.modelo_embed} · LLM ${m.modelo_llm}`;
});
function renderFontes(fontes){
  document.getElementById('fontes').innerHTML = fontes.map(f =>
    `<div class="fonte"><b>[Fonte ${f.rank}]</b> ${f.secao} — pág. ${f.pagina}
     <span class="score">(sim=${f.score})</span>
     <div class="previa">${f.previa}…</div></div>`).join('');
}
async function perguntar() {
  const q = document.getElementById('q').value.trim();
  if (!q) return;
  const k = parseInt(document.getElementById('k').value) || 5;
  const btn = document.getElementById('btn');
  btn.disabled = true;
  document.getElementById('status').textContent = 'buscando trechos...';
  document.getElementById('resposta').textContent = '';
  document.getElementById('fontes').innerHTML = '';
  document.getElementById('aval').style.display = 'none';
  ultima = {pergunta: q, fontes: [], resposta: ''};
  try {
    const r = await fetch('/consultar', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({q, k})});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    while (true) {
      const {value, done} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream:true});
      let nl;
      while ((nl = buf.indexOf('\\n')) >= 0) {
        const linha = buf.slice(0, nl); buf = buf.slice(nl+1);
        if (!linha.trim()) continue;
        const ev = JSON.parse(linha);
        if (ev.tipo === 'fontes') {
          ultima.fontes = ev.fontes; renderFontes(ev.fontes);
          document.getElementById('status').textContent = 'gerando resposta...';
        } else if (ev.tipo === 'token') {
          ultima.resposta += ev.t;
          document.getElementById('resposta').textContent = ultima.resposta;
        } else if (ev.tipo === 'fim') {
          document.getElementById('status').textContent =
            `busca ${ev.seg_busca}s · geração ${ev.seg_geracao}s`;
        } else if (ev.tipo === 'erro') {
          throw new Error(ev.msg);
        }
      }
    }
    if (!ultima.resposta) document.getElementById('resposta').textContent = '(sem resposta)';
    document.getElementById('aval').style.display = 'flex';
    document.getElementById('nota').value = '';
  } catch(e) {
    document.getElementById('status').textContent =
      'erro: ' + e.message + ' — o servidor pode ter parado (a janela preta foi fechada?). Rode o atalho de novo.';
  } finally {
    btn.disabled = false;
  }
}
async function avaliar(veredito) {
  if (!ultima) return;
  const nota = document.getElementById('nota').value;
  await fetch('/avaliar', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({pergunta: ultima.pergunta, veredito, nota,
                          fontes: ultima.fontes, resposta: ultima.resposta})});
  document.getElementById('status').textContent = 'avaliação salva: ' + veredito;
  document.getElementById('aval').style.display = 'none';
}
document.getElementById('q').addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') perguntar();
});
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo_json(self):
        n = int(self.headers.get("Content-Length", 0))
        bruto = self.rfile.read(n) if n else b"{}"
        return json.loads(bruto.decode("utf-8"))

    def _linha(self, obj):
        """Envia um evento NDJSON e força o flush (mantém a conexão viva)."""
        self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
        self.wfile.flush()

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            html = PAGINA.replace("__TOPK__", str(TOP_K)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif self.path == "/meta":
            self._json({
                "n_chunks": META.get("n_chunks"),
                "modelo_embed": META.get("modelo_embed"),
                "modelo_llm": MODELO_LLM,
            })
        else:
            self._json({"erro": "rota desconhecida"}, 404)

    def _consultar_stream(self, q, k):
        """Executa a consulta e transmite resultado em NDJSON, logando ao fim."""
        import time
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        t0 = time.time()
        hits = buscar(q, INDEX, CHUNKS, MODEL, k)
        seg_busca = round(time.time() - t0, 2)
        fontes = fontes_de_hits(hits)
        self._linha({"tipo": "fontes", "fontes": fontes})

        resposta = ""
        t1 = time.time()
        if hits:
            try:
                for tok in iter_ollama(montar_prompt(q, hits)):
                    resposta += tok
                    self._linha({"tipo": "token", "t": tok})
            except Exception as e:  # erro ao falar com o Ollama
                log_servidor("ERRO Ollama: " + repr(e))
                self._linha({"tipo": "erro", "msg": "falha ao gerar (Ollama): " + str(e)})
        seg_geracao = round(time.time() - t1, 2)
        self._linha({"tipo": "fim", "seg_busca": seg_busca, "seg_geracao": seg_geracao})

        registrar_log({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "pergunta": q, "k": k,
            "modelo_embed": META.get("modelo_embed"), "modelo_llm": MODELO_LLM,
            "n_chunks_indice": META.get("n_chunks"),
            "resposta": resposta, "fontes": fontes,
            "seg_busca": seg_busca, "seg_geracao": seg_geracao,
        })

    def do_POST(self):
        try:
            dados = self._corpo_json()
            if self.path == "/consultar":
                q = (dados.get("q") or "").strip()
                k = int(dados.get("k") or TOP_K)
                if not q:
                    return self._json({"erro": "pergunta vazia"}, 400)
                self._consultar_stream(q, k)
            elif self.path == "/avaliar":
                dados["ts"] = datetime.now().isoformat(timespec="seconds")
                LOG_DIR.mkdir(exist_ok=True)
                with open(LOG_AVALIACOES, "a", encoding="utf-8") as f:
                    f.write(json.dumps(dados, ensure_ascii=False) + "\n")
                self._json({"ok": True})
            else:
                self._json({"erro": "rota desconhecida"}, 404)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # cliente fechou a aba/janela no meio — normal, não derruba o servidor
            log_servidor("cliente desconectou durante " + self.path)
        except Exception as e:  # noqa: BLE001
            log_servidor("ERRO em " + self.path + ": " + repr(e) + "\n" + traceback.format_exc())
            try:
                self._json({"erro": str(e)}, 500)
            except Exception:
                pass

    def log_message(self, *a):  # silencia log de acesso padrão do http.server
        pass


def main():
    global INDEX, CHUNKS, MODEL, META
    ap = argparse.ArgumentParser(description="Interface web de testes do RAG")
    ap.add_argument("-p", "--porta", type=int, default=8000)
    ap.add_argument("--sem-navegador", action="store_true")
    args = ap.parse_args()

    if not (BASE / "index" / "tormenta.faiss").exists():
        raise SystemExit("Índice não encontrado. Rode ingestao.py primeiro.")

    print("Carregando índice e embedder (uma vez)...")
    INDEX, CHUNKS, MODEL, META = carregar()
    print(f"  {META['n_chunks']} chunks | {META['modelo_embed']} | {MODELO_LLM}")

    url = f"http://127.0.0.1:{args.porta}"
    srv = ThreadingHTTPServer(("127.0.0.1", args.porta), Handler)
    log_servidor(f"servidor iniciado em {url}")
    print(f"Servindo em {url}  (Ctrl+C para parar)")
    print(f"Logs: {LOG_DIR}")
    if not args.sem_navegador:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando.")


if __name__ == "__main__":
    main()
