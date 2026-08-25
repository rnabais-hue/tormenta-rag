# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA das DISTINÇÕES (Cap. 2) de *Heróis de Arton*.

`fonte="herois-arton"`, `capitulo="distincoes"`, versão 1.1, págs 104–215.
36 Distinções (entidade NOVA). Cada uma: conceito → Admissão (requisito) →
Marca da Distinção (1 poder) → Poderes da distinção (N poderes, cada um com
uma tag de tipo). Layout guiado por TIPOGRAFIA:

  - nome da distinção: splash Tormenta20 sz~58 (usamos o TOC como lista autoritativa)
  - seções: Tormenta20 sz18–24  ("Admissão", "Marca da Distinção", "Poderes da distinção"
    + subseções especiais 1-off tipo "Ornitópteros Goblins"/"Implantes")
  - poderes: Tormenta20 sz14–17
  - tag do poder (tipo): Tormenta20 sz10–12 à direita do nome (ex.: "Tormenta")
  - corpo/efeito: IowanOldStyle (Roman/Bold/Italic) 9–10pt
  - caixas "X em Jogo": SourceSansPro → descartadas

Ordena spans por (página, coluna, y) para respeitar as 2 colunas e roda uma
máquina de estados. Saída: dados/distincoes_herois.json. NÃO toca no índice.
"""
import sys, io, json, re
from pathlib import Path
import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = Path(__file__).parent / "livro" / "T20-Herois-de-Arton-v1.1.pdf"
OUT = Path(__file__).parent / "dados" / "distincoes_herois.json"
OUT.parent.mkdir(exist_ok=True)
FONTE = "herois-arton"
VERSAO = "1.1"

SECOES = {"Admissão", "Marca da Distinção", "Poderes da distinção"}
COL_X = 290  # divisória das 2 colunas


def dehyph(s):
    if not s:
        return ""
    s = re.sub(r"[\xad­]\s*", "", s)
    s = re.sub(r"(?<=[a-zà-ÿ])-\s+(?=[a-zà-ÿ])", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def slug(s):
    s = s.lower()
    for a, b in [("á","a"),("â","a"),("ã","a"),("à","a"),("é","e"),("ê","e"),
                 ("í","i"),("ó","o"),("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def nomes_toc(doc):
    """36 nomes de distinção, em ordem (o TOC dá nomes limpos; ignoramos as páginas
    do TOC, que apontam para a página mecânica, não o início visual)."""
    nomes = []
    for lvl, title, page in doc.get_toc():
        if lvl == 2 and 108 <= page <= 213 and title not in (
                "Distinções em Jogo", "Usando Distinções"):
            nomes.append((title.strip(), page))
    nomes.sort(key=lambda x: x[1])
    return [n for n, _ in nomes]


def paginas_splash(doc):
    """Índices PDF das páginas de splash (início visual de cada distinção): uma
    página com span Tormenta20 sz>=50 (nome gigante ou drop-cap). São 36, a cada 3."""
    out = []
    for idx in range(106, 215):
        page = doc[idx]
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    if s["font"].startswith("Tormenta20") and s["size"] >= 50:
                        out.append(idx)
                        break
                else:
                    continue
                break
            else:
                continue
            break
    return out


def _classificar(s):
    """Retorna (role, texto, x, y). role in {sec,power,tag,body,drop,name,box,skip}."""
    t = s["text"]
    fn = s["font"]
    sz = s["size"]
    x = s["bbox"][0]
    y = s["bbox"][1]
    st = t.strip()
    if not st:
        return None
    if fn.startswith("SourceSansPro"):
        return ("box", t, x, y)
    if fn.startswith("Tormenta20"):
        if sz >= 30:
            return ("drop" if len(st) <= 2 else "name", st, x, y)
        if 18 <= sz <= 26:
            return ("sec", st, x, y)
        if 13.5 <= sz < 18:
            return ("power", st, x, y)
        if 9.5 <= sz < 13.5:
            # tag de poder ou número de página (rodapé y>735)
            if y > 735:
                return None
            return ("tag", st, x, y)
        return None
    if "IowanOldStyle" in fn:
        if "BoldItalic" in fn:
            return None            # epígrafes/pull-quotes flavor → descartar
        return ("body", t, x, y)
    return None


def _classificar_linha(spans):
    """Classifica uma LINHA (lista de spans em ordem de leitura) → (role, payload).

    Preserva a ordem intra-linha (evita deslocar refs inline itálicas). role in
    {sec, power, body, skip}; payload = texto (sec/body) ou (nome, tag) (power)."""
    # ignora linha de caixa lateral (SourceSansPro dominante)
    if spans and all(s["font"].startswith("SourceSansPro") for s in spans):
        return ("skip", None)
    # cabeçalho de seção: algum span Tormenta20 sz18-26
    for s in spans:
        if s["font"].startswith("Tormenta20") and 18 <= s["size"] <= 26:
            return ("sec", s["text"].strip())
    # cabeçalho de poder: algum span Tormenta20 sz13.5-18
    nome_pod = None
    tag = None
    for s in spans:
        if s["font"].startswith("Tormenta20"):
            if 13.5 <= s["size"] < 18:
                nome_pod = (nome_pod + " " + s["text"].strip()).strip() if nome_pod else s["text"].strip()
            elif 9.5 <= s["size"] < 13.5 and s["bbox"][1] <= 735:
                tag = (tag + " " + s["text"].strip()).strip() if tag else s["text"].strip()
    if nome_pod:
        return ("power", (dehyph(nome_pod), dehyph(tag) if tag else None))
    # linha-tag isolada (categoria do poder, ex.: "Tormenta"): só Tormenta20 pequeno, fora do rodapé
    if all(s["font"].startswith("Tormenta20") and 9 <= s["size"] < 13.5
           and s["bbox"][1] <= 735 for s in spans):
        return ("tag", dehyph(" ".join(s["text"].strip() for s in spans)))
    # corpo: junta spans IowanOldStyle não-BoldItalic; drop-cap (Tormenta20 grande) vira prefixo
    partes = []
    for s in spans:
        fn = s["font"]; sz = s["size"]; t = s["text"]
        if fn.startswith("Tormenta20") and sz >= 30 and len(t.strip()) <= 2:
            partes.append(t.strip())              # drop-cap
        elif "IowanOldStyle" in fn and "BoldItalic" not in fn:
            partes.append(t)
    if partes:
        return ("body", "".join(partes) if False else " ".join(p for p in partes))
    return ("skip", None)


def extrair_distincao(doc, nome, idx_ini, idx_fim, pagina):
    # coleta LINHAS preservando ordem de spans; ordena por (página, coluna, y)
    linhas = []
    for pg in range(idx_ini, idx_fim + 1):
        if pg >= doc.page_count:
            break
        page = doc[pg]
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for l in b["lines"]:
                sp = [s for s in l["spans"] if s["text"].strip()]
                if not sp:
                    continue
                lx = min(s["bbox"][0] for s in sp)
                ly = min(s["bbox"][1] for s in sp)
                col = 0 if lx < COL_X else 1
                role, payload = _classificar_linha(sp)
                if role != "skip":
                    linhas.append((pg, col, ly, role, payload))
    linhas.sort(key=lambda z: (z[0], z[1], z[2]))

    conceito, admissao = [], []
    marca = {"nome": None, "efeito": []}
    poderes = []
    modo = "conceito"
    subsecao = None
    alvo = conceito
    cur_power = None
    ultima_role = None

    for pg, col, y, role, payload in linhas:
        if role == "sec":
            txt = payload
            if txt == "Admissão":
                modo, alvo = "admissao", admissao
            elif txt.startswith("Marca da") or txt == "Distinção":
                modo = "marca"; alvo = marca["efeito"]; cur_power = None
            elif txt.startswith("Poderes da"):
                modo = "poderes"; cur_power = None; subsecao = None
            else:
                modo = "poderes"; subsecao = dehyph(txt); cur_power = None
            ultima_role = "sec"
            continue
        if role == "power":
            pnome, ptag = payload
            # nome que quebra em 2+ linhas: continuação começa em minúscula (ex.: "e
            # infiltração", "para ornitópteros") logo após outra linha-de-poder, sem corpo.
            if ultima_role == "power" and pnome[:1].islower():
                if modo == "marca" and marca["nome"] and not marca["efeito"]:
                    marca["nome"] += " " + pnome
                    ultima_role = "power"; continue
                if cur_power is not None and not cur_power["efeito"]:
                    cur_power["nome"] += " " + pnome
                    if ptag and not cur_power["tag"]:
                        cur_power["tag"] = ptag
                    ultima_role = "power"; continue
            if modo == "marca" and marca["nome"] is None:
                marca["nome"] = pnome
                if ptag:
                    marca["tag"] = ptag
                alvo = marca["efeito"]
            else:
                cur_power = {"nome": pnome, "tag": ptag, "subsecao": subsecao, "efeito": []}
                poderes.append(cur_power)
                modo = "poderes"
                alvo = cur_power["efeito"]
            ultima_role = "power"
            continue
        if role == "tag":
            if cur_power and not cur_power["tag"]:
                cur_power["tag"] = payload
            elif modo == "marca" and marca["nome"] and not marca.get("tag"):
                marca["tag"] = payload
            ultima_role = "tag"
            continue
        if role == "body":
            alvo.append(payload)
            ultima_role = "body"

    def junta(lst):
        s = dehyph(" ".join(lst))
        # cola drop-cap: "P aladinos" -> "Paladinos"
        s = re.sub(r"\b([A-ZÀ-Ý]) ([a-zà-ÿ])", r"\1\2", s, count=1)
        return s

    return {
        "id": f"distincao:herois:{slug(nome)}",
        "tipo": "distincao", "nome": nome, "pagina": pagina,
        "fonte": FONTE, "versao": VERSAO,
        "conceito": junta(conceito),
        "admissao": junta(admissao),
        "marca": {"nome": marca["nome"], "efeito": junta(marca["efeito"])},
        "poderes": [{"nome": p["nome"], "tag": p["tag"], "subsecao": p["subsecao"],
                     "efeito": junta(p["efeito"])} for p in poderes],
    }


def main():
    print(f"Abrindo {PDF.name}...")
    doc = pymupdf.open(PDF)
    nomes = nomes_toc(doc)
    splashes = paginas_splash(doc)
    print(f"nomes TOC={len(nomes)}  splashes={len(splashes)}")
    assert len(nomes) == len(splashes) == 36, "contagem inesperada"

    dists = []
    for nome, idx_ini in zip(nomes, splashes):
        d = extrair_distincao(doc, nome, idx_ini, idx_ini + 2, pagina=idx_ini - 1)
        dists.append(d)
        npow = len(d["poderes"])
        marca_ok = "M" if d["marca"]["nome"] else "-"
        print(f"  {nome:32.32} p{d['pagina']:>3}  marca={marca_ok} poderes={npow:>2} "
              f"conceito={len(d['conceito']):>4}c admissao={len(d['admissao']):>4}c")

    total_pod = sum(len(d["poderes"]) for d in dists)
    dados = {"fonte": FONTE, "livro": "Heróis de Arton", "versao": VERSAO,
             "capitulo": "Capítulo 2: Distinções", "total": len(dists),
             "total_poderes": total_pod, "distincoes": dists}
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] {len(dists)} distinções, {total_pod} poderes -> {OUT}")


if __name__ == "__main__":
    main()
