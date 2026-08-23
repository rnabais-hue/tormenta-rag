# -*- coding: utf-8 -*-
r"""Integração ESTRUTURADA do Capítulo 5: Jogando (págs 218–245) e Parceiros (págs 266–268) ao índice FAISS.

Substitui os 93 chunks antigos de texto corrido do Capítulo 5 por ~47 chunks estruturados:
  - 7 manobras individuais + 1 lista consolidada de manobras.
  - 4 tipos de ação + 1 visão geral da rodada de combate.
  - 4 situações táticas + 1 consolidado da Tabela 5-3 (Situações Especiais) + 1 Tabela 5-4 (Objetos).
  - 3 chunks de ferimentos, sangramento, morte e tabela de descanso.
  - 2 chunks de dano (físico, elemental/mágico) e acertos críticos.
  - 7 habilidades universais + 1 acúmulo de bônus e tipos de efeito.
  - 3 regras de testes (CDs, escolher 10/20, testes estendidos).
  - 10 parceiros individuais (com tiers Iniciante/Veterano/Mestre) + 2 regras gerais de parceiros e montarias.

Reconstrói em memória os vetores das outras famílias (zero re-embutimento do restante).
"""
import io
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
DADOS_JSON = BASE / "dados" / "regras_jogo.json"
INDEX_DIR = BASE / "index"
FAISS_PATH = INDEX_DIR / "tormenta.faiss"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
META_PATH = INDEX_DIR / "meta.json"

