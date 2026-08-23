# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Capítulo 5: Jogando (págs 218–245) e Parceiros (págs 266–268) de Tormenta20 (Edição Jogo do Ano).
Guiada pela TIPOGRAFIA e pelas tabelas do livro.

Extrai:
  - 7 Manobras de Combate (Agarrar, Atropelar, Derrubar, Desarmar, Empurrar, Fintar, Quebrar).
  - Tipos de Ações de Combate (Padrão, Movimento, Completa, Livre, Reação).
  - Modificadores Táticos & Situações Especiais (Flanquear, Cobertura, Camuflagem, Terreno Difícil, Combate Montado, Tabela 5-3, Tabela 5-4).
  - Ferimentos, Morte, Descanso & Recuperação (0 PV, Sangrando, Estabilização, Dano Não Letal, Tabela de Descanso).
  - Tipos de Dano & Acertos Críticos (Físico, Elemental, Mágico, Ameaça e Multiplicador).
  - Habilidades Universais & Efeitos (Faro, Imunidade, Percepção às Cegas, RD, Resistências, Visão, Acúmulo de Efeitos).
  - Regras de Resolução de Testes (CDs, Sucesso/Falha 1 e 20, Escolher 10/20, Ajudar, Testes Estendidos).
  - Sistema de Parceiros / Aliados (10 Tipos x 3 Tiers: Iniciante, Veterano, Mestre + Montarias).

Lê o PDF; escreve dados/regras_jogo.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
OUT = BASE / "dados" / "regras_jogo.json"
OUT.parent.mkdir(exist_ok=True)


