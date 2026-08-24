"""Backfill de PROCEDÊNCIA: carimba `fonte` nos chunks que ainda não têm.

Antes da camada multi-livro, o índice foi construído só com o livro básico, então
todo chunk sem `fonte` é do núcleo. Este script marca `fonte="nucleo"` nesses
chunks — é METADADO PURO: não recalcula embeddings, não mexe no FAISS, não muda a
contagem. Idempotente (chunks que já têm `fonte` são preservados).

Uso:
    python migrar_fonte.py            # aplica
    python migrar_fonte.py --dry      # só relata, não grava

Depois disto, cada extrair_/integrar_ de um livro novo deve carimbar a sua própria
`fonte` (ver fontes.py). O núcleo fica marcado retroativamente aqui.
"""
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import fontes

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
FONTE_ALVO = "nucleo"


def main():
    dry = "--dry" in sys.argv

    meta_path = INDEX_DIR / "meta.json"
    chunks_path = INDEX_DIR / "chunks.jsonl"
    if not chunks_path.exists():
        raise SystemExit("index/chunks.jsonl não encontrado. Rode a ingestão/integradores antes.")

    chunks = [json.loads(l) for l in chunks_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    antes = Counter(c.get("fonte", "<sem fonte>") for c in chunks)
    sem_fonte = [c for c in chunks if not c.get("fonte")]
    print(f"[1/3] {len(chunks)} chunks | distribuição de fonte ANTES: {dict(antes)}")
    print(f"      {len(sem_fonte)} chunks sem `fonte` -> serao marcados como {FONTE_ALVO!r}")

    if not fontes.existe(FONTE_ALVO):
        raise SystemExit(f"Fonte {FONTE_ALVO!r} não está em fontes.py")

    if dry:
        print("[dry] nada gravado.")
        return
    if not sem_fonte:
        print("[2/3] nada a fazer (todos os chunks já têm `fonte`). Idempotente.")
        return

    # backup (só os arquivos que existem; o .faiss não muda mas vai junto por segurança)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bkp = INDEX_DIR / f"backup-{stamp}"
    bkp.mkdir(exist_ok=True)
    for nome in ("tormenta.faiss", "chunks.jsonl", "meta.json"):
        if (INDEX_DIR / nome).exists():
            shutil.copy2(INDEX_DIR / nome, bkp / nome)
    print(f"[2/3] backup em {bkp.name}\\")

    for c in sem_fonte:
        c["fonte"] = FONTE_ALVO

    with open(chunks_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # registra o mapa de fontes no meta (para inspeção/consulta)
    depois = Counter(c.get("fonte") for c in chunks)
    meta["fontes"] = dict(depois)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[3/3] OK — distribuição de fonte DEPOIS: {dict(depois)}")
    print(f"      n_chunks inalterado: {meta.get('n_chunks')} (metadado puro, sem re-embed)")


if __name__ == "__main__":
    main()
