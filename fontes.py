"""Registro canônico das FONTES (livros) do RAG de Tormenta20.

Fonte-de-verdade dos rótulos de procedência. Cada chunk do índice guarda apenas
o *id* da fonte (ex.: fonte="nucleo"); o rótulo humano exibido na citação
("Ameaças de Arton, pág. 12") é resolvido aqui, para que:

  - a resposta cite o LIVRO certo (crucial a partir do 2º livro);
  - dê para ESCOPAR por livro ("só do básico", "segundo Heróis de Arton");
  - o nome/versão de um livro seja corrigido em UM lugar só.

Contrato para novas famílias/livros: todo extrair_/integrar_ carimba
`fonte=<id deste registro>` e `pagina` em cada chunk. Ids em kebab-case.

Este módulo é código (sem texto de livro) → versionado normalmente.
"""

# id -> metadados de exibição. `titulo` é o que aparece na citação.
FONTES = {
    "nucleo": {
        "titulo": "Tormenta20 (Edição Jogo do Ano)",
        "abrev": "T20",
        "versao": "Jogo do Ano",
        "ano": 2024,
    },
    "ameacas-arton": {
        "titulo": "Ameaças de Arton",
        "abrev": "AmA",
        "versao": "1.0",
        "data": "2023-11-17",
    },
    "herois-arton": {
        "titulo": "Heróis de Arton",
        "abrev": "HdA",
        "versao": "1.1",
    },
    "atlas-arton": {
        "titulo": "Atlas de Arton",
        "abrev": "AtA",
        "versao": "1.0",
        "data": "2023-11-17",
    },
    "deuses-arton": {
        "titulo": "Deuses de Arton",
        "abrev": "DdA",
        "versao": "Ebook",
    },
}

# Fonte assumida para chunks sem o campo (compatibilidade com o índice pré-procedência).
FONTE_PADRAO = "nucleo"


def existe(fonte_id):
    """True se `fonte_id` é uma fonte conhecida."""
    return fonte_id in FONTES


def titulo(fonte_id):
    """Título do livro para exibição/citação. Desconhecido → o próprio id (fail-safe)."""
    return FONTES.get(fonte_id or FONTE_PADRAO, {}).get("titulo", fonte_id or FONTE_PADRAO)


def abrev(fonte_id):
    """Sigla curta do livro (fallback: título)."""
    f = FONTES.get(fonte_id or FONTE_PADRAO)
    return f.get("abrev", titulo(fonte_id)) if f else (fonte_id or FONTE_PADRAO)


def rotulo_completo(fonte_id):
    """Ex.: 'Ameaças de Arton (v1.0)'. Usa versão quando houver."""
    f = FONTES.get(fonte_id or FONTE_PADRAO)
    if not f:
        return fonte_id or FONTE_PADRAO
    v = f.get("versao")
    return f"{f['titulo']} (v{v})" if v and not str(v)[0].isalpha() else f["titulo"]


if __name__ == "__main__":
    for fid, meta in FONTES.items():
        print(f"{fid:16s} -> {titulo(fid)}  [{abrev(fid)}]")