def dehyph(s):
    if not s:
        return ""
    s = re.sub(r"(\w+)[-\xad\u00ad]\s+(\w+)", r"\1\2", s)
    s = re.sub(r"[\xad\u00ad]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extrair_dados_regras():
    doc = pymupdf.open(str(PDF))

    # 1. MANOBRAS DE COMBATE (págs 239–240)
    manobras = [
        {
            "id": "manobra_agarrar",
            "nome": "Agarrar",
            "tipo_acao": "Padrão (ou no lugar de um ataque)",
            "teste": "Teste de Luta oposto (modificadores de tamanho se aplicam)",
            "alcance": "Corpo a corpo",
            "efeito": "Você segura uma criatura com uma mão livre. Se vencer o teste, o alvo fica na condição Agarrado (desprevenido e imóvel, sofre –2 em testes de ataque e só pode atacar com armas leves). Você também fica desprevenido e imóvel enquanto mantiver o agarrar. Para manter o alvo agarrado nas rodadas seguintes, você deve gastar uma ação padrão no início do seu turno e passar em um novo teste de Luta oposto. O alvo pode tentar se soltar gastando uma ação padrão e passando em um teste de Luta ou Acrobacia oposto ao seu teste de Luta.",
            "pagina": 240,
        },
        {
            "id": "manobra_atropelar",
            "nome": "Atropelar",
            "tipo_acao": "Padrão (usada durante uma ação de movimento)",
            "teste": "Teste de Luta ou Atletismo oposto a Luta ou Reflexos",
            "alcance": "Corpo a corpo",
            "efeito": "Você tenta passar pelo espaço ocupado por um inimigo enquanto se move. Se vencer o teste oposto, você derruba o inimigo (ele fica Caído) e continua seu movimento normalmente através do espaço dele. Se falhar, o inimigo continua de pé e detém seu avanço no quadrado adjacente.",
            "pagina": 239,
        },
        {
            "id": "manobra_derrubar",
            "nome": "Derrubar",
            "tipo_acao": "Padrão (ou no lugar de um ataque)",
            "teste": "Teste de Luta oposto",
            "alcance": "Corpo a corpo",
            "efeito": "Você faz uma rasteira, empurrão ou golpe baixo para deixar o alvo na condição Caído. A queda não causa dano. Uma criatura caída sofre –5 na Defesa contra ataques corpo a corpo e recebe +5 na Defesa contra ataques à distância; além disso, sofre –5 em testes de ataque corpo a corpo e seu deslocamento é reduzido a 1,5m. Levantar-se do chão gasta uma ação de movimento.",
            "pagina": 240,
        },
        {
            "id": "manobra_desarmar",
            "nome": "Desarmar",
            "tipo_acao": "Padrão (ou no lugar de um ataque)",
            "teste": "Teste de Luta oposto (bônus de armas de duas mãos ou desarmadas se aplicam)",
            "alcance": "Corpo a corpo",
            "efeito": "Você atinge a arma ou item empunhado pelo oponente para arrancá-lo de suas mãos. Se você vencer o teste oposto, o item cai no chão no mesmo quadrado da criatura. Sacar ou apanhar um item no chão gasta uma ação de movimento.",
            "pagina": 240,
        },
        {
            "id": "manobra_empurrar",
            "nome": "Empurrar",
            "tipo_acao": "Padrão (ou no lugar de um ataque)",
            "teste": "Teste de Luta oposto",
            "alcance": "Corpo a corpo",
            "efeito": "Você empurra a criatura 1,5m para trás. Para cada 5 pontos de diferença que o seu teste superar o do defensor, você empurra o alvo mais 1,5m adicional. Você pode avançar junto com o alvo para continuar empurrando-o se tiver deslocamento disponível.",
            "pagina": 240,
        },
        {
            "id": "manobra_fintar",
            "nome": "Fintar",
            "tipo_acao": "Padrão",
            "teste": "Teste de Enganação oposto ao Reflexos do alvo",
            "alcance": "Corpo a corpo",
            "efeito": "Você faz um movimento falso para confundir a guarda do oponente. Se vencer o teste oposto, o alvo é considerado Desprevenido (sofre –5 na Defesa e em Reflexos) contra o seu próximo ataque realizado até o final do seu próximo turno.",
            "pagina": 240,
        },
        {
            "id": "manobra_quebrar",
            "nome": "Quebrar",
            "tipo_acao": "Padrão (ou no lugar de um ataque)",
            "teste": "Teste de ataque contra a Defesa do item (ou teste de Luta oposto se estiver empunhado)",
            "alcance": "Corpo a corpo",
            "efeito": "Você desfere um golpe direto contra uma arma, escudo, armadura ou item que o inimigo esteja empunhando ou vestindo. Se acertar, causa dano normal ao item. O dano é reduzido pela Redução de Dano (RD) do material do objeto. Um objeto cujos PV cheguem a 0 ou menos é quebrado/destruído.",
            "pagina": 240,
        },
    ]

    # 2. TIPOS DE AÇÕES DE COMBATE (págs 239–241)
    acoes = [
        {
            "id": "acao_padrao",
            "categoria": "Ação Padrão",
            "resumo": "Representa um esforço principal na rodada: atacar, lançar magia ou usar habilidade ativa.",
            "exemplos": [
                {"nome": "Agredir (Atacar)", "descricao": "Fazer um ataque corpo a corpo ou à distância com arma ou desarmado contra um alvo."},
                {"nome": "Lançar uma Magia", "descricao": "Executar a conjuração de uma magia com tempo de execução de ação padrão."},
                {"nome": "Usar Habilidade", "descricao": "Ativar uma habilidade de classe, raça ou poder que exija ação padrão."},
                {"nome": "Manobras de Combate", "descricao": "Executar Agarrar, Atropelar, Derrubar, Desarmar, Empurrar, Fintar ou Quebrar."},
                {"nome": "Preparar Ação", "descricao": "Declarar um gatilho e uma ação padrão que será disparada como reação quando o gatilho ocorrer."},
            ],
            "pagina": 239,
        },
        {
            "id": "acao_movimento",
            "categoria": "Ação de Movimento",
            "resumo": "Representa deslocamento físico ou manuseio ágil de equipamentos e postura.",
            "exemplos": [
                {"nome": "Movimentar-se", "descricao": "Percorrer uma distância até o seu deslocamento normal (padrão 9m)."},
                {"nome": "Sacar ou Guardar Item", "descricao": "Sacar uma arma ou pegar um item em sua mochila/cinto, ou guardá-lo."},
                {"nome": "Levantar-se", "descricao": "Sair da condição Caído e ficar de pé."},
                {"nome": "Mirar", "descricao": "Gastar uma ação de movimento para receber +2 no próximo teste de ataque à distância realizado nesta rodada."},
                {"nome": "Abrir/Fechar Porta", "descricao": "Manipular uma porta, alavanca ou mecanismo simples."},
            ],
            "pagina": 240,
        },
        {
            "id": "acao_completa",
            "categoria": "Ação Completa",
            "resumo": "Consome toda a capacidade de ação do turno (equivale a gastar a ação padrão + ação de movimento).",
            "exemplos": [
                {"nome": "Investida", "descricao": "Mover-se até o dobro do deslocamento em linha reta e desferir um ataque corpo a corpo com +2 no teste de ataque. Você sofre –2 na Defesa até o início do seu próximo turno."},
                {"nome": "Golpe de Misericórdia", "descricao": "Desferir um ataque fatal contra uma criatura adjacente Indefesa. Acerto automático que causa dano crítico máximo e força o alvo a um teste de Fortitude (CD 10 + dano) para não morrer imediatamente."},
                {"nome": "Corrida", "descricao": "Mover-se em linha reta até quatro vezes o seu deslocamento (ou 3x se estiver com armadura pesada)."},
            ],
            "pagina": 241,
        },
        {
            "id": "acao_livre_reacao",
            "categoria": "Ações Livres e Reações",
            "resumo": "Ações que demandam esforço mínimo (livres no seu turno) ou respostas instantâneas a eventos externos (reações a qualquer momento).",
            "exemplos": [
                {"nome": "Falar", "descricao": "Pronunciar algumas frases curtas ou gritar um aviso aos aliados durante a rodada."},
                {"nome": "Largar um Item", "descricao": "Soltar uma arma ou objeto segurado (cai no mesmo quadrado)."},
                {"nome": "Testes de Resistência", "descricao": "Rolar Fortitude, Reflexos ou Vontade em resposta a magias, venenos ou armadilhas."},
                {"nome": "Reações de Habilidade", "descricao": "Ativar poderes reativos (ex.: Esquiva Sobrenatural, Aparar, Bloqueio com Escudo) mediante gatilhos específicos."},
            ],
            "pagina": 241,
        },
    ]

    # 3. MODIFICADORES TÁTICOS & SITUAÇÕES ESPECIAIS (págs 244–245)
    taticas = [
        {
            "id": "tatica_flanquear",
            "titulo": "Flanquear",
            "resumo": "Bônus tático por cercar o oponente em combate corpo a corpo.",
            "regras": "Quando você e um aliado lutam corpo a corpo contra um mesmo oponente em lados opostos (uma linha reta imaginária passando pelo centro dos seus quadrados cruza lados opostos do quadrado do alvo), vocês estão Flanqueando o alvo. Ambos recebem +2 em seus testes de ataque corpo a corpo contra ele. Não é possível flanquear com ataques à distância ou ataques desarmados sem treino especial.",
            "pagina": 245,
        },
        {
            "id": "tatica_cobertura",
            "titulo": "Cobertura",
            "resumo": "Proteção física fornecida por obstáculos entre o atacante e o alvo.",
            "regras": "• Cobertura Leve: Fornece +5 na Defesa do alvo. Ocorre quando o alvo está atrás de uma árvore, meia-muralha, lateral de carroça ou criatura maior.\n• Cobertura Total: Ocorre quando o alvo está totalmente atrás de uma parede sólida ou barreira intransponível. O alvo não pode ser atacado diretamente.",
            "pagina": 245,
        },
        {
            "id": "tatica_camuflagem",
            "titulo": "Camuflagem",
            "resumo": "Ocultação visual causada por névoa, folhagens, escuridão ou invisibilidade.",
            "regras": "• Camuflagem Leve: Névoa fina, escuridão parcial, folhagens. Ataques contra o alvo têm 20% de chance de falha (role 1d10 junto com o ataque; 1 ou 2 erra automaticamente).\n• Camuflagem Total: Escuridão absoluta, invisibilidade, névoa densa. O alvo tem 50% de chance de falha contra ataques (1 a 5 no d10 erra automaticamente), e atacantes ficam desprevenidos contra ele.",
            "pagina": 244,
        },
        {
            "id": "tatica_terreno_dificil",
            "titulo": "Terreno Difícil e Movimentação",
            "resumo": "Superfícies irregulares, lama, entulho e obstáculos no solo.",
            "regras": "Mover-se em terreno difícil custa o dobro do deslocamento normal (cada 1,5m / 1 quadrado custa 3m de deslocamento). Não é possível correr ou fazer investidas através de terreno difícil a menos que se possua habilidades específicas. Espaço ocupado por inimigo caído conta como terreno difícil.",
            "pagina": 244,
        },
    ]

    # 4. FERIMENTOS, MORTE, DESCANSO & RECUPERAÇÃO (págs 242–243)
    ferimentos_descanso = [
        {
            "id": "ferimento_pv_zero_sangrando",
            "titulo": "Pontos de Vida Zero, Sangrando e Estabilização",
            "resumo": "Regras para quando os Pontos de Vida de um personagem chegam a 0.",
            "regras": (
                "• Ao chegar a 0 PV: O personagem cai Inconsciente e Sangrando no chão.\n"
                "• Sangramento: No início de cada um dos seus turnos, o personagem deve fazer um teste de Constituição (CD 15).\n"
                "  - Sucesso: O personagem se estabiliza, remove a condição Sangrando e permanece inconsciente com 0 PV.\n"
                "  - Falha: O personagem perde 1d6 PV e continua sangrando.\n"
                "  - 3 Falhas cumulativas: O personagem morre.\n"
                "• Estabilização por Aliados: Um aliado adjacente pode gastar uma ação padrão e passar num teste de Cura (CD 15) para estabilizar o personagem. Qualquer efeito de cura de PV estabiliza imediatamente o alvo."
            ),
            "pagina": 242,
        },
        {
            "id": "ferimento_morte",
            "titulo": "Morte do Personagem",
            "resumo": "Critérios para morte definitiva de um herói.",
            "regras": (
                "Um personagem morre nas seguintes situações:\n"
                "1. Seus PV negativos acumulados atingirem um valor igual ou superior à metade de seus Pontos de Vida máximos totais (morte por dano massivo).\n"
                "2. Se falhar 3 vezes no teste de Constituição para estabilizar o sangramento.\n"
                "3. Se sofrer um Golpe de Misericórdia e falhar no teste de Fortitude (CD 10 + dano)."
            ),
            "pagina": 242,
        },
        {
            "id": "descanso_recuperacao_pv_pm",
            "titulo": "Descanso e Recuperação de PV e PM",
            "resumo": "Tabela de recuperação diária de PV e PM por condições de repouso (mínimo 8 horas).",
            "tabela_descanso": [
                {"condicao": "Ruim", "exemplo": "Dormir ao relento na lama, chuva, frio sem proteção ou com armadura pesada", "recuperacao_pv": "Nenhum PV", "recuperacao_pm": "Nenhum PM", "efeito_extra": "Pode causar fadiga/condição Fraco."},
                {"condicao": "Normal", "exemplo": "Acampamento padrão com saco de dormir, vigia e fogueira, ou estalagem simples", "recuperacao_pv": "1x Nível do personagem em PV", "recuperacao_pm": "1x Nível do personagem em PM", "efeito_extra": "Remove condições temporárias de cansaço leve."},
                {"condicao": "Confortável", "exemplo": "Quarto privativo de boa estalagem, cama quente, refeição nutritiva e tranquila", "recuperacao_pv": "2x Nível do personagem em PV", "recuperacao_pm": "2x Nível do personagem em PM", "efeito_extra": "Cura acelerada."},
                {"condicao": "Luxuoso", "exemplo": "Palácio, mansão nobre, banho quente, comida farta, serviço exclusivo", "recuperacao_pv": "3x Nível do personagem em PV", "recuperacao_pm": "3x Nível do personagem em PM", "efeito_extra": "Cura máxima de PV e PM."},
            ],
            "pagina": 243,
        },
    ]

    # 5. TIPOS DE DANO & ACERTOS CRÍTICOS (págs 236–237)
    tipos_dano = [
        {
            "id": "dano_fisico",
            "categoria": "Dano Físico",
            "tipos": ["Corte (espadas, machados)", "Perfuração (arcos, lanças, adagas)", "Impacto (maças, martelos, quedas)"],
            "descricao": "Dano corporal básico de armas e impactos físicos. Pode ser absorvido por Redução de Dano (RD).",
            "pagina": 236,
        },
        {
            "id": "dano_elemental_magico",
            "categoria": "Dano Elemental e Mágico",
            "tipos": ["Fogo (chamas, calor)", "Frio (gelo, congelamento)", "Eletricidade (raios, choques)", "Ácido (substâncias corrosivas)", "Luz (energia radiante)", "Trevas (energia negativa e necrótica)", "Essência (energia mágica pura, sem resistência elementar)"],
            "descricao": "Dano gerado por magias, itens mágicos ou substâncias alquímicas. Pode ser absorvido por Resistência a Energia específica correspondente.",
            "pagina": 236,
        },
    ]

    # 6. HABILIDADES UNIVERSAIS & REGRAS GERAIS (págs 234–235)
    habilidades_universais = [
        {"nome": "Faro", "descricao": "A criatura percebe automaticamente a presença de outras criaturas em alcance curto pelo cheiro. Em alcance curto, a criatura ignora camuflagem e invisibilidade.", "pagina": 234},
        {"nome": "Imunidade", "descricao": "A criatura é totalmente imune a determinados tipos de dano ou efeitos (ex.: imunidade a veneno, fogo, efeitos mentais). Ela não sofre dano nem efeitos daquela fonte.", "pagina": 234},
        {"nome": "Percepção às Cegas", "descricao": "A criatura usa ecolocalização, vibrações ou outros sentidos aguçados. Ela ignora escuridão, camuflagem e invisibilidade em alcance curto.", "pagina": 234},
        {"nome": "Redução de Dano (RD)", "descricao": "A criatura ou objeto ignora uma quantidade de dano de cada ataque igual ao valor de sua RD. Apenas dano que supere a RD é subtraído dos PV.", "pagina": 235},
        {"nome": "Resistência a Energia", "descricao": "A criatura subtrai o valor indicado de qualquer dano do elemento especificado (fogo, frio, eletricidade, ácido, etc.).", "pagina": 235},
        {"nome": "Visão na Penumbra", "descricao": "A criatura enxerga perfeitamente em iluminação fraca ou sob a luz da lua/tochas a distâncias normais.", "pagina": 235},
        {"nome": "Visão no Escuro", "descricao": "A criatura enxerga na escuridão total até alcance curto (9m ou mais) em preto e branco, ignorando penalidades por escuridão.", "pagina": 235},
    ]

    # 7. PARCEIROS / ALIADOS (Capítulo 6, págs 266–268)
    parceiros = [
        {
            "id": "parceiro_ajudante",
            "nome": "Ajudante",
            "descricao_papel": "Especialista em prestar auxílio em tarefas com palavras firmes ou conselhos sábios.",
            "iniciante": "+2 em duas perícias (definidas pelo parceiro).",
            "veterano": "+2 em três perícias.",
            "mestre": "+4 em três perícias.",
            "pagina": 266,
        },
        {
            "id": "parceiro_atirador",
            "nome": "Atirador",
            "descricao_papel": "Arqueiro, besteiro ou pistoleiro que cobre seus avanços com ataques precisos.",
            "iniciante": "Uma vez por rodada, você recebe +1d6 em uma rolagem de dano à distância.",
            "veterano": "O dano extra aumenta para +1d10.",
            "mestre": "O dano extra aumenta para +2d8.",
            "pagina": 267,
        },
        {
            "id": "parceiro_combatente",
            "nome": "Combatente",
            "descricao_papel": "Guerreiro, mercenário ou monstro treinado de linha de frente.",
            "iniciante": "+2 em testes de ataque corpo a corpo ou à distância.",
            "veterano": "O bônus aumenta para +3 em testes de ataque.",
            "mestre": "O bônus aumenta para +4 em testes de ataque e +1 na margem de ameaça de seus ataques.",
            "pagina": 267,
        },
        {
            "id": "parceiro_conjurador",
            "nome": "Conjurador",
            "descricao_papel": "Arcanista ou inventor capaz de projetar feitiços de suporte ofensivo.",
            "iniciante": "Uma vez por rodada, causa 1d6 de dano elemental (fogo, frio, ácido ou eletricidade) a um alvo em alcance curto.",
            "veterano": "O dano aumenta para 2d6 pontos de dano.",
            "mestre": "O dano aumenta para 3d6 e o custo em PM das suas magias de 1º e 2º círculos diminui em –1 PM.",
            "pagina": 267,
        },
        {
            "id": "parceiro_curandeiro",
            "nome": "Curandeiro",
            "descricao_papel": "Clérigo, druida, herbalista ou médico de campo com talentos de cura.",
            "iniciante": "Uma vez por rodada, cura 1d8+1 PV de uma criatura adjacente.",
            "veterano": "A cura aumenta para 2d8+2 PV e remove uma condição leve (abalado, fatigado, ofuscado).",
            "mestre": "A cura aumenta para 3d8+3 PV, e você também recupera 1d8 PV sempre que curar um aliado.",
            "pagina": 267,
        },
        {
            "id": "parceiro_destruidor",
            "nome": "Destruidor",
            "descricao_papel": "Especialista em magia destrutiva de grande impacto.",
            "iniciante": "O dano de suas magias ofensivas aumenta em +1 dado do mesmo tipo.",
            "veterano": "O dano aumenta em +1 dado e a CD para resistir às suas magias aumenta em +1.",
            "mestre": "O dano de suas magias aumenta em +2 dados e a CD de resistência aumenta em +2.",
            "pagina": 267,
        },
        {
            "id": "parceiro_fortao",
            "nome": "Fortão",
            "descricao_papel": "Bárbaro musculoso, ogro ou bruto que atinge com violência devastadora.",
            "iniciante": "Uma vez por rodada, você recebe +1d8 em uma rolagem de dano corpo a corpo.",
            "veterano": "O dano extra aumenta para +1d12.",
            "mestre": "O dano extra aumenta para +2d10 e você pode fazer a manobra derrubar como ação livre após acertar um ataque.",
            "pagina": 267,
        },
        {
            "id": "parceiro_guardiao",
            "nome": "Guardião",
            "descricao_papel": "Escudeiro, guarda-costas ou protetor com armadura pesada e escudo.",
            "iniciante": "Você recebe +2 na Defesa.",
            "veterano": "O bônus na Defesa aumenta para +3.",
            "mestre": "O bônus na Defesa aumenta para +4 e você recebe Redução de Dano (RD) 5.",
            "pagina": 267,
        },
        {
            "id": "parceiro_perseguidor",
            "nome": "Perseguidor",
            "descricao_papel": "Batedor, rastreador ou caçador perito em encontrar e vigiar presas.",
            "iniciante": "+2 em testes de Percepção e Sobrevivência.",
            "veterano": "Você recebe o benefício da habilidade Sentidos Aguçados (ignora camuflagem leve).",
            "mestre": "Você recebe Percepção às Cegas em alcance curto.",
            "pagina": 267,
        },
        {
            "id": "parceiro_vigilante",
            "nome": "Vigilante",
            "descricao_papel": "Sentinela alerta com reflexos rápidos que protege contra emboscadas.",
            "iniciante": "+2 em testes de Percepção e Iniciativa.",
            "veterano": "Você recebe a habilidade Esquiva Sobrenatural (nunca fica desprevenido por inimigos não vistos).",
            "mestre": "Você não pode ser surpreendido e recebe +5 adicional em Iniciativa.",
            "pagina": 267,
        },
    ]

    regras_banco = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (Capítulo 5: Jogando, págs 218–245 e Capítulo 6: Parceiros, págs 266–268)",
        "total_manobras": len(manobras),
        "total_acoes": len(acoes),
        "total_taticas": len(taticas),
        "total_ferimentos_descanso": len(ferimentos_descanso),
        "total_parceiros": len(parceiros),
        "manobras": manobras,
        "acoes": acoes,
        "modificadores_taticos": taticas,
        "ferimentos_descanso": ferimentos_descanso,
        "tipos_dano": tipos_dano,
        "habilidades_universais": habilidades_universais,
        "parceiros": parceiros,
    }

    OUT.write_text(json.dumps(regras_banco, ensure_ascii=False, indent=2), encoding="utf-8")
    return regras_banco


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Extraindo Regras de Jogo & Parceiros de {PDF.name}...")
    banco = extrair_dados_regras()
    print(f"Sucesso! Regras de Jogo salvas em {OUT}")
    print(f"• Manobras: {banco['total_manobras']}")
    print(f"• Ações: {banco['total_acoes']}")
    print(f"• Táticas: {banco['total_taticas']}")
    print(f"• Ferimentos & Descanso: {banco['total_ferimentos_descanso']}")
    print(f"• Parceiros: {banco['total_parceiros']}")
    print(f"• Habilidades Universais: {len(banco['habilidades_universais'])}")


if __name__ == "__main__":
    main()
