# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das NOVAS MAGIAS ARCANAS — *Heróis de Arton* (Cap. 3, págs 254–257).

Mesmo schema/stat-block do núcleo (`extrair_magias.py`): nome Tormenta20 ~16pt; subtítulo
"Arcana N (Escola)" Tormenta20 ~9pt; stat block com rótulos negrito IowanOldStyle
(Execução/Alcance/Alvo|Área|Efeito/Duração/Resistência) + valores Roman; descrição Roman;
aprimoramentos "+N PM:"/"Truque:". A ORDEM DE BLOCOS do PyMuPDF já é a de leitura (colunas
estreitas) → segmenta por cabeçalho, como no núcleo (verificado: 22 magias limpas).

Diferença: filtra o splash de seção "Novas magias Arcanas" (48pt) do nome. `fonte="herois-arton"`.
Saída: dados/magias_herois.json. NÃO toca no índice.
"""
import io, json, re, sys
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).parent
PDF = BASE / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = BASE / "dados" / "magias_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
PG_INI, PG_FIM = 254, 257
CUSTO_PM_CIRCULO = {1: 1, 2: 3, 3: 6, 4: 10, 5: 15}
HEADER_RE = re.compile(r"^(Arcana|Divina|Universal)\s+(\d+)\s*\(([^)]+)\)", re.I)
STAT_RE = re.compile(
    r"^Execu[çc][ãa]o\s*:\s*(.*?)[;.]\s*"
    r"Alcance\s*:\s*(.*?)[;.]\s*"
    r"(?:(Alvo ou [ÁA]rea|Alvos|Alvo|[ÁA]rea|Efeito)\s*:\s*(.*?)[;.]\s*)?"
    r"Dura[çc][ãa]o\s*:\s*(.*?)(?:[;.]\s*Resist[êe]ncia\s*:\s*(.*?))?\.\s+(.*)",
    re.I | re.DOTALL)


def slug(s):
    s = s.lower()
    for a, b in [("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def dehyph(s):
    s = re.sub(r"(\w)[-\xad]\s+(\w)", r"\1\2", s)
    s = re.sub(r"[\xad­]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_nome(s):
    """Versalete no nome vem em CAIXA-ALTA (ex.: 'Armadura ELEMENTAL') → normaliza a palavra."""
    return " ".join(w.capitalize() if (len(w) > 1 and w.isupper()) else w for w in s.split())


def coletar_spans(doc):
    spans = []
    for pno in range(PG_INI, PG_FIM + 1):
        for b in doc[pno - 1].get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    txt = s["text"].strip()
                    if txt:
                        spans.append({"text": txt, "font": s["font"], "size": round(s["size"], 1),
                                      "bold": bool(s["flags"] & 16) or "Bold" in s["font"], "page": pno})
    return spans


def limites(spans):
    bnd = []
    for i, s in enumerate(spans):
        m = HEADER_RE.match(s["text"])
        if m and "Tormenta20" in s["font"]:
            nm = []
            j = i - 1
            while j >= 0 and 14 <= spans[j]["size"] < 24 and "Tormenta20" in spans[j]["font"]:
                nm.insert(0, spans[j]["text"]); j -= 1
            bnd.append({"start": j + 1, "hdr": i, "nome": norm_nome(dehyph(" ".join(nm))),
                        "tipo": m.group(1).lower(), "circulo": int(m.group(2)),
                        "escola": m.group(3).strip().capitalize(), "page": s["page"]})
    return bnd


def parse_corpo(sb, sp):
    full = dehyph(" ".join(s["text"] for s in sp))
    rec = {"id": f"magia:herois:{slug(sb['nome'])}", "tipo": "magia", "nome": sb["nome"],
           "fonte": FONTE, "versao": "1.1", "arcana_divina": sb["tipo"], "circulo": sb["circulo"],
           "custo_pm": CUSTO_PM_CIRCULO.get(sb["circulo"], 1), "escola": sb["escola"],
           "execucao": "", "alcance": "", "alvo_tipo": "", "alvo": "", "duracao": "",
           "resistencia": "", "descricao": full, "aprimoramentos": [], "pagina": sb["page"]}
    m = STAT_RE.match(full)
    if not m:
        return rec
    corpo = m.group(7).strip()
    apr_splits = re.split(r"(?=(?:Truque|\+\s*\d+\s*PM(?:\s*\([^)]+\))?)\s*:)", corpo)
    apr_re = re.compile(r"^(Truque|\+\s*\d+\s*PM(?:\s*\([^)]+\))?)\s*:\s*(.*)", re.DOTALL | re.I)
    aprs = []
    for part in apr_splits[1:]:
        ma = apr_re.match(part.strip())
        if ma:
            aprs.append({"custo": ma.group(1).strip(), "efeito": re.sub(r"\s+", " ", ma.group(2)).strip()})
    rec.update({"execucao": m.group(1).strip(), "alcance": m.group(2).strip(),
                "alvo_tipo": (m.group(3) or "").strip(), "alvo": (m.group(4) or "").strip(),
                "duracao": m.group(5).strip(), "resistencia": (m.group(6) or "").strip(),
                "descricao": apr_splits[0].strip(), "aprimoramentos": aprs})
    return rec


def main():
    doc = pymupdf.open(str(PDF))
    spans = coletar_spans(doc)
    bnd = limites(spans)
    magias = []
    for i, sb in enumerate(bnd):
        end = bnd[i + 1]["start"] if i + 1 < len(bnd) else len(spans)
        magias.append(parse_corpo(sb, spans[sb["hdr"] + 1:end]))
    banco = {"fonte": FONTE, "livro": "Heróis de Arton", "secao": "Novas Magias Arcanas",
             "pagina": PG_INI, "total": len(magias), "magias": magias}
    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for m in magias if m["execucao"])
    print(f"{len(magias)} magias ({ok} com stat block parseado) -> {OUT.name}\n")
    for m in magias:
        print(f"  {m['nome']:<22} Arcana {m['circulo']} ({m['escola']:<13}) | "
              f"exec={m['execucao'][:14]:<14} alvo={(m['alvo'] or m['alvo_tipo'])[:16]:<16} | {len(m['aprimoramentos'])} aprim")


if __name__ == "__main__":
    main()
