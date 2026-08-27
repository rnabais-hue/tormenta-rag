# -*- coding: utf-8 -*-
r"""Integra o recorte SEGURO do Cap. 4 (Regras Opcionais) de *Heróis de Arton* ao FAISS.

Escopo desta rodada = as LISTAS entity-like do capítulo (as partes limpas e de alto
valor p/ o jogador), extraídas em 4 JSONs:
  • Papéis no Grupo (9)                 dados/papeis_grupo_herois.json
  • Complicações (54: 32 gerais + 22 de classe)   dados/complicacoes_herois.json
  • Objetivos Heroicos (7)              dados/objetivos_herois.json
  • Idades Variadas (7 faixas + 19 mazelas)        dados/idades_herois.json

Ficam de FORA (BACKLOG, chunk `tipo="pendencia"`): os MÓDULOS PROCEDURAIS do capítulo
— Regras Mais Soltas (Atributos Variados/Raças Abertas/Devoções Abertas), Combate
Avançado (+tabelas de crítico/morte/falha), Culinária Avançada, Exploração de Masmorras
e o subsistema Domínios (regência/construções/unidades/eventos).

Aditivo, `fonte="herois-arton"`, `capitulo="regras-opcionais"`. IDEMPOTÊNCIA ESTREITA:
remove só chunks com capitulo=="regras-opcionais" (não toca no resto). Embute só os novos.

Uso: python integrar_regras_opcionais_herois.py
"""
import json, re, shutil, time
from collections import Counter
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import fontes

BASE = Path(__file__).parent
INDEX_DIR = BASE / "index"
FONTE_ID = "herois-arton"
LIVRO = fontes.titulo(FONTE_ID)
CAP = "regras-opcionais"
SEC = "Heróis de Arton > Capítulo 4: Regras Opcionais"
D = BASE / "dados"


def base_chunk(titulo, subsecao, pagina, texto, **extra):
    c = {"titulo": titulo, "secao": f"{SEC} > {subsecao}", "pagina": pagina,
         "fonte": FONTE_ID, "capitulo": CAP, "texto": texto}
    c.update(extra)
    return c


def _mods_txt(mods):
    return ", ".join(f"{k} {v:+d}" for k, v in mods.items()) if mods else "nenhum"