MODELO_EMBED = "BAAI/bge-m3"
os.environ.setdefault("HF_HOME", r"C:\LLM-Local\models")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def gerar_chunks_estruturados():
    banco = json.loads(DADOS_JSON.read_text(encoding="utf-8"))
    novos = []

    # 1. Manobras Individuais
    for m in banco["manobras"]:
        texto = (
            f"MANOBRA DE COMBATE: {m['nome'].upper()}\n"
            f"• Ação: {m['tipo_acao']}\n"
            f"• Teste: {m['teste']}\n"
            f"• Alcance: {m['alcance']}\n"
            f"• Efeito: {m['efeito']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 5: Jogando, pág. {m['pagina']})"
        )
        novos.append({
            "id": f"regra_manobra_{m['id']}",
            "tipo": "regra_jogo",
            "categoria_regra": "manobra",
            "nome_regra": m["nome"],
            "titulo": f"Manobra de Combate: {m['nome']}",
            "secao": f"Capítulo 5: Jogando > Combate > Manobras > {m['nome']}",
            "pagina": m["pagina"],
            "texto": texto,
        })

    # 2. Lista Consolidada de Manobras de Combate
    lista_manobras_txt = (
        "LISTA CONSOLIDADA: TODAS AS MANOBRAS DE COMBATE (TORMENTA20)\n"
        "Manobras são ataques corpo a corpo especiais para desferir efeitos táticos no oponente:\n\n"
    )
    for m in banco["manobras"]:
        lista_manobras_txt += (
            f"• {m['nome'].upper()} (Ação: {m['tipo_acao']} | Teste: {m['teste']}): {m['efeito']}\n\n"
        )
    lista_manobras_txt += "Regra Geral: Bônus ou penalidades de tamanho e armas se aplicam aos testes opostos de Luta."
    novos.append({
        "id": "regra_lista_manobras_todas",
        "tipo": "regra_jogo_lista",
        "categoria_regra": "manobras_todas",
        "titulo": "Lista de Todas as Manobras de Combate",
        "secao": "Capítulo 5: Jogando > Combate > Manobras",
        "pagina": 240,
        "texto": lista_manobras_txt.strip(),
    })

    # 3. Tipos de Ação de Combate
    for a in banco["acoes"]:
        ex_txt = "\n".join([f"  - {e['nome']}: {e['descricao']}" for e in a["exemplos"]])
        texto = (
            f"AÇÕES DE COMBATE: {a['categoria'].upper()}\n"
            f"• Resumo: {a['resumo']}\n"
            f"• Principais Ações:\n{ex_txt}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 5: Jogando, pág. {a['pagina']})"
        )
        novos.append({
            "id": f"regra_acao_{a['id']}",
            "tipo": "regra_jogo",
            "categoria_regra": "acao",
            "nome_regra": a["categoria"],
            "titulo": f"Ações de Combate: {a['categoria']}",
            "secao": f"Capítulo 5: Jogando > Combate > Ações > {a['categoria']}",
            "pagina": a["pagina"],
            "texto": texto,
        })

    # 4. Visão Geral da Rodada de Combate
    novos.append({
        "id": "regra_combate_rodada_geral",
        "tipo": "regra_jogo",
        "categoria_regra": "combate_geral",
        "titulo": "A Rodada de Combate e Economia de Ações",
        "secao": "Capítulo 5: Jogando > Combate > A Rodada de Combate",
        "pagina": 239,
        "texto": (
            "A RODADA DE COMBATE E ECONOMIA DE AÇÕES EM TORMENTA20\n"
            "• Duração da Rodada: Uma rodada representa cerca de 6 segundos no mundo do jogo.\n"
            "• Iniciativa: No início do combate, cada participante rola um teste de Iniciativa (1d20 + Destreza + bônus). Os personagens agem em ordem decrescente de resultado.\n"
            "• Capacidade de Ação por Turno: Em seu turno, cada personagem tem direito a:\n"
            "  - 1 Ação Padrão (atacar, lançar magia, manobra, usar habilidade);\n"
            "  - 1 Ação de Movimento (deslocar-se até seu deslocamento, sacar/guardar item, levantar-se, mirar);\n"
            "  - Ou 1 Ação Completa (investida, golpe de misericórdia, corrida);\n"
            "  - Qualquer quantidade razoável de Ações Livres (falar, largar item);\n"
            "  - Reações fora do seu turno (testes de resistência, habilidades reativas).\n"
            "• Troca de Ações: Você pode trocar sua ação padrão por uma ação de movimento adicional (ficando com 2 ações de movimento no turno)."
        ),
    })

    # 5. Táticas e Situações Especiais
    for t in banco["modificadores_taticos"]:
        texto = (
            f"MODIFICADOR TÁTICO: {t['titulo'].upper()}\n"
            f"• Resumo: {t['resumo']}\n"
            f"• Regras e Mecânicas:\n{t['regras']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 5: Jogando, pág. {t['pagina']})"
        )
        novos.append({
            "id": f"regra_tatica_{t['id']}",
            "tipo": "regra_jogo",
            "categoria_regra": "tatica",
            "nome_regra": t["titulo"],
            "titulo": f"Modificador Tático: {t['titulo']}",
            "secao": f"Capítulo 5: Jogando > Combate > Situações Especiais > {t['titulo']}",
            "pagina": t["pagina"],
            "texto": texto,
        })

    # 6. Tabela 5-3: Situações Especiais Consolidada
    novos.append({
        "id": "regra_tabela_situacoes_especiais",
        "tipo": "regra_jogo",
        "categoria_regra": "tatica",
        "titulo": "Tabela 5-3: Modificadores de Situações Especiais de Combate",
        "secao": "Capítulo 5: Jogando > Combate > Situações Especiais",
        "pagina": 245,
        "texto": (
            "TABELA 5-3: MODIFICADORES DE SITUAÇÕES ESPECIAIS DE COMBATE (TORMENTA20)\n\n"
            "MODIFICADORES NO ATAQUE (QUANDO O ATACANTE ESTÁ...):\n"
            "• Caído: –5 no teste de ataque.\n"
            "• Cego: 50% de chance de falha em todos os ataques.\n"
            "• Em posição elevada: +2 no teste de ataque corpo a corpo.\n"
            "• Flanqueando o alvo: +2 no teste de ataque corpo a corpo.\n"
            "• Invisível: +5 no teste de ataque (não se aplica a alvos cegos).\n"
            "• Ofuscado: –2 no teste de ataque.\n\n"
            "MODIFICADORES NA DEFESA (QUANDO O ALVO ESTÁ...):\n"
            "• Caído: –5 na Defesa contra ataques corpo a corpo, +5 na Defesa contra ataques à distância.\n"
            "• Cego: –5 na Defesa.\n"
            "• Desprevenido: –5 na Defesa e em Reflexos.\n"
            "• Sob camuflagem leve: 20% de chance de falha contra ataques (1-2 no d10).\n"
            "• Sob camuflagem total: 50% de chance de falha contra ataques (1-5 no d10).\n"
            "• Sob cobertura leve: +5 na Defesa.\n"
            "• Sob cobertura total: O alvo não pode ser atacado."
        ),
    })

    # 7. Tabela 5-4: Quebrando Objetos e Estatísticas
    novos.append({
        "id": "regra_quebrando_objetos_tabela",
        "tipo": "regra_jogo",
        "categoria_regra": "tatica",
        "titulo": "Regras de Quebrar Objetos e Tabela 5-4: Estatísticas de Objetos",
        "secao": "Capítulo 5: Jogando > Combate > Quebrando Objetos",
        "pagina": 245,
        "texto": (
            "REGRAS DE QUEBRAR OBJETOS E TABELA 5-4 (TORMENTA20)\n"
            "• Atacar Objeto Solto: Teste de ataque contra a Defesa do objeto (baseada no tamanho). Se em movimento, recebe +5 na Defesa.\n"
            "• Atacar Objeto Empunhado: Veja manobra Quebrar (teste de ataque contra teste de Luta do portador).\n"
            "• Redução de Dano (RD) e Destruição: O dano causado é reduzido pela RD do material. Com 0 ou menos PV, o objeto é quebrado/destruído.\n\n"
            "TABELA DE OBJETOS COMUNS (TAMANHO, DEFESA, RD, PV):\n"
            "• Pergaminho: Minúsculo | Defesa 15 | RD 0 | 1 PV\n"
            "• Corda: Minúsculo | Defesa 15 | RD 0 | 2 PV\n"
            "• Corrente: Minúsculo | Defesa 15 | RD 10 | 2 PV\n"
            "• Cadeira: Pequeno | Defesa 12 | RD 5 | 5 PV\n"
            "• Barril: Médio | Defesa 10 | RD 5 | 10 PV\n"
            "• Porta de madeira: Grande | Defesa 8 | RD 5 | 20 PV\n"
            "• Porta de pedra: Grande | Defesa 8 | RD 8 | 100 PV\n"
            "• Porta de ferro: Grande | Defesa 8 | RD 10 | 100 PV\n"
            "• Carroça: Grande | Defesa 8 | RD 5 | 50 PV\n"
            "• Casebre: Enorme | Defesa 5 | RD 5 | 100 PV\n"
            "• Celeiro: Colossal | Defesa 0 | RD 5 | 200 PV\n\n"
            "ARMAS, ARMADURAS E ESCUDOS:\n"
            "• Arma leve de madeira: Defesa 5 | 2 PV\n"
            "• Arma de uma mão de madeira: Defesa 5 | 5 PV\n"
            "• Arma de duas mãos de madeira: Defesa 5 | 10 PV\n"
            "• Arma leve de metal: Defesa 10 | 2 PV\n"
            "• Arma de uma mão de metal: Defesa 10 | 5 PV\n"
            "• Arma de duas mãos de metal: Defesa 10 | 10 PV\n"
            "• Escudo leve: Defesa 5 | 10 PV | Escudo pesado: Defesa 10 | 20 PV\n"
            "• Armadura leve: Defesa 5 | 20 PV | Armadura pesada: Defesa 10 | 40 PV"
        ),
    })

    # 8. Ferimentos, Morte e Descanso
    for f in banco["ferimentos_descanso"]:
        if "tabela_descanso" in f:
            desc_linhas = "\n".join([
                f"• Condição {d['condicao'].upper()} ({d['exemplo']}): Recupera {d['recuperacao_pv']} e {d['recuperacao_pm']}. ({d['efeito_extra']})"
                for d in f["tabela_descanso"]
            ])
            texto = (
                f"{f['titulo'].upper()}\n"
                f"• Resumo: {f['resumo']}\n\n"
                f"TABELA DE CONDIÇÕES DE DESCANSO (8 HORAS DE REPOUSO):\n"
                f"{desc_linhas}\n\n"
                f"(Fonte: Tormenta20 Jogo do Ano, Cap. 5: Jogando, pág. {f['pagina']})"
            )
        else:
            texto = (
                f"{f['titulo'].upper()}\n"
                f"• Resumo: {f['resumo']}\n\n"
                f"{f['regras']}\n\n"
                f"(Fonte: Tormenta20 Jogo do Ano, Cap. 5: Jogando, pág. {f['pagina']})"
            )
        novos.append({
            "id": f"regra_ferimento_{f['id']}",
            "tipo": "regra_jogo",
            "categoria_regra": "descanso" if "descanso" in f["id"] else "ferimento",
            "nome_regra": f["titulo"],
            "titulo": f["titulo"],
            "secao": f"Capítulo 5: Jogando > Ferimentos & Morte > {f['titulo']}",
            "pagina": f["pagina"],
            "texto": texto,
        })

    # 9. Tipos de Dano e Críticos
    for d in banco["tipos_dano"]:
        t_lista = ", ".join(d["tipos"])
        novos.append({
            "id": f"regra_dano_{d['id']}",
            "tipo": "regra_jogo",
            "categoria_regra": "dano",
            "nome_regra": d["categoria"],
            "titulo": f"Tipos de Dano: {d['categoria']}",
            "secao": f"Capítulo 5: Jogando > Combate > Dano > {d['categoria']}",
            "pagina": d["pagina"],
            "texto": (
                f"TIPOS DE DANO: {d['categoria'].upper()}\n"
                f"• Descrição: {d['descricao']}\n"
                f"• Tipos Específicos: {t_lista}\n"
                f"(Fonte: Tormenta20 Jogo do Ano, Cap. 5: Jogando, pág. {d['pagina']})"
            ),
        })

    novos.append({
        "id": "regra_acerto_critico",
        "tipo": "regra_jogo",
        "categoria_regra": "dano",
        "titulo": "Regras de Acertos Críticos e Margem de Ameaça",
        "secao": "Capítulo 5: Jogando > Combate > Acertos Críticos",
        "pagina": 237,
        "texto": (
            "ACERTOS CRÍTICOS EM TORMENTA20\n"
            "• Margem de Ameaça: Cada arma ou ataque tem uma margem de ameaça (padrão 20, ou 19-20, etc.). Se a rolagem natural do d20 for igual ou superior à margem de ameaça E o total acertar a Defesa do alvo, o ataque é um Acerto Crítico.\n"
            "• Multiplicador de Crítico: O dano dos dados do ataque é multiplicado pelo valor do multiplicador (padrão x2, ou x3, x4). Bônus numéricos fixos (como Força) são multiplicados, enquanto dados extras de habilidades (como Ataque Furtivo ou dano de magia) NÃO são multiplicados.\n"
            "• 20 Natural: Um 20 natural no teste de ataque é sempre um acerto automático, independentemente da Defesa do alvo."
        ),
    })

    # 10. Habilidades Universais & Acúmulo de Efeitos
    for h in banco["habilidades_universais"]:
        novos.append({
            "id": f"regra_habilidade_universal_{h['nome'].lower().replace(' ', '_')}",
            "tipo": "regra_jogo",
            "categoria_regra": "habilidade_universal",
            "nome_regra": h["nome"],
            "titulo": f"Habilidade Universal: {h['nome']}",
            "secao": f"Capítulo 5: Jogando > Regras do Jogo > Habilidades Gerais > {h['nome']}",
            "pagina": h["pagina"],
            "texto": (
                f"HABILIDADE UNIVERSAL: {h['nome'].upper()}\n"
                f"• Descrição Mecânica: {h['descricao']}\n"
                f"(Fonte: Tormenta20 Jogo do Ano, Cap. 5: Jogando, pág. {h['pagina']})"
            ),
        })

    novos.append({
        "id": "regra_acumulo_efeitos_bonus",
        "tipo": "regra_jogo",
        "categoria_regra": "habilidade_universal",
        "titulo": "Regras de Acúmulo de Bônus e Efeitos",
        "secao": "Capítulo 5: Jogando > Regras do Jogo > Acumulando Efeitos",
        "pagina": 232,
        "texto": (
            "REGRAS DE ACÚMULO DE EFEITOS E BÔNUS (TORMENTA20)\n"
            "• Mesma Fonte NÃO Acumula: Bônus de habilidades, magias ou itens com o mesmo nome ou da mesma fonte não se acumulam. Aplica-se apenas o bônus mais alto.\n"
            "• Fontes Diferentes Acumulam: Bônus de fontes distintas (exemplo: uma habilidade de classe + uma magia + um item superior) se acumulam normalmente.\n"
            "• Bônus de Atributos: Você não pode somar o mesmo modificador de atributo mais de uma vez na mesma estatística (como somar Carisma duas vezes na Defesa).\n"
            "• Penalidades Sempre Acumulam: Ao contrário de bônus, penalidades de diferentes fontes ou mesmo da mesma fonte sempre se acumulam, a menos que especificado em contrário."
        ),
    })

    # 11. Regras de Resolução de Testes
    novos.append({
        "id": "regra_testes_resolucao_cds",
        "tipo": "regra_jogo",
        "categoria_regra": "testes",
        "titulo": "Resolução de Testes e Classes de Dificuldade (CD)",
        "secao": "Capítulo 5: Jogando > Regras do Jogo > Fazendo Testes",
        "pagina": 226,
        "texto": (
            "RESOLUÇÃO DE TESTES E CLASSES DE DIFICULDADE (TORMENTA20)\n"
            "• Fórmula Básica: Teste = 1d20 + Modificador de Perícia ou Atributo vs Classe de Dificuldade (CD).\n"
            "• Sucesso: Resultado igual ou superior à CD significa que a ação foi bem-sucedida.\n"
            "• Tabela de Dificuldades Comuns:\n"
            "  - Fácil: CD 10\n"
            "  - Médio: CD 15\n"
            "  - Difícil: CD 20\n"
            "  - Desafiador / Formidável: CD 25\n"
            "  - Heroico / Quase Impossível: CD 30\n"
            "• Testes Opostos: Quando duas criaturas disputam diretamente, ambas rolam; quem obtiver o maior resultado vence (empates favorecem o personagem com maior bônus fixo)."
        ),
    })

    novos.append({
        "id": "regra_testes_automaticos_escolher_10_20",
        "tipo": "regra_jogo",
        "categoria_regra": "testes",
        "titulo": "Sucesso/Falha Automáticos, Ajudar e Escolher 10/20",
        "secao": "Capítulo 5: Jogando > Regras do Jogo > Regras Adicionais de Testes",
        "pagina": 227,
        "texto": (
            "REGRAS ADICIONAIS DE TESTES EM TORMENTA20\n"
            "• 1 Natural e 20 Natural em Perícias: Em testes de perícia gerais, 1 e 20 NÃO são falhas e sucessos automáticos (apenas em testes de ataque e testes de resistência de magias).\n"
            "• Ajudar em Teste: Um aliado adjacente gasta uma ação de movimento/padrão para ajudar e faz um teste contra CD 10. Se passar, fornece +2 no teste do personagem principal (máximo de +10 de bônus por múltiplos ajudantes).\n"
            "• Escolher 10: Em situações calmas, sem pressão ou combate, você pode escolher 10 (considerar o resultado do d20 como 10 automático).\n"
            "• Escolher 20: Quando não há qualquer penalidade por falha e você tem tempo de sobra (gasta 20 vezes o tempo normal), pode escolher 20 (considerar o d20 como 20)."
        ),
    })

    novos.append({
        "id": "regra_testes_estendidos",
        "tipo": "regra_jogo",
        "categoria_regra": "testes",
        "titulo": "Regras de Testes Estendidos e Desafios Complexos",
        "secao": "Capítulo 5: Jogando > Regras do Jogo > Testes Estendidos",
        "pagina": 228,
        "texto": (
            "TESTES ESTENDIDOS EM TORMENTA20\n"
            "• Estrutura: Usados para tarefas complexas e dramáticas (infiltração, perseguição, desarmar armadilha complexa, pesquisa épica). Exige acumular um número de sucessos (ex.: 3 a 6 sucessos) antes de atingir um número de falhas (geralmente 3 falhas).\n"
            "• CD e Perícias: O mestre define a CD de cada etapa e quais perícias podem ser utilizadas.\n"
            "• Testes Estendidos em Grupo: Cada membro do grupo realiza um teste por rodada; o grupo compartilha o total acumulado de sucessos e falhas.\n"
            "• Consequências: Atingir os sucessos conclui o desafio com êxito; atingir as falhas resulta em fracasso dramático ou complicação grave."
        ),
    })

    # 12. Parceiros / Aliados Individuais
    for p in banco["parceiros"]:
        texto = (
            f"PARCEIRO / ALIADO: {p['nome'].upper()}\n"
            f"• Papel: {p['descricao_papel']}\n"
            f"• Nível Iniciante: {p['iniciante']}\n"
            f"• Nível Veterano: {p['veterano']}\n"
            f"• Nível Mestre: {p['mestre']}\n"
            f"(Fonte: Tormenta20 Jogo do Ano, Cap. 6: O Mestre, pág. {p['pagina']})"
        )
        novos.append({
            "id": f"regra_parceiro_{p['id']}",
            "tipo": "parceiro",
            "nome_parceiro": p["nome"],
            "titulo": f"Parceiro: {p['nome']}",
            "secao": f"Capítulo 6: O Mestre > Parceiros > {p['nome']}",
            "pagina": p["pagina"],
            "texto": texto,
        })

    # 13. Regras Gerais de Parceiros e Montarias
    novos.append({
        "id": "regra_parceiros_geral",
        "tipo": "parceiro_regra",
        "titulo": "Regras Gerais do Sistema de Parceiros e Limites por Patamar",
        "secao": "Capítulo 6: O Mestre > Parceiros > Regras de Parceiros",
        "pagina": 266,
        "texto": (
            "SISTEMA DE PARCEIROS (ALIADOS) EM TORMENTA20\n"
            "• Conceito: Parceiros são NPCs ou criaturas que acompanham o grupo e fornecem benefícios passivos mecânicos a um personagem específico sem sobrecarregar a mesa com fichas completas.\n"
            "• Limite de Parceiros por Patamar:\n"
            "  - Iniciante (1º ao 4º nível): Até 1 parceiro;\n"
            "  - Veterano (5º ao 10º nível) e Campeão (11º ao 16º nível): Até 2 parceiros;\n"
            "  - Lendário (17º ao 20º nível): Até 3 parceiros.\n"
            "• Mudança de Alvo: Você pode transferir um parceiro para um aliado adjacente gastando uma ação de movimento.\n"
            "• Imunidade a Dano: Em regras padrão, parceiros não sofrem dano nem são alvos diretos de ataques inimigos (a menos em situações narrativas extremas)."
        ),
    })

    novos.append({
        "id": "regra_parceiros_montarias",
        "tipo": "parceiro_regra",
        "titulo": "Parceiros do Tipo Montaria",
        "secao": "Capítulo 6: O Mestre > Parceiros > Montarias",
        "pagina": 267,
        "texto": (
            "PARCEIROS DO TIPO MONTARIA EM TORMENTA20\n"
            "• Regras Básicas: Montarias são parceiros que fornecem bônus especiais de movimentação e combate. Para usar uma montaria, ela deve ser pelo menos uma categoria de tamanho maior que você.\n"
            "• Ação de Montar: Montar ou desmontar gasta uma ação de movimento (ou ação livre com teste de Cavalgar CD 20).\n"
            "• Exemplos Comuns:\n"
            "  - Cavalo: Aumenta deslocamento e fornece ação de movimento extra para deslocar;\n"
            "  - Grifo: Fornece deslocamento de voo e dano em investidas;\n"
            "  - Lobo de Caverna: Aumenta deslocamento e bônus de dano corpo a corpo;\n"
            "  - Trog de Montaria: Fornece bônus em testes de resistência e deslocamento em terrenos difíceis."
        ),
    })

    return novos


