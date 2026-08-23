# -*- coding: utf-8 -*-
r"""
Camada de GERAÇÃO plugável — desacopla o gerador da recuperação (perguntar.py).

Motivação (arquitetura): RAG = recuperação (bge-m3 + FAISS, local, sempre igual)
× geração (quem redige lendo o contexto). Hoje a geração é cravada no qwen3:8b via
Ollama. Este módulo torna o gerador um BACKEND TROCÁVEL atrás de uma única interface
— mesmo (prompt, instrucao) entra, texto sai — para permitir, sem reescrever o RAG:
  - ollama-local   (default): qwen3:8b via Ollama local (offline, CPU) — o de hoje.
  - ollama-remoto  : um Ollama num host com GPU (ex.: 14B) — mais forte, mais rápido.
  - api-claude     : Claude via API (nuvem) — o teto de qualidade. ⚠️ envia o contexto
                     (trechos do livro) para fora; use ciente dos direitos autorais.

Escolha do backend por variável de ambiente `TORMENTA_GERADOR`; cada backend tem
suas próprias variáveis (abaixo). A interface é compatível com o uso atual em
perguntar.py (iter_* para streaming, gerar() para one-shot), então a "fiação" depois
é só trocar as chamadas de perguntar_ollama/iter_ollama por gerar/iter_gerar.

Variáveis de ambiente:
  TORMENTA_GERADOR            ollama-local (default) | ollama-remoto | api-claude
  TORMENTA_OLLAMA_URL         default http://127.0.0.1:11434/api/chat
  TORMENTA_OLLAMA_MODELO      default qwen3:8b
  TORMENTA_OLLAMA_REMOTO_URL  URL do Ollama remoto (obrigatório p/ ollama-remoto)
  TORMENTA_OLLAMA_REMOTO_MODELO  default qwen3:14b
  TORMENTA_API_MODELO         default claude-sonnet-5 (confirme o id atual)
  ANTHROPIC_API_KEY           chave da API (obrigatória p/ api-claude)

Uso (self-test):
  python geradores.py                      # mostra o backend ativo e a config
  python geradores.py "diga olá em 5 palavras"   # gera com o backend ativo
"""

import os
import sys
import json

import requests

TIMEOUT = 600


def backend_ativo():
    """Nome do backend selecionado (env TORMENTA_GERADOR), default ollama-local."""
    return os.environ.get("TORMENTA_GERADOR", "ollama-local").strip().lower()


# ---------------------------------------------------------------- Ollama (local/remoto)
def _ollama_conf():
    """(url, modelo) conforme o backend ativo. ollama-remoto exige URL explícita."""
    b = backend_ativo()
    if b == "ollama-remoto":
        url = os.environ.get("TORMENTA_OLLAMA_REMOTO_URL")
        if not url:
            raise RuntimeError("ollama-remoto exige TORMENTA_OLLAMA_REMOTO_URL "
                               "(ex.: http://SEU_HOST:11434/api/chat).")
        modelo = os.environ.get("TORMENTA_OLLAMA_REMOTO_MODELO", "qwen3:14b")
    else:
        url = os.environ.get("TORMENTA_OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
        modelo = os.environ.get("TORMENTA_OLLAMA_MODELO", "qwen3:8b")
    return url, modelo


def _payload_ollama(prompt, instrucao, modelo, stream, temperatura):
    return {
        "model": modelo,
        "messages": [
            {"role": "system", "content": instrucao},
            {"role": "user", "content": prompt},
        ],
        "think": False,                     # desliga o 'thinking' (mais rápido)
        "stream": stream,
        "options": {"temperature": temperatura},
    }


def _iter_ollama(prompt, instrucao, temperatura):
    url, modelo = _ollama_conf()
    resp = requests.post(url, json=_payload_ollama(prompt, instrucao, modelo, True, temperatura),
                         stream=True, timeout=TIMEOUT)
    resp.raise_for_status()
    for linha in resp.iter_lines():
        if not linha:
            continue
        dado = json.loads(linha)
        if "message" in dado and dado["message"].get("content"):
            yield dado["message"]["content"]
        if dado.get("done"):
            break


def _gerar_ollama(prompt, instrucao, temperatura):
    url, modelo = _ollama_conf()
    resp = requests.post(url, json=_payload_ollama(prompt, instrucao, modelo, False, temperatura),
                         timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


# ---------------------------------------------------------------- Claude API (nuvem)
def _cliente_anthropic():
    """Importa o SDK sob demanda (não instala nada). Erros claros se faltar."""
    try:
        from anthropic import Anthropic
    except ModuleNotFoundError as exc:
        raise RuntimeError("Backend api-claude exige o pacote 'anthropic' "
                           "(instale com aprovação: pip install anthropic).") from exc
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Backend api-claude exige ANTHROPIC_API_KEY no ambiente.")
    return Anthropic()


def _api_modelo():
    return os.environ.get("TORMENTA_API_MODELO", "claude-sonnet-5")


def _iter_api(prompt, instrucao, temperatura):
    cli = _cliente_anthropic()
    with cli.messages.stream(model=_api_modelo(), max_tokens=1500, system=instrucao,
                             temperature=temperatura,
                             messages=[{"role": "user", "content": prompt}]) as stream:
        for texto in stream.text_stream:
            yield texto


def _gerar_api(prompt, instrucao, temperatura):
    cli = _cliente_anthropic()
    msg = cli.messages.create(model=_api_modelo(), max_tokens=1500, system=instrucao,
                              temperature=temperatura,
                              messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


# ---------------------------------------------------------------- interface pública
_ITER = {"ollama-local": _iter_ollama, "ollama-remoto": _iter_ollama, "api-claude": _iter_api}
_ONESHOT = {"ollama-local": _gerar_ollama, "ollama-remoto": _gerar_ollama, "api-claude": _gerar_api}


def iter_gerar(prompt, instrucao, temperatura=0.2):
    """Gera token a token (streaming) com o backend ativo. yield de pedaços de texto."""
    b = backend_ativo()
    if b not in _ITER:
        raise RuntimeError(f"TORMENTA_GERADOR desconhecido: {b!r} "
                           f"(use: {', '.join(_ITER)}).")
    yield from _ITER[b](prompt, instrucao, temperatura)


def gerar(prompt, instrucao, stream=False, temperatura=0.2):
    """Gera a resposta completa. Se stream=True, imprime os tokens enquanto chegam
    (comportamento da CLI) e devolve o texto acumulado."""
    b = backend_ativo()
    if not stream:
        if b not in _ONESHOT:
            raise RuntimeError(f"TORMENTA_GERADOR desconhecido: {b!r}.")
        return _ONESHOT[b](prompt, instrucao, temperatura)
    partes = []
    for tok in iter_gerar(prompt, instrucao, temperatura):
        partes.append(tok)
        print(tok, end="", flush=True)
    print()
    return "".join(partes)


def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    b = backend_ativo()
    print(f"Backend ativo: {b}")
    if b.startswith("ollama"):
        url, modelo = _ollama_conf()
        print(f"  url={url} | modelo={modelo}")
    elif b == "api-claude":
        print(f"  modelo={_api_modelo()} | ANTHROPIC_API_KEY set: {bool(os.environ.get('ANTHROPIC_API_KEY'))}")
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        instrucao = "Você é um assistente conciso. Responda em português."
        print("\n--- resposta ---")
        gerar(prompt, instrucao, stream=True)


if __name__ == "__main__":
    main()