def chunks_de():
    out = []
    pap = json.loads((D / "papeis_grupo_herois.json").read_text(encoding="utf-8"))
    com = json.loads((D / "complicacoes_herois.json").read_text(encoding="utf-8"))
    obj = json.loads((D / "objetivos_herois.json").read_text(encoding="utf-8"))
    ida = json.loads((D / "idades_herois.json").read_text(encoding="utf-8"))
    cba = json.loads((D / "combate_avancado_herois.json").read_text(encoding="utf-8"))
    dom = json.loads((D / "dominios_herois.json").read_text(encoding="utf-8"))
    rms = json.loads((D / "regras_soltas_herois.json").read_text(encoding="utf-8"))

    # ---------- Papéis no Grupo ----------
    p0 = pap["pagina"]
    out.append(base_chunk("Papéis no Grupo (visão geral)", "Papéis no Grupo", p0,
                          f"Regra opcional de {LIVRO} (Cap. 4). Papéis no Grupo: {pap['introducao']}",
                          tipo="regra_opcional", subtipo="overview", regra="Papéis no Grupo"))
    for p in pap["papeis"]:
        texto = (f"Papel no grupo: {p['nome']} (regra opcional, {LIVRO}, pág. {p['pagina']}).\n"
                 f"{p['descricao']}\nBenefício: {p['beneficio']}")
        out.append(base_chunk(f"Papel no Grupo: {p['nome']}", f"Papéis no Grupo > {p['nome']}",
                              p["pagina"], texto, tipo="papel_grupo", nome=p["nome"],
                              beneficio=p["beneficio"]))
    out.append(base_chunk("Lista dos Papéis no Grupo", "Papéis no Grupo > Lista", p0,
                          f"Os {pap['total']} Papéis no Grupo de {LIVRO} (Cap. 4): "
                          f"{', '.join(p['nome'] for p in pap['papeis'])}.",
                          tipo="regra_opcional_lista", regra="Papéis no Grupo"))

    # ---------- Complicações ----------
    c0 = com["pagina"]
    out.append(base_chunk("Complicações (visão geral)", "Complicações", c0,
                          f"Regra opcional de {LIVRO} (Cap. 4). Complicações: {com['introducao']}",
                          tipo="regra_opcional", subtipo="overview", regra="Complicações"))
    for c in com["complicacoes"]:
        cls = f" — complicação de classe ({c['classe']})" if c.get("classe") else " — complicação geral"
        voto = " Esta é uma complicação de código/voto (†): se violá-la, perde todos os PM." if c.get("voto") else ""
        texto = (f"Complicação: {c['nome']}{cls} (regra opcional, {LIVRO}, pág. {c['pagina']}).\n"
                 f"{c['efeito']}{voto}")
        out.append(base_chunk(f"Complicação: {c['nome']}", f"Complicações > {c['nome']}",
                              c["pagina"], texto, tipo="complicacao", nome=c["nome"],
                              categoria=c["categoria"], classe=c.get("classe"), voto=c.get("voto", False)))
    for s in com.get("regras_extra", []):
        out.append(base_chunk(f"Complicações — {s['titulo']}", f"Complicações > {s['titulo']}",
                              s["pagina"], f"{s['titulo']} ({LIVRO}, Cap. 4, pág. {s['pagina']}).\n{s['texto']}",
                              tipo="regra_opcional", subtipo="caixa", regra="Complicações"))
    out.append(base_chunk("Lista das Complicações", "Complicações > Lista", c0,
                          f"As {com['total']} Complicações de {LIVRO} (Cap. 4): "
                          f"{com['n_gerais']} gerais e {com['n_classe']} de classe. "
                          f"Gerais: {', '.join(c['nome'] for c in com['complicacoes'] if c['categoria']=='geral')}. "
                          f"De classe: {', '.join(c['nome']+' ('+(c['classe'] or '?')+')' for c in com['complicacoes'] if c['categoria']=='classe')}.",
                          tipo="regra_opcional_lista", regra="Complicações"))

    # ---------- Objetivos Heroicos ----------
    o0 = obj["pagina"]
    out.append(base_chunk("Objetivos Heroicos (visão geral)", "Objetivos Heroicos", o0,
                          f"Regra opcional de {LIVRO} (Cap. 4). Objetivos Heroicos: {obj['introducao']}",
                          tipo="regra_opcional", subtipo="overview", regra="Objetivos Heroicos"))
    for o in obj["objetivos"]:
        texto = (f"Objetivo heroico: {o['nome']} (regra opcional, {LIVRO}, pág. {o['pagina']}).\n"
                 f"{o['descricao']}\nBenefício: {o['beneficio']}\nPenalidade: {o['penalidade']}\n"
                 f"Conclusão: {o['conclusao']}")
        out.append(base_chunk(f"Objetivo Heroico: {o['nome']}", f"Objetivos Heroicos > {o['nome']}",
                              o["pagina"], texto, tipo="objetivo_heroico", nome=o["nome"]))
    for s in obj.get("regras_extra", []):
        out.append(base_chunk(f"Objetivos — {s['titulo']}", f"Objetivos Heroicos > {s['titulo']}",
                              s["pagina"], f"{s['titulo']} ({LIVRO}, Cap. 4, pág. {s['pagina']}).\n{s['texto']}",
                              tipo="regra_opcional", subtipo="caixa", regra="Objetivos Heroicos"))
    out.append(base_chunk("Lista dos Objetivos Heroicos", "Objetivos Heroicos > Lista", o0,
                          f"Os {obj['total']} Objetivos Heroicos de {LIVRO} (Cap. 4): "
                          f"{', '.join(o['nome'] for o in obj['objetivos'])}.",
                          tipo="regra_opcional_lista", regra="Objetivos Heroicos"))

    # ---------- Idades Variadas ----------
    i0 = ida["pagina"]
    out.append(base_chunk("Idades Variadas (visão geral)", "Idades Variadas", i0,
                          f"Regra opcional de {LIVRO} (Cap. 4). Idades Variadas (inclui 'O Peso da "
                          f"Idade' e 'Envelhecendo'): {ida['introducao']}",
                          tipo="regra_opcional", subtipo="overview", regra="Idades Variadas"))
    for f in ida["faixas"]:
        tracos = " ".join(f"{t['nome']}: {t['efeito']}" for t in f["tracos"])
        texto = (f"Faixa etária: {f['nome']} ({f['idade']}) — regra opcional de idade, {LIVRO}, "
                 f"pág. {f['pagina']}.\nModificadores de atributo: {_mods_txt(f['modificadores'])}.\n"
                 f"{f['resumo']}\n{tracos}".strip())
        out.append(base_chunk(f"Faixa Etária: {f['nome']} ({f['idade']})",
                              f"Idades Variadas > Faixas > {f['nome']}", f["pagina"], texto,
                              tipo="faixa_etaria", nome=f["nome"], idade=f["idade"],
                              modificadores=f["modificadores"]))
    for m in ida["mazelas"]:
        texto = (f"Mazela da idade (O Peso da Idade): {m['nome']} — {LIVRO}, Cap. 4, pág. {m['pagina']}.\n"
                 f"{m['efeito']}")
        out.append(base_chunk(f"Mazela da Idade: {m['nome']}", f"Idades Variadas > O Peso da Idade > {m['nome']}",
                              m["pagina"], texto, tipo="mazela_idade", nome=m["nome"]))
    for s in ida.get("regras_extra", []):
        if s["titulo"] == "(tabela)":
            continue     # Tabela 4-2 é redundante com as faixas; não vira chunk
        out.append(base_chunk(f"Idades — {s['titulo']}", f"Idades Variadas > {s['titulo']}",
                              s["pagina"], f"{s['titulo']} ({LIVRO}, Cap. 4, pág. {s['pagina']}).\n{s['texto']}",
                              tipo="regra_opcional", subtipo="caixa", regra="Idades Variadas"))
    out.append(base_chunk("Faixas Etárias e Mazelas da Idade (lista)", "Idades Variadas > Lista", i0,
                          f"Faixas etárias de {LIVRO} (Cap. 4): "
                          f"{', '.join(f['nome']+' ('+f['idade']+')' for f in ida['faixas'])}. "
                          f"Mazelas de 'O Peso da Idade': {', '.join(m['nome'] for m in ida['mazelas'])}.",
                          tipo="regra_opcional_lista", regra="Idades Variadas"))

    # ---------- Combate Avançado ----------
    b0 = cba["pagina"]
    out.append(base_chunk("Combate Avançado (visão geral)", "Combate Avançado", b0,
                          f"Regra opcional de {LIVRO} (Cap. 4). Combate Avançado: {cba['introducao']}",
                          tipo="regra_opcional", subtipo="overview", regra="Combate Avançado"))
    for r in cba["regras"]:
        texto = (f"Regra opcional de combate: {r['nome']} ({LIVRO}, Cap. 4, pág. {r['pagina']}).\n"
                 f"{r['efeito']}")
        out.append(base_chunk(f"Combate Avançado: {r['nome']}", f"Combate Avançado > {r['nome']}",
                              r["pagina"], texto, tipo="regra_opcional", subtipo="combate_avancado",
                              regra="Combate Avançado", nome=r["nome"]))
    for tb in cba["tabelas"]:
        corpo = "\n".join(f"{ln['faixa']}: {ln['efeito']}" for ln in tb["linhas"])
        texto = f"Tabela de Combate Avançado: {tb['nome']} ({LIVRO}, Cap. 4, pág. {tb['pagina']}).\n{corpo}"
        out.append(base_chunk(f"Tabela: {tb['nome']}", f"Combate Avançado > Tabela {tb['nome']}",
                              tb["pagina"], texto, tipo="regra_opcional", subtipo="tabela",
                              regra="Combate Avançado", nome=tb["nome"]))
    out.append(base_chunk("Lista das Regras de Combate Avançado", "Combate Avançado > Lista", b0,
                          f"Regras opcionais de Combate Avançado de {LIVRO} (Cap. 4): "
                          f"{', '.join(r['nome'] for r in cba['regras'])}. "
                          f"Tabelas: {', '.join(tb['nome'] for tb in cba['tabelas'])}.",
                          tipo="regra_opcional_lista", regra="Combate Avançado"))

    # ---------- Domínios ----------
    dp = dom["pagina"]
    out.append(base_chunk("Domínios (visão geral)", "Domínios", dp,
                          f"Regra opcional de {LIVRO} (Cap. 4): subsistema de DOMÍNIOS (regência de um "
                          f"reino). Partes: {', '.join(m['nome'] for m in dom['modulos'])}. Inclui uma lista "
                          f"de {dom['total_construcoes']} Construções e a tabela de Unidades Militares.",
                          tipo="regra_opcional", subtipo="overview", regra="Domínios"))
    for m in dom["modulos"]:
        texto = (f"Domínios — {m['nome']} (regra opcional de regência, {LIVRO}, Cap. 4, pág. {m['pagina']}).\n"
                 f"{m['efeito']}")
        out.append(base_chunk(f"Domínios: {m['nome']}", f"Domínios > {m['nome']}", m["pagina"],
                              texto, tipo="regra_opcional", subtipo="dominios", regra="Domínios", nome=m["nome"]))
    for c in dom["construcoes"]:
        texto = (f"Construção de domínio: {c['nome']} ({LIVRO}, Cap. 4, pág. {c['pagina']}).\n{c['descricao']}")
        out.append(base_chunk(f"Construção: {c['nome']}", f"Domínios > Construções > {c['nome']}",
                              c["pagina"], texto, tipo="construcao_dominio", nome=c["nome"], regra="Domínios"))
    tu = dom.get("tabela_unidades")
    if tu:
        corpo = "\n".join(tu["linhas"])
        out.append(base_chunk("Domínios: Unidades Militares (Tabela 4-11)", "Domínios > Unidades Militares",
                              tu["pagina"], f"Unidades Militares de domínio ({LIVRO}, Cap. 4, pág. {tu['pagina']}). "
                              f"Colunas: {', '.join(tu['colunas'])}.\n{corpo}",
                              tipo="regra_opcional", subtipo="tabela", regra="Domínios", nome="Unidades Militares"))
    for tc in dom.get("tabelas_custo", []):
        corpo = "\n".join(tc["linhas"])
        out.append(base_chunk(f"Domínios: {tc['nome']}", f"Domínios > {tc['nome']}", tc["pagina"],
                              f"Tabela de domínio: {tc['nome']} ({LIVRO}, Cap. 4, pág. {tc['pagina']}). "
                              f"Colunas: {', '.join(tc['colunas'])}.\n{corpo}",
                              tipo="regra_opcional", subtipo="tabela", regra="Domínios", nome=tc["nome"]))
    out.append(base_chunk("Lista das Construções de Domínio", "Domínios > Construções > Lista", dp,
                          f"As {dom['total_construcoes']} Construções de domínio de {LIVRO} (Cap. 4): "
                          f"{', '.join(c['nome'] for c in dom['construcoes'])}.",
                          tipo="regra_opcional_lista", regra="Domínios"))

    # ---------- Módulos menores: Regras Mais Soltas, Culinária, Exploração ----------
    SEC_ROT = {"regras_soltas": "Regras Mais Soltas", "culinaria": "Culinária Avançada",
               "exploracao_masmorras": "Exploração de Masmorras"}
    for m in rms["modulos"]:
        rot = SEC_ROT.get(m["subtipo"], m.get("regra", "Regras Opcionais"))
        texto = f"{rot} — {m['nome']} (regra opcional, {LIVRO}, Cap. 4, pág. {m['pagina']}).\n{m['efeito']}"
        out.append(base_chunk(f"{rot}: {m['nome']}", f"{rot} > {m['nome']}", m["pagina"], texto,
                              tipo="regra_opcional", subtipo=m["subtipo"], regra=rot, nome=m["nome"]))
    for p in rms["pratos"]:
        texto = f"Prato especial (Culinária Avançada): {p['nome']} ({LIVRO}, Cap. 4, pág. {p['pagina']}).\n{p['descricao']}"
        out.append(base_chunk(f"Prato Especial: {p['nome']}", f"Culinária Avançada > Pratos > {p['nome']}",
                              p["pagina"], texto, tipo="prato_especial", nome=p["nome"], regra="Culinária Avançada"))
    for i in rms["ingredientes"]:
        texto = f"Ingrediente de culinária: {i['nome']} ({LIVRO}, Cap. 4, pág. {i['pagina']}).\n{i['descricao']}"
        out.append(base_chunk(f"Ingrediente: {i['nome']}", f"Culinária Avançada > Ingredientes > {i['nome']}",
                              i["pagina"], texto, tipo="ingrediente_culinaria", nome=i["nome"], regra="Culinária Avançada"))
    out.append(base_chunk("Lista de Pratos e Ingredientes (Culinária)", "Culinária Avançada > Lista", 307,
                          f"Pratos Especiais de {LIVRO} (Cap. 4): {', '.join(p['nome'] for p in rms['pratos'])}. "
                          f"Ingredientes: {', '.join(i['nome'] for i in rms['ingredientes'])}.",
                          tipo="regra_opcional_lista", regra="Culinária Avançada"))

    # ---------- Cap. 4 COMPLETO ----------
    ntc = len(dom.get("tabelas_custo", []))
    out.append(base_chunk("Cap. 4 (Regras Opcionais) — COMPLETO", "Backlog", 280,
        f"Cap. 4 (Regras Opcionais) de {LIVRO}: COMPLETO. Integrados as listas entity-like (Papéis, Complicações, "
        f"Objetivos, Idades), Combate Avançado (18 regras + 3 tabelas), o subsistema Domínios (23 módulos + "
        f"{dom['total_construcoes']} construções + unidades + {ntc} tabelas de custo: Terrenos 4-9, Construções "
        f"4-10, Eventos Aleatórios 4-13) e os módulos menores (Regras Mais Soltas, Culinária Avançada com "
        f"{rms['total_pratos']} pratos + {rms['total_ingredientes']} ingredientes, Exploração de Masmorras). "
        f"Nada pendente neste capítulo.",
        tipo="pendencia", nome="Cap. 4 Regras Opcionais COMPLETO"))

    resumo = dict(
        papeis=pap["total"], complicacoes=com["total"], objetivos=obj["total"],
        faixas=ida["total_faixas"], mazelas=ida["total_mazelas"],
        combate_regras=cba["total_regras"], combate_tabelas=cba["total_tabelas"],
        dominios_modulos=dom["total_modulos"], construcoes=dom["total_construcoes"],
        modulos_menores=rms["total_modulos"], pratos=rms["total_pratos"], ingredientes=rms["total_ingredientes"],
        overviews=sum(1 for c in out if c.get("subtipo") == "overview"),
        caixas=sum(1 for c in out if c.get("subtipo") == "caixa"),
        tabelas=sum(1 for c in out if c.get("subtipo") == "tabela"),
        listas=sum(1 for c in out if c["tipo"] == "regra_opcional_lista"),
        total_chunks=len(out))
    return out, resumo