def integrar():
    t0 = time.perf_counter()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = INDEX_DIR / f"backup-{ts}"
    shutil.copytree(INDEX_DIR, backup_dir, ignore=shutil.ignore_patterns("backup-*"))
    print(f"[1/5] Backup do índice em {backup_dir.name}\\")

    # Lê índice e chunks atuais
    index = faiss.read_index(str(FAISS_PATH))
    chunks_atuais = [
        json.loads(line)
        for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    meta = json.loads(META_PATH.read_text(encoding="utf-8")) if META_PATH.exists() else {}
    print(f"[2/5] Índice atual: {len(chunks_atuais)} chunks, dim {index.d}")

    # Remove chunks antigos do Cap. 5: Jogando (págs 218 a 245)
    manter_indices = []
    chunks_mantidos = []
    antigos_cap5 = 0
    for i, c in enumerate(chunks_atuais):
        sec = c.get("secao", "")
        p = c.get("pagina", 0)
        tp = c.get("tipo", "")
        # Chunks antigos do Cap. 5
        eh_cap5_antigo = (
            (218 <= p <= 245 or "Capítulo 5" in sec)
            and tp in ["", None, "texto_corrido", "regra_jogo", "regra_jogo_lista", "parceiro", "parceiro_regra"]
        )
        if eh_cap5_antigo:
            antigos_cap5 += 1
        else:
            manter_indices.append(i)
            chunks_mantidos.append(c)

    print(f"      Removendo {antigos_cap5} chunks antigos do Capítulo 5: Jogando")

    novos_chunks = gerar_chunks_estruturados()
    print(f"[3/5] {len(novos_chunks)} chunks estruturados de Regras de Jogo e Parceiros gerados.")
    print("      Reconstruindo vetores das outras famílias...")

    # Reconstrói vetores mantidos
    vecs_mantidos = np.empty((len(manter_indices), index.d), dtype="float32")
    for new_idx, old_idx in enumerate(manter_indices):
        vecs_mantidos[new_idx] = index.reconstruct(int(old_idx))

    # Embuti apenas os novos chunks
    print(f"[4/5] Carregando embedder {MODELO_EMBED} e embutindo {len(novos_chunks)} novos chunks...")
    model = SentenceTransformer(MODELO_EMBED)
    novos_textos = [c["texto"] for c in novos_chunks]
    novos_vecs = model.encode(
        novos_textos,
        batch_size=8,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).astype("float32")

    # Combina
    todos_vecs = np.vstack([vecs_mantidos, novos_vecs])
    todos_chunks = chunks_mantidos + novos_chunks

    # Reconstrói índice FAISS
    novo_index = faiss.IndexFlatIP(index.d)
    novo_index.add(todos_vecs)
    faiss.write_index(novo_index, str(FAISS_PATH))

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in todos_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    meta["n_chunks"] = len(todos_chunks)
    meta["regras_jogo_estruturadas"] = len(novos_chunks)
    meta["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = time.perf_counter() - t0
    print(
        f"[5/5] SUCESSO — Índice: {len(chunks_atuais)} -> {len(todos_chunks)} chunks "
        f"(-{antigos_cap5} antigos, +{len(novos_chunks)} novos estruturados)."
    )
    print(f"      Tempo total: {dt:.1f}s. Backup em {backup_dir.name}\\")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    integrar()


if __name__ == "__main__":
    main()
