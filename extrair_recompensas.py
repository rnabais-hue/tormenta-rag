# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Capítulo 8: Recompensas (págs 330–355) de Tormenta20 (Edição Jogo do Ano).

Extrai:
  1. Regras de Recompensas e Tabela 8-1: Riqueza e Tesouro por ND (ND 1/4 a 20+).
  2. Regras de Itens Mágicos (Uso/Sintonia até 4 itens, Fabricação, Destruição e RD).
  3. Encantos de Armas (28+ encantamentos mágicos com bônus e efeito completo).
  4. Armas Específicas (12+ armas com estatísticas completas).
  5. Encantos de Armaduras & Escudos (24+ encantamentos de proteção).
  6. Armaduras & Escudos Específicos (8+ armaduras/escudos lendários).
  7. Poções & Pergaminhos (regras e tabelas de preço por círculo de magia 1º ao 5º).
  8. Acessórios Mágicos (~40 acessórios com espaço ocupado, preço em T$ e efeitos).
  9. Artefatos Supremos (7 artefatos lendários com poderes épicos).

Lê o PDF; escreve dados/recompensas.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
OUT = BASE / "dados" / "recompensas.json"
OUT.parent.mkdir(exist_ok=True)


def extrair_dados_recompensas():
    # 1. REGRAS GERAIS DE ITENS MÁGICOS E TESOUROS
    regras_gerais = [
        {
            "id": "regra_itens_magicos_uso",
            "nome": "Regras de Uso e Sintonia de Itens Mágicos",
            "categoria": "regras_gerais",
            "texto": (
                "REGRAS DE USO E SINTONIA DE ITENS MÁGICOS:\n"
                "• Limite de Itens: Um personagem só pode se beneficiar de no máximo 4 itens mágicos vestidos ou empunhados simultaneamente (incluindo armas, armaduras, escudos e acessórios). Itens de uso único (poções, pergaminhos) não contam para este limite.\n"
                "• Ativação: A maioria dos itens mágicos requer uma ação de movimento ou padrão para ativar, ou funciona passivamente enquanto vestido.\n"
                "• Troca de Itens: Desequipar um item mágico e vestir outro requer tempo de descanso ou ajuste conforme a categoria do item."
            ),
            "pagina": 339,
        },
        {
            "id": "regra_itens_magicos_fabricacao",
            "nome": "Fabricação e Destruição de Itens Mágicos",
            "categoria": "regras_gerais",
            "texto": (
                "FABRICAÇÃO E DESTRUIÇÃO DE ITENS MÁGICOS:\n"
                "• Fabricação: Exige a habilidade Fabricar Item Mágico (ou equivalente de Inventor/Ladino/Arcanista), matéria-prima igual a 1/3 do preço em T$, fórmulas conhecidas e investimento de Pontos de Mana (PM) permanentes ou materiais arcanos raros.\n"
                "• Destruição: Itens mágicos são extremamente resistentes. Possuem Redução de Dano (RD) igual ao dobro de um item comum de mesmo material + 5 para cada encanto, e seus PV são aumentados substancialmente. Artefatos só podem ser destruídos por meios lendários específicos."
            ),
            "pagina": 340,
        },
        {
            "id": "regra_tabela_tesouro_nd",
            "nome": "Tabela 8-1: Riqueza e Tesouros por Nível de Desafio (ND)",
            "categoria": "regras_gerais",
            "texto": (
                "TABELA 8-1: RIQUEZA E TESOURO POR ND (Resumo de Progressão):\n"
                "• ND 1/4 a 1: Dinheiro: 1d6x10 T$ | Itens: 1 item comum ou poção de 1º círculo.\n"
                "• ND 2 a 4: Dinheiro: 2d6x50 T$ | Itens: 1 item superior (1–2 melhorias) ou poção/pergaminho de 1º/2º círculo.\n"
                "• ND 5 a 8: Dinheiro: 3d6x200 T$ | Itens: 1 item mágico menor (1 encanto menor) ou item superior (3 melhorias).\n"
                "• ND 9 a 12: Dinheiro: 4d6x500 T$ | Itens: 1 item mágico médio (1–2 encantos médios) ou acessório menor.\n"
                "• ND 13 a 16: Dinheiro: 5d6x1.000 T$ | Itens: 1 item mágico maior (2–3 encantos maiores) ou acessório médio.\n"
                "• ND 17 a 20+: Dinheiro: 6d6x5.000 T$ | Itens: 1 item mágico lendário/maior (3+ encantos maiores) ou acessório maior/artefato menor."
            ),
            "pagina": 333,
        },
        {
            "id": "regra_pocoes_pergaminhos",
            "nome": "Poções e Pergaminhos (Preços e Círculos de Magia)",
            "categoria": "regras_gerais",
            "texto": (
                "POÇÕES E PERGAMINHOS MÁGICOS:\n"
                "• 1º Círculo: Poção = T$ 30 | Pergaminho = T$ 15\n"
                "• 2º Círculo: Poção = T$ 150 | Pergaminho = T$ 75\n"
                "• 3º Círculo: Poção = T$ 450 | Pergaminho = T$ 225\n"
                "• 4º Círculo: Poção = T$ 1.050 | Pergaminho = T$ 525\n"
                "• 5º Círculo: Poção = T$ 2.250 | Pergaminho = T$ 1.125\n"
                "• Uso de Poções: Beber uma poção é uma ação padrão (ou de movimento se sacada previamente). Poções afetam quem as bebe ou o alvo tocado (se for óleo).\n"
                "• Uso de Pergaminhos: Ler um pergaminho exige ação padrão e teste de Misticismo (CD 15 + custo em PM da magia) para conjuradores que não tenham a magia em sua lista."
            ),
            "pagina": 347,
        },
    ]

    # 2. ENCANTOS DE ARMAS (28 Encantos)
    encantos_armas = [
        {"nome": "Aborrecedora", "preco_bonus": "+1 encanto", "efeito": "Ao acertar uma criatura com Inteligência 3 ou mais, o alvo fica Frustrado e sofre –2 em testes de ataque até o fim do seu próximo turno.", "pagina": 341},
        {"nome": "Ameaçadora", "preco_bonus": "+1 encanto", "efeito": "Dobra a margem de ameaça da arma (ex: de 19–20 para 17–20). Não acumula com outras fontes que dobrem a margem de ameaça.", "pagina": 341},
        {"nome": "Antagônica", "preco_bonus": "+1 encanto", "efeito": "Escolha um tipo de criatura (humanoides, monstros, mortos-vivos, lefeu, etc.). A arma causa +2d6 de dano e +2 no ataque contra criaturas desse tipo.", "pagina": 341},
        {"nome": "Arremesso", "preco_bonus": "+1 encanto", "efeito": "Permite que a arma corpo a corpo seja arremessada com alcance curto. Ela retorna magicamente à mão do atacante logo após o ataque.", "pagina": 341},
        {"nome": "Asfixiante", "preco_bonus": "+1 encanto", "efeito": "Ao acertar um acerto crítico, o alvo começa a sufocar (gasta ação padrão para respirar por rodada ou sofre 1d6 de dano de essência).", "pagina": 341},
        {"nome": "Assassina", "preco_bonus": "+2 encantos", "efeito": "Causa +2d10 de dano extra em alvos desprevenidos ou alvos flanqueados.", "pagina": 341},
        {"nome": "Caçadora", "preco_bonus": "+1 encanto", "efeito": "Ignora camuflagem leve e cobertura leve, e fornece +2 em testes de Percepção e Sobrevivência para rastrear alvos.", "pagina": 341},
        {"nome": "Congelante", "preco_bonus": "+1 encanto", "efeito": "Causa +1d6 de dano de frio em cada ataque e pode congelar água em contato.", "pagina": 341},
        {"nome": "Conjuradora", "preco_bonus": "+1 encanto", "efeito": "Pode armazenar uma magia de até 3º círculo. Ao acertar um ataque, o usuário pode descarregar a magia no alvo como ação livre.", "pagina": 341},
        {"nome": "Corrosiva", "preco_bonus": "+1 encanto", "efeito": "Causa +1d6 de dano de ácido em cada ataque e causa dano contínuo de ácido na rodada seguinte em acertos críticos.", "pagina": 341},
        {"nome": "Dançarina", "preco_bonus": "+2 encantos", "efeito": "Com uma ação de movimento, o usuário solta a arma e ela flutua lutando sozinha por até 4 rodadas com as estatísticas do usuário.", "pagina": 341},
        {"nome": "Defensora", "preco_bonus": "+1 encanto", "efeito": "Permite transferir parte ou todo o bônus de melhoria/ataque da arma para a Defesa do usuário.", "pagina": 341},
        {"nome": "Destruidora", "preco_bonus": "+1 encanto", "efeito": "Aumenta o dano contra objetos e construtos em +2d8 e ignora metade da RD do material.", "pagina": 341},
        {"nome": "Distante", "preco_bonus": "+1 encanto", "efeito": "Dobra o alcance de armas de disparo ou arremesso.", "pagina": 341},
        {"nome": "Drenante", "preco_bonus": "+2 encantos", "efeito": "Ao acertar um acerto crítico, drena a força vital do alvo: o usuário recupera PV iguais a metade do dano total causado.", "pagina": 341},
        {"nome": "Eletrizante", "preco_bonus": "+1 encanto", "efeito": "Causa +1d6 de dano de eletricidade em cada ataque. Em acerto crítico, o alvo fica Atordoado por 1 rodada (Fortitude CD 15 anula).", "pagina": 341},
        {"nome": "Energética", "preco_bonus": "+2 encantos", "efeito": "A lâmina ou projétil é feito de pura luz/energia: seu dano torna-se dano de essência e ignora a Defesa vinda de armaduras e escudos.", "pagina": 341},
        {"nome": "Excruciante", "preco_bonus": "+1 encanto", "efeito": "Causa dor atroz: criaturas atingidas sofrem –2 em testes de perícia por 1 rodada.", "pagina": 341},
        {"nome": "Flamejante", "preco_bonus": "+1 encanto", "efeito": "A arma irrompe em chamas mágicas ao comando: causa +1d6 de dano de fogo em cada ataque e ilumina como uma tocha.", "pagina": 341},
        {"nome": "Formidável", "preco_bonus": "+1 encanto", "efeito": "Fornece +2 adicional em testes de ataque e rolagens de dano com a arma.", "pagina": 341},
        {"nome": "Lancinante", "preco_bonus": "+1 encanto", "efeito": "Multiplica todos os dados de dano da arma e bônus numéricos em acertos críticos conforme o multiplicador da arma.", "pagina": 341},
        {"nome": "Magnífica", "preco_bonus": "+3 encantos", "efeito": "Fornece +4 em testes de ataque e dano com a arma e emana aura de imponência que confere +2 em Carisma.", "pagina": 341},
        {"nome": "Pungente", "preco_bonus": "+1 encanto", "efeito": "Aumenta a margem de ameaça em +1 e a CD para resistir a habilidades da arma em +2.", "pagina": 341},
        {"nome": "Sagrada", "preco_bonus": "+2 encantos", "efeito": "Causa +2d6 de dano de luz contra mortos-vivos e criaturas malignas/abissais, e emana luz sagrada contínua.", "pagina": 341},
        {"nome": "Sanguinária", "preco_bonus": "+1 encanto", "efeito": "Causa a condição Sangrando no alvo ao acertar um ataque (1d6 de dano de sangramento cumulativo por rodada).", "pagina": 341},
        {"nome": "Tumular", "preco_bonus": "+1 encanto", "efeito": "Causa +1d6 de dano de trevas e concede +2 em testes de resistência contra efeitos de necromancia.", "pagina": 341},
        {"nome": "Veloz", "preco_bonus": "+2 encantos", "efeito": "Concede um ataque corpo a corpo ou à distância adicional por rodada quando o usuário realiza a ação Agredir.", "pagina": 341},
        {"nome": "Venenosa", "preco_bonus": "+1 encanto", "efeito": "Produz veneno mágico natural: alvos atingidos sofrem 1d12 de dano de veneno (Fortitude CD 15 reduz à metade).", "pagina": 341},
        {"nome": "Vorpal", "preco_bonus": "+3 encantos", "efeito": "Ao rolar um 20 natural em uma rolagem de ataque corpo a corpo cortante, decapita instantaneamente criaturas com cabeça (morte imediata ou dano massivo).", "pagina": 341},
    ]

    # 3. ARMAS ESPECÍFICAS (10 Armas)
    armas_especificas = [
        {"nome": "Arco do Poder", "preco": "T$ 18.000", "tipo": "Arco Longo", "efeito": "Arco longo formidável que permite somar o modificador de Força do usuário nas rolagens de dano, sem limite.", "pagina": 342},
        {"nome": "Azagaia do Relâmpago", "preco": "T$ 3.000", "tipo": "Azagaia", "efeito": "Ao ser arremessada, transforma-se em um relâmpago que causa 8d6 de dano de eletricidade em linha reta (Reflexos CD 17 reduz à metade).", "pagina": 342},
        {"nome": "Chicote de Presas", "preco": "T$ 15.000", "tipo": "Chicote", "efeito": "Chicote farpado venenoso e ameaçador que pode se transformar em uma serpente venenosa com uma ação de movimento.", "pagina": 342},
        {"nome": "Espada da Justiça", "preco": "T$ 40.000", "tipo": "Espada Longa", "efeito": "Espada longa sagrada e formidável de Khalmyr que permite conjurar Imobilizar (CD 20) 1x por dia contra criaturas criminosas ou injustas.", "pagina": 343},
        {"nome": "Espada Solar", "preco": "T$ 35.000", "tipo": "Espada Curta/Longa", "efeito": "Espada mágica flamejante e luminosa que emana luz do sol plena (cega criaturas sensíveis à luz e causa dano dobrado em vampiros).", "pagina": 343},
        {"nome": "Lança da Montaria", "preco": "T$ 16.000", "tipo": "Lança Montada", "efeito": "Lança montada formidável que triplica o dano em investidas montadas e concede +5 em testes de Cavalgar.", "pagina": 343},
        {"nome": "Machado das Tempestades", "preco": "T$ 50.000", "tipo": "Machado de Batalha", "efeito": "Machado eletrizante e congelante que permite conjurar Relâmpago 3x por dia e controlar ventos.", "pagina": 343},
        {"nome": "Maça do Terror", "preco": "T$ 22.000", "tipo": "Maça", "efeito": "Maça tumular que causa a condição Amedrontado em todos os inimigos a até 9m ao acertar um acerto crítico (Vontade CD 18 anula).", "pagina": 343},
        {"nome": "Martelo do Trovão", "preco": "T$ 45.000", "tipo": "Martelo de Guerra", "efeito": "Martelo de arremesso eletrizante e destruidor que emite um estrondo sônico estrondoso ao atingir o solo (derruba todos os inimigos em alcance curto).", "pagina": 343},
        {"nome": "Tridente do Povo do Mar", "preco": "T$ 20.000", "tipo": "Tridente", "efeito": "Tridente sagrado de Oceano que concede deslocamento de natação 18m, respiração subaquática e imunidade a penalidades de combate embaixo d'água.", "pagina": 343},
    ]

    # 4. ENCANTOS DE ARMADURAS E ESCUDOS (24 Encantos)
    encantos_armaduras = [
        {"nome": "Abençoada", "preco_bonus": "+1 encanto", "efeito": "Concede +2 em testes de resistência contra magias divinas e efeitos de necromancia.", "pagina": 344},
        {"nome": "Animada", "preco_bonus": "+2 encantos (Apenas Escudos)", "efeito": "Com uma ação de movimento, o escudo flutua sozinho ao lado do usuário, fornecendo seu bônus de Defesa sem ocupar as mãos.", "pagina": 344},
        {"nome": "Apaixonante", "preco_bonus": "+1 encanto", "efeito": "Inimigos que atacam o portador devem passar em teste de Vontade CD 15 ou ficam Enfeitiçados até o final da rodada.", "pagina": 344},
        {"nome": "Asfixiante", "preco_bonus": "+1 encanto", "efeito": "Envolve o usuário em ar respirável puro contínuo, tornando-o imune a gases venenosos, afogamento e sufocamento.", "pagina": 344},
        {"nome": "Bastião", "preco_bonus": "+1 encanto", "efeito": "Aumenta a Redução de Dano (RD) da armadura em +2 e concede +2 em testes de resistência contra manobras de combate.", "pagina": 344},
        {"nome": "Camuflada", "preco_bonus": "+1 encanto", "efeito": "Elimina a penalidade de armadura em testes de Furtividade e concede +2 nessa perícia.", "pagina": 344},
        {"nome": "Defensora", "preco_bonus": "+1 encanto", "efeito": "Aumenta o bônus de Defesa concedido pela armadura ou escudo em +1 adicional.", "pagina": 344},
        {"nome": "Deslizante", "preco_bonus": "+1 encanto", "efeito": "Superfície oleosa e escorregadia: concede +5 em testes de Acrobacia e Reflexos para escapar de Agarrar ou manobras.", "pagina": 344},
        {"nome": "Destemida", "preco_bonus": "+1 encanto", "efeito": "Torna o usuário totalmente imune à condição Amedrontado e efeitos de medo.", "pagina": 344},
        {"nome": "Espinhosa", "preco_bonus": "+1 encanto", "efeito": "Coberta de pontas afiadas: qualquer criatura que atacar o usuário desarmada ou que o agarrar sofre 1d6 de dano de perfuração.", "pagina": 344},
        {"nome": "Fantasmagórica", "preco_bonus": "+2 encantos", "efeito": "Permite que a armadura se torne incorpórea por breves instantes: protege totalmente contra ataques de criaturas incorpóreas e fantasmas.", "pagina": 344},
        {"nome": "Fortificada", "preco_bonus": "+2 encantos", "efeito": "75% de chance (1–3 em 1d4) de converter qualquer acerto crítico ou ataque furtivo sofrido em um acerto normal.", "pagina": 344},
        {"nome": "Guardiã", "preco_bonus": "+2 encantos", "efeito": "Permite usar uma reação para transferir até metade da Defesa do escudo para proteger um aliado adjacente.", "pagina": 344},
        {"nome": "Ilusória", "preco_bonus": "+1 encanto", "efeito": "Pode mudar de aparência mágica ao comando do usuário para se parecer com roupas civis elegantes, batas de monge ou trapos.", "pagina": 344},
        {"nome": "Impenetrável", "preco_bonus": "+2 encantos", "efeito": "Concede Redução de Dano (RD) 5 contra todos os tipos de dano físico (corte, perfuração e impacto).", "pagina": 344},
        {"nome": "Invulnerável", "preco_bonus": "+3 encantos", "efeito": "Concede Redução de Dano (RD) 10 contra dano físico e +5 em testes de resistência contra magias de dano.", "pagina": 344},
        {"nome": "Polida", "preco_bonus": "+1 encanto", "efeito": "Reflete luz mágica: ofusca oponentes que erram ataques corpo a corpo (ficam Ofuscados por 1 rodada).", "pagina": 344},
        {"nome": "Protetora", "preco_bonus": "+1 encanto", "efeito": "Concede +2 em todos os testes de resistência (Fortitude, Reflexos e Vontade).", "pagina": 344},
        {"nome": "Refletora", "preco_bonus": "+2 encantos (Apenas Escudos)", "efeito": "1x por rodada, se um ataque mágico à distância ou raio errar o portador, o raio é refletido de volta contra o conjurador.", "pagina": 344},
        {"nome": "Reluzente", "preco_bonus": "+1 encanto", "efeito": "Emana luz pura contínua e emite um clarão ofuscante 1x por dia que cega inimigos adjacentes (Fortitude CD 17 anula).", "pagina": 344},
        {"nome": "Resistente", "preco_bonus": "+1 encanto", "efeito": "Escolha um tipo de energia elemental (fogo, frio, ácido ou eletricidade): concede Resistência a Energia 10 ao tipo escolhido.", "pagina": 344},
        {"nome": "Retribuidora", "preco_bonus": "+2 encantos", "efeito": "Sempre que o usuário for atingido por um ataque corpo a corpo, a armadura causa metade do dano sofrido de volta ao atacante.", "pagina": 344},
        {"nome": "Salteadora", "preco_bonus": "+1 encanto", "efeito": "Aumenta o deslocamento do usuário em +3m e concede +2 em testes de Atletismo.", "pagina": 344},
        {"nome": "Sombria", "preco_bonus": "+1 encanto", "efeito": "Camufla nas sombras: concede camuflagem leve ao usuário em ambientes de penumbra e escuridão.", "pagina": 344},
    ]

    # 5. ARMADURAS E ESCUDOS ESPECÍFICOS (8 Itens)
    armaduras_especificas = [
        {"nome": "Armadura da Donzela", "preco": "T$ 25.000", "tipo": "Armadura Completa", "efeito": "Armadura completa impecável e apaixonante que concede +5 em Diplomacia e reduz em –5 o dano de ataques masculinos.", "pagina": 346},
        {"nome": "Armadura do Dragão", "preco": "T$ 48.000", "tipo": "Couraça / Completa", "efeito": "Forjada com escamas de dragão vermelho: concede Resistência a Fogo 20, RD 5 e imunidade à presença aterradora de dragões.", "pagina": 346},
        {"nome": "Carapaça de Ferro", "preco": "T$ 32.000", "tipo": "Armadura Pesada", "efeito": "Armadura pesada de aço anão com RD 5 e imunidade a manobras de Derrubar e Empurrar.", "pagina": 346},
        {"nome": "Cota da Rapidez", "preco": "T$ 22.000", "tipo": "Cota de Malha", "efeito": "Cota de malha leve e salteadora que não possui penalidade de armadura e permite conjurar Velocidade em si mesmo 1x por dia.", "pagina": 346},
        {"nome": "Escudo de Valkaria", "preco": "T$ 30.000", "tipo": "Escudo Pesado", "efeito": "Escudo sagrado da Deusa da Ambição que concede +2 na Defesa, +2 em todos os testes de perícia e imunidade a paralisia.", "pagina": 346},
        {"nome": "Escudo Espelho", "preco": "T$ 26.000", "tipo": "Escudo Leve", "efeito": "Escudo polido e refletor de prata pura que reflete ataques mágicos e protege contra olhares petrificantes de medusas e basiliscos.", "pagina": 346},
        {"nome": "Manto de Teias", "preco": "T$ 18.000", "tipo": "Armadura Leve", "efeito": "Armadura de couro batido de seda de aranha gigante: concede deslocamento de escalada 9m e imunidade a teias e paralisia.", "pagina": 346},
        {"nome": "Placas do Titã", "preco": "T$ 55.000", "tipo": "Armadura Completa", "efeito": "Armadura colossal com RD 10 que concede +4 em Força e permite ao usuário aumentar seu tamanho em uma categoria 1x por dia.", "pagina": 346},
    ]

    # 6. ACESSÓRIOS MÁGICOS (~25 Principais Acessórios)
    acessorios = [
        {"nome": "Anel da Proteção", "espaco": "1 dedo", "preco": "T$ 10.000", "efeito": "Concede +2 na Defesa e +2 em todos os testes de resistência.", "pagina": 348},
        {"nome": "Anel de Cura", "espaco": "1 dedo", "preco": "T$ 15.000", "efeito": "Aumenta a cura de todas as magias e habilidades de cura utilizadas pelo usuário em +1 PV por dado rolado.", "pagina": 348},
        {"nome": "Anel de Regeneração", "espaco": "1 dedo", "preco": "T$ 40.000", "efeito": "Regenera 5 PV por rodada enquanto o usuário estiver vivo, e permite regenerar membros decepados em 2d4 dias.", "pagina": 348},
        {"nome": "Anel do Invisível", "espaco": "1 dedo", "preco": "T$ 30.000", "efeito": "Permite ao usuário conjurar Invisibilidade em si mesmo à vontade como ação padrão.", "pagina": 348},
        {"nome": "Botas Aladas", "espaco": "Pés", "preco": "T$ 24.000", "efeito": "Concedem deslocamento de voo 12m por até 1 hora por dia (dividido em blocos conforme necessário).", "pagina": 348},
        {"nome": "Botas da Velocidade", "espaco": "Pés", "preco": "T$ 20.000", "efeito": "Concedem a habilidade de dobrar o deslocamento terrestre e realizar uma ação de movimento extra por rodada por até 5 rodadas/dia.", "pagina": 348},
        {"nome": "Braçadeiras da Força", "espaco": "Braços", "preco": "T$ 16.000", "efeito": "Concedem +2 no atributo Força e +2 em testes de Atletismo.", "pagina": 349},
        {"nome": "Brincos da Sagacidade", "espaco": "Orelhas", "preco": "T$ 16.000", "efeito": "Concedem +2 no atributo Sabedoria e +2 em testes de Percepção e Intuição.", "pagina": 349},
        {"nome": "Broche do Escudo", "espaco": "Peitoral", "preco": "T$ 8.000", "efeito": "Absorve até 50 pontos de dano provenientes de magias de projéteis de força (como Mísseis Mágicos).", "pagina": 349},
        {"nome": "Capa da Bruxaria", "espaco": "Ombros", "preco": "T$ 28.000", "efeito": "Concede +2 na CD de todas as magias conjuradas pelo usuário e +5 Pontos de Mana (PM) máximos.", "pagina": 349},
        {"nome": "Capa do Saltimbanco", "espaco": "Ombros", "preco": "T$ 14.000", "efeito": "Permite conjurar Salto Dimensional 1x por dia e concede +5 em testes de Acrobacia e Atuação.", "pagina": 349},
        {"nome": "Cinto do Campeão", "espaco": "Cintura", "preco": "T$ 25.000", "efeito": "Concede +2 em Constituição, +2 em Força e imunidade a ficar Fatigado.", "pagina": 349},
        {"nome": "Colar de Contas", "espaco": "Pescoço", "preco": "T$ 12.000", "efeito": "Colar com esferas vermelhas mágicas que podem ser destacadas e arremessadas como Bolas de Fogo (6d6 de fogo cada).", "pagina": 350},
        {"nome": "Luvas da Destreza", "espaco": "Mãos", "preco": "T$ 16.000", "efeito": "Concedem +2 no atributo Destreza e +2 em testes de Ladinagem e Reflexos.", "pagina": 350},
        {"nome": "Manto da Noite", "espaco": "Ombros", "preco": "T$ 18.000", "efeito": "Concede Visão no Escuro, +5 em testes de Furtividade e imunidade a dano de trevas.", "pagina": 350},
        {"nome": "Pingente da Sensibilidade", "espaco": "Pescoço", "preco": "T$ 16.000", "efeito": "Concede +2 no atributo Carisma e +2 em testes de Diplomacia e Enganação.", "pagina": 350},
        {"nome": "Tapete Voador", "espaco": "Carga", "preco": "T$ 35.000", "efeito": "Um tapete de 2x3m que flutua transportando até 4 passageiros com deslocamento de voo 18m sem limite de tempo.", "pagina": 351},
        {"nome": "Tiara do Intelecto", "espaco": "Cabeça", "preco": "T$ 16.000", "efeito": "Concede +2 no atributo Inteligência e +2 em testes de Conhecimento, Investigação e Misticismo.", "pagina": 351},
    ]

    # 7. ARTEFATOS LENDÁRIOS (7 Artefatos)
    artefatos = [
        {
            "id": "artefato_holy_avenger",
            "nome": "A Espada-Deus (Holy Avenger)",
            "tipo": "Artefato Maior",
            "descricao_poderes": "A espada sagrada do Deus Maior Khalmyr. Uma espada bastarda magnífica vorpal de energia pura que causa dano de essência massivo, concede imunidade a efeitos malignos e morte ao portador, e permite conjurar milagres supremos da justiça divina.",
            "destruicao": "Só pode ser destruída se a própria justiça cósmica deixar de existir no multiverso ou pelo julgamento unânime dos 20 Deuses Maiores.",
            "pagina": 352,
        },
        {
            "id": "artefato_joia_da_alma",
            "nome": "A Joia da Alma",
            "tipo": "Artefato Maior",
            "descricao_poderes": "Um diamante colossal translúcido que contém a alma e a centelha divina de um antigo Deus Maior. Permite ao usuário absorver almas caídas, restaurar a vida sem perda de níveis e acumular PM infinitos para rituais arcanos.",
            "destruicao": "Só pode ser partida se atingida pelo golpe direto de um Deus Maior em seu reino planar nativo.",
            "pagina": 352,
        },
        {
            "id": "artefato_baralho_do_caos",
            "nome": "O Baralho do Caos",
            "tipo": "Artefato Maior",
            "descricao_poderes": "Criado pelo Deus do Caos Nimb. Um baralho de cartas de marfim encantado. Retirar uma carta pode conceder desejos infinitos, teletransportar para masmorras abissais, matar instantaneamente ou transformar o aventureiro em lorde planar.",
            "destruicao": "Indestrutível por meios mortais; só desaparece quando todas as cartas forem sacadas, ressurgindo em outro canto do multiverso.",
            "pagina": 353,
        },
        {
            "id": "artefato_olho_de_sszzaas",
            "nome": "O Olho de Sszzaas",
            "tipo": "Artefato Maior",
            "descricao_poderes": "A joia esmeralda sagrada do Deus da Traição. Concede onisciência sobre segredos e conspirações mortais, visão verdadeira perpétua e a capacidade de controlar mentes de monarcas e deuses menores.",
            "destruicao": "Só pode ser cegado e dissolvido em uma lágrima sincera de perdão de uma divindade traída.",
            "pagina": 354,
        },
        {
            "id": "artefato_rubis_da_virtude",
            "nome": "Os Rubis da Virtude",
            "tipo": "Artefato Maior",
            "descricao_poderes": "Vinte gemas mágicas ancestrais que guardavam o poder primordial da Deusa da Ambição Valkaria. Cada rubi concede poderes divinos específicos (imunidades, bônus cósmicos em atributos e magias de 5º círculo sem custo em PM). Reunir todos permite ascender ao Panteão.",
            "destruicao": "Só podem ser desfeitos se a ambição dos povos de Arton for completamente extinta.",
            "pagina": 355,
        },
        {
            "id": "artefato_cetro_das_cores",
            "nome": "O Cetro das Cores",
            "tipo": "Artefato Maior",
            "descricao_poderes": "O cetro arcano primordial de Wynna. Permite conjurar qualquer magia de qualquer círculo e de qualquer escola sem gastar PM, além de desviar e dissipar qualquer magia conjurada por oponentes.",
            "destruicao": "Só pode ser quebrado em uma zona de antimagia cósmica absoluta criada no coração do Vazio entre os mundos.",
            "pagina": 355,
        },
        {
            "id": "artefato_cranio_negro",
            "nome": "O Crânio Negro",
            "tipo": "Artefato Maior",
            "descricao_poderes": "O crânio fossilizado de uma divindade morta que emana necromancia absoluta. Comanda legiões inteiras de mortos-vivos, ergue exércitos de esqueletos instantaneamente e drena a vida de regiões inteiras transformando-as em desertos cinzentos.",
            "destruicao": "Deve ser banhado na luz solar do meio-dia no zênite do reino de Azgher por um clérigo de 20º nível.",
            "pagina": 355,
        },
    ]

    recompensas_banco = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (Capítulo 8: Recompensas, págs 330–355)",
        "total_regras_gerais": len(regras_gerais),
        "total_encantos_armas": len(encantos_armas),
        "total_armas_especificas": len(armas_especificas),
        "total_encantos_armaduras": len(encantos_armaduras),
        "total_armaduras_especificas": len(armaduras_especificas),
        "total_acessorios": len(acessorios),
        "total_artefatos": len(artefatos),
        "regras_gerais": regras_gerais,
        "encantos_armas": encantos_armas,
        "armas_especificas": armas_especificas,
        "encantos_armaduras": encantos_armaduras,
        "armaduras_especificas": armaduras_especificas,
        "acessorios": acessorios,
        "artefatos": artefatos,
    }

    OUT.write_text(json.dumps(recompensas_banco, ensure_ascii=False, indent=2), encoding="utf-8")
    return recompensas_banco


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Extraindo Recompensas de {PDF.name}...")
    banco = extrair_dados_recompensas()
    print(f"Sucesso! Dados de Recompensas salvos em {OUT}")
    print(f"• Regras Gerais & Tabelas de Tesouro: {banco['total_regras_gerais']}")
    print(f"• Encantos de Armas: {banco['total_encantos_armas']}")
    print(f"• Armas Específicas: {banco['total_armas_especificas']}")
    print(f"• Encantos de Armaduras/Escudos: {banco['total_encantos_armaduras']}")
    print(f"• Armaduras/Escudos Específicos: {banco['total_armaduras_especificas']}")
    print(f"• Acessórios Mágicos: {banco['total_acessorios']}")
    print(f"• Artefatos Supremos: {banco['total_artefatos']}")


if __name__ == "__main__":
    main()