def eh_regras_opc(c):
    return c.get("fonte") == FONTE_ID and c.get("capitulo") == CAP


def integrar():
    t0 = time.time()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = INDEX_DIR / f"backup-{ts}"

    print(f"[1/5] Backup em {backup_dir.name}")
    backup_dir.mkdir(exist_ok=True)
    for fn in ["chunks.jsonl", "meta.json", "tormenta.faiss"]:
        p = INDEX_DIR / fn
        if p.exists():
            shutil.copy2(p, backup_dir / fn)

    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    chunks_atuais = [json.loads(l) for l in (INDEX_DIR / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    idx_faiss = faiss.read_index(str(INDEX_DIR / "tormenta.faiss"))
    dim = idx_faiss.d
    n_antes = len(chunks_atuais)
    print(f"[2/5] Índice atual: {n_antes} chunks, dim {dim}")

    manter_idx, mantidos, rem = [], [], 0
    for i, c in enumerate(chunks_atuais):
        if eh_regras_opc(c):
            rem += 1
        else:
            manter_idx.append(i); mantidos.append(c)
    if rem:
        print(f"      Removendo {rem} chunks regras-opcionais anteriores (idempotência estreita)")

    novos, resumo = chunks_de()
    print(f"[3/5] {len(novos)} chunks gerados: {resumo}.")

    if manter_idx:
        vecs_m = np.empty((len(manter_idx), dim), dtype="float32")
        for pos, old in enumerate(manter_idx):
            vecs_m[pos] = idx_faiss.reconstruct(int(old))
    else:
        vecs_m = np.empty((0, dim), dtype="float32")

    print(f"[4/5] Embutindo {len(novos)} chunks novos (BAAI/bge-m3)...")
    te = time.time()
    model = SentenceTransformer("BAAI/bge-m3")
    vecs_n = model.encode([c["texto"] for c in novos], batch_size=8,
                          show_progress_bar=False, normalize_embeddings=True).astype("float32")
    print(f"      {len(novos)} vetores em {time.time()-te:.1f}s")

    todos_vecs = np.vstack([vecs_m, vecs_n]) if len(vecs_m) else vecs_n
    novo_index = faiss.IndexFlatIP(dim)
    novo_index.add(todos_vecs)

    todos_chunks = mantidos + novos
    for i, c in enumerate(todos_chunks):
        c["id"] = i
    (INDEX_DIR / "chunks.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in todos_chunks) + "\n", encoding="utf-8")
    faiss.write_index(novo_index, str(INDEX_DIR / "tormenta.faiss"))

    meta["n_chunks"] = len(todos_chunks)
    meta["fontes"] = dict(Counter(c.get("fonte", "nucleo") for c in todos_chunks))
    meta["herois_cap4_regras_opcionais_estruturado"] = resumo
    meta["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")
    (INDEX_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[5/5] SUCESSO — {n_antes} -> {len(todos_chunks)} chunks (+{len(novos)-rem} líquido). "
          f"fontes={meta['fontes']}. Tempo {time.time()-t0:.1f}s.")


if __name__ == "__main__":
    integrar()
