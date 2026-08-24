# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Capítulo 9: O Mundo de Arton (págs 364–397) de Tormenta20 (Edição Jogo do Ano).

Extrai:
  - 28 Regiões, Reinos, Grandes Potências, Cidades Lendárias, Ermos e Ilhas de Arton com schema tipado:
    - `id`, `nome`, `tipo_regiao`, `capital`, `regente_lider`, `divindades_principais`, `locais_destaque`, `cultura_sociedade`, `ganchos_aventura`, `pagina`.
  - Linha do Tempo e Marcos Históricos de Arton (Guerras Táuricas, Queda de Valkaria, Guerra Artoniana, Conflagração do Aço).

Lê o PDF; escreve dados/mundo_arton.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
OUT = BASE / "dados" / "mundo_arton.json"
OUT.parent.mkdir(exist_ok=True)


def dehyph(s):
    if not s:
        return ""
    s = re.sub(r"(\w+)[-\xad\u00ad]\s+(\w+)", r"\1\2", s)
    s = re.sub(r"[\xad\u00ad]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extrair_dados_mundo():
    # 28 Regiões e Reinos de Arton estruturados com base no Cap. 9
    regioes = [
        # 1. REINOS CENTRAIS DO REINADO
        {
            "id": "reino_deheon",
            "nome": "Deheon",
            "titulo_descritivo": "O Reino Capital e Coração do Reinado",
            "tipo_regiao": "Reino do Reinado",
            "capital": "Valkaria",
            "regente_lider": "Rainha-Imperatriz Shivara Sharpblade",
            "divindades_principais": ["Valkaria", "Khalmyr", "Tanna-Toh"],
            "locais_destaque": ["Cidade de Valkaria", "Estátua Gigante de Valkaria", "Palácio Imperial", "Labirinto de Valkaria", "Vila do Mar", "Ponte do Rio dos Deuses"],
            "cultura_sociedade": "Centro cosmopolita, cultural e político de Arton. Deheon abriga todas as raças e crenças civilizadas. A capital Valkaria é erguida aos pés e em torno da colossal estátua da Deusa da Ambição, ponto de encontro supremo de aventureiros de todo o mundo.",
            "ganchos_aventura": "Intrigas da corte imperial, conspirações da nobreza de outros reinos, masmorras nos subterrâneos de Valkaria e missões imperiais em nome de Shivara.",
            "pagina": 364,
        },
        {
            "id": "reino_bielefeld",
            "nome": "Bielefeld",
            "titulo_descritivo": "O Reino dos Cavaleiros",
            "tipo_regiao": "Reino do Reinado",
            "capital": "Norm",
            "regente_lider": "Lorde Wolfram e os Grão-Mestres das Ordens de Cavalaria",
            "divindades_principais": ["Khalmyr", "Thyatis", "Lin-Wu"],
            "locais_destaque": ["Cidade de Norm", "Castelo de Bielefeld", "Sede da Ordem da Luz", "Fortaleza da Ordem do Leopardo"],
            "cultura_sociedade": "Sociedade rigidamente estratificada e devotada à cavalaria, honra, justiça e código militar. É a sede da lendária Ordem dos Cavaleiros da Luz, baluarte da defesa do bem em Arton.",
            "ganchos_aventura": "Torneios de cavalaria, códigos de honra em conflito com a realidade das ruas, monstros lendários ameaçando vilarejos feudais e espionagem purista.",
            "pagina": 366,
        },
        {
            "id": "reino_wynlla",
            "nome": "Wynlla",
            "titulo_descritivo": "O Reino da Magia",
            "tipo_regiao": "Reino do Reinado",
            "capital": "Sophand",
            "regente_lider": "Conselho dos Magos e Rainha-Feiticeira",
            "divindades_principais": ["Wynna", "Tanna-Toh"],
            "locais_destaque": ["Cidade de Sophand", "O Lar dos Golens", "Torre Arcana Central", "Ruínas de Vectora Velha"],
            "cultura_sociedade": "A magia permeia cada aspecto do cotidiano, da iluminação pública aos afazeres domésticos operados por golens e construtos arcanos. Conjuradores de todas as linhagens encontram aqui respeito e recursos inigualáveis.",
            "ganchos_aventura": "Golens que despertam com livre-arbítrio, experimentos arcanos fora de controle, anomalias mágicas e disputas de guildas de feiticeiros.",
            "pagina": 368,
        },
        {
            "id": "reino_namalkah",
            "nome": "Namalkah",
            "titulo_descritivo": "O Reino dos Cavalos",
            "tipo_regiao": "Reino do Reinado",
            "capital": "Hippiontar",
            "regente_lider": "Khan das Estepes e Senhores das Tropas",
            "divindades_principais": ["Hippion (Deusa Menor)", "Thyatis", "Allihanna"],
            "locais_destaque": ["Acampamento de Hippiontar", "As Grandes Pradarias de Namalkah", "O Vale dos Potros Sagrados"],
            "cultura_sociedade": "Povo nômade e apaixonado por cavalos e liberdade. Em Namalkah, o cavalo é considerado um irmão sagrado. Os melhores cavaleiros e arqueiros montados de Arton nascem nestas pradarias.",
            "ganchos_aventura": "Ladrões de cavalos sagrados, ataques de predadores monstruosos das estepes, corridas e disputas de clãs nômades.",
            "pagina": 369,
        },
        {
            "id": "reino_ahlen",
            "nome": "Ahlen",
            "titulo_descritivo": "O Reino da Intriga",
            "tipo_regiao": "Reino do Reinado",
            "capital": "Thartann",
            "regente_lider": "Rei Thormy e a Nobreza da Casa Real de Thartann",
            "divindades_principais": ["Hyninn", "Sszzaas", "Valkaria"],
            "locais_destaque": ["Cidade de Thartann", "Castelo dos Espelhos", "Beco dos Venenos", "Subterrâneos de Ahlen"],
            "cultura_sociedade": "Em Ahlen, traição e astúcia não são crimes, mas virtudes políticas. Nada é o que parece: contratos possuem cláusulas ocultas, banquetes nobres contêm taças envenenadas e a inteligência supera a força bruta.",
            "ganchos_aventura": "Conspirações para assassinar lordes, guerras secretas entre guildas de ladrões, resgate de nobres chantageados e roubo de documentos de estado.",
            "pagina": 370,
        },
        {
            "id": "reino_zakharov",
            "nome": "Zakharov",
            "titulo_descritivo": "O Reino das Armas",
            "tipo_regiao": "Reino do Reinado",
            "capital": "Rhond",
            "regente_lider": "Lorde das Forjas e Mestre Supremo dos Armeiros",
            "divindades_principais": ["Arsenal", "Keenn (antigo)", "Khalmyr"],
            "locais_destaque": ["Cidade de Rhond (A Cidade dos Armeiros)", "As Grandes Forjas de Zakharov", "Mina de Aço Negro"],
            "cultura_sociedade": "Famoso em todo o Reinado pela metalurgia incomparável. Todo cidadão de Zakharov carrega uma arma de qualidade superior, e os forjadores do reino guardam segredos arcanos de têmpera e ligas metálicas.",
            "ganchos_aventura": "Roubo de segredos de forja de armas mágicas, sabotagem nas minas de ferro, disputas entre clãs de mestres armeiros e armas amaldiçoadas.",
            "pagina": 371,
        },
        {
            "id": "reino_pondsmania",
            "nome": "Pondsmânia",
            "titulo_descritivo": "O Reino das Fadas",
            "tipo_regiao": "Reino do Reinado",
            "capital": "A Cidade Normal dos Humanos (cenográfica)",
            "regente_lider": "Rainha das Fadas e Nobres Feéricos",
            "divindades_principais": ["Wynna", "Allihanna", "Nimb"],
            "locais_destaque": ["A Floresta das Fadas", "A Cidade Normal dos Humanos", "O Bosque dos Cogumelos Gigantes", "O Lago dos Desejos"],
            "cultura_sociedade": "Uma terra de pura magia, sonho e surrealismo feérico. As leis da física e do bom senso são maleáveis: plantas falam, animais usam roupas e as fadas tentam imitar humanos construindo cidades cenográficas hilárias e perigosas.",
            "ganchos_aventura": "Humanos enfeitiçados que esqueceram quem são, caprichos perigosos de nobres feéricos, contratos mágicos capciosos e portais para o reino de Wynna.",
            "pagina": 372,
        },

        # 2. LUGARES LENDÁRIOS E CIDADES ESPECIAIS
        {
            "id": "local_academia_arcana",
            "nome": "A Academia Arcana",
            "titulo_descritivo": "A Maior Escola de Magia do Multiverso Artoniano",
            "tipo_regiao": "Lugar Lendário",
            "capital": "Câmpus da Academia Arcana",
            "regente_lider": "Mestre Supremo Talude (Mago Máximo de Arton)",
            "divindades_principais": ["Wynna", "Tanna-Toh"],
            "locais_destaque": ["Grande Biblioteca Arcana", "Salão dos Portais Planares", "Torre Elemental de Talude", "Jardim das Quimeras"],
            "cultura_sociedade": "Localizada em um semiplano acessível por portais mágicos em várias capitais de Arton. Reúne os estudantes e pesquisadores de magia mais brilhantes do mundo, onde magias de 5º círculo são estudadas e segredos planares são desvendados.",
            "ganchos_aventura": "Fuga de criaturas planares convocadas em laboratório, artefatos corrompidos na biblioteca proibida, duelo de arquimagos e invasão de agentes puristas.",
            "pagina": 373,
        },
        {
            "id": "local_vectora",
            "nome": "Vectora",
            "titulo_descritivo": "O Mercado nas Nuvens (A Cidade Voadora)",
            "tipo_regiao": "Lugar Lendário",
            "capital": "Vectora",
            "regente_lider": "Lorde Vectorius (O Arquimago Inovador)",
            "divindades_principais": ["Valkaria", "Wynna", "Tibhar (antigo)"],
            "locais_destaque": ["Palácio Flutuante de Vectorius", "O Grande Bazar das Nuvens", "Doca dos Balões e Pégasos", "Praça das Guildas Mercantis"],
            "cultura_sociedade": "Uma montanha invertida que flutua pelos céus de Arton movida por magia monumental. É o maior entreposto comercial do mundo: tudo o que existe para ser comprado, vendido ou trocado pode ser encontrado em Vectora.",
            "ganchos_aventura": "Ataques de piratas aéreos e monstros voadores, sabotagem nas pedras de levitação de Vectorius, leilões clandestinos de itens proibidos e crimes nas docas.",
            "pagina": 374,
        },

        # 3. GRANDES POTÊNCIAS BELIGERANTES
        {
            "id": "reino_supremacia_purista",
            "nome": "A Supremacia Purista",
            "titulo_descritivo": "A Nação Militarista Humana e a Conflagração do Aço",
            "tipo_regiao": "Grande Potência",
            "capital": "Kannilar (antiga capital de Yuden)",
            "regente_lider": "General Herman Von Krauser e o Conselho de Generais",
            "divindades_principais": ["Arsenal", "Tanna-Toh (distorcida)", "Aharadak (cultos heréticos secretos)"],
            "locais_destaque": ["Fortaleza de Kannilar", "Campos de Trabalho de Yuden", "As Fábricas de Guerra", "Fronteira da Conflagração do Aço"],
            "cultura_sociedade": "Formada pela união de Yuden e Portsmouth. Uma sociedade fanática, hiper-militarizada e abertamente supremacista humana. Acredita que apenas a raça humana deve herdar Arton, escravizando ou exterminando elfos, anões, goblins e demais povos.",
            "ganchos_aventura": "Missões de infiltração atrás das linhas inimigas, resgate de prisioneiros não-humanos em campos de concentração, sabotagem de colossos de guerra puristas e espionagem militar.",
            "pagina": 376,
        },
        {
            "id": "reino_imperio_tauron",
            "nome": "O Império de Tauron",
            "titulo_descritivo": "O Antigo Império de Tapista e a Terra dos Minotauros",
            "tipo_regiao": "Grande Potência",
            "capital": "Tiberus (em reconstrução pós-queda) e Nova Malpetrim",
            "regente_lider": "Senado dos Minotauros e Legiões Provinciais",
            "divindades_principais": ["Tauron (Deus Maior falecido)", "Arsenal", "Khalmyr"],
            "locais_destaque": ["Ruínas de Tiberus", "Nova Malpetrim", "Coliseu Imperial", "Fortalezas Legionárias de Tapista"],
            "cultura_sociedade": "Após a queda do Deus Maior Tauron e a destruição de Tiberus, o império dos minotauros passa por uma profunda crise existencial e política. A antiga lei da força e escravidão está sendo contestada por rebeliões e reformas.",
            "ganchos_aventura": "Revoltas de gladiadores e escravos libertos, confrontos de legiões rebeldes, monstros do Ermo atacando cidades desprotegidas e busca por relíquias de Tauron.",
            "pagina": 382,
        },
        {
            "id": "reino_duyshidakk_lamnor",
            "nome": "Continente Bestial (Lamnor & Duyshidakk)",
            "titulo_descritivo": "O Sul Selvagem e o Império da Aliança Negra",
            "tipo_regiao": "Grande Potência",
            "capital": "Urkk'thran (A Capital Duyshidakk) e Rarnaakk",
            "regente_lider": "Thwor Ironfist (Deus Maior e Libertador Duyshidakk)",
            "divindades_principais": ["Thwor", "Megalokk", "Ragnar (antigo)"],
            "locais_destaque": ["Urkk'thran", "Ruínas de Lenórienn", "Fortaleza Conquistada", "Garganta de Rarnaakk"],
            "cultura_sociedade": "O continente sul de Arton, dominado pela civilização Duyshidakk (goblins, hobgoblins, orcs e bugbears unidos sob a fé de Thwor). Uma sociedade marcial, pragmática e meritocrática que desafia a supremacia dos reinos do norte.",
            "ganchos_aventura": "Expedições ao continente sul, diplomacia tensa com os embaixadores de Thwor, exploração de templos e masmorras élficas esquecidas em Lenórienn.",
            "pagina": 392,
        },

        # 4. ALÉM DO REINADO & FRONTEIRAS
        {
            "id": "reino_dos_mortos",
            "nome": "O Reino dos Mortos",
            "titulo_descritivo": "A Terra Maldita de Aslynn e os Mortos-Vivos",
            "tipo_regiao": "Além do Reinado",
            "capital": "Necrópole de Aslynn",
            "regente_lider": "Lorde Vampiro e Altos Sacerdotes Necromantes",
            "divindades_principais": ["Tenebra", "Aharadak", "Ragnar (antigo)"],
            "locais_destaque": ["Necrópole de Aslynn", "A Cidadela dos Ossos", "O Rio de Sangue", "As Catacumbas Esquecidas"],
            "cultura_sociedade": "Região amaldiçoada onde os mortos não descansam. Zumbis, esqueletos, aparições e vampiros governam sobre aldeões aterrorizados. A necromancia é a lei suprema e a luz do sol é fraca e cinzenta.",
            "ganchos_aventura": "Libertação de almas aprisionadas, caça a lordes vampiros, destruição de obeliscos de energia negativa e sobrevivência em território hostil.",
            "pagina": 377,
        },
        {
            "id": "reino_samburdia",
            "nome": "Repúblicas Livres de Sambúrdia",
            "titulo_descritivo": "O Celeiro de Arton e as Terras Férteis",
            "tipo_regiao": "Além do Reinado",
            "capital": "Curavel",
            "regente_lider": "Conselho dos Agricultores e Mestres Druidas",
            "divindades_principais": ["Allihanna", "Lena", "Marah"],
            "locais_destaque": ["Cidade de Curavel", "Os Grandes Campos de Trigo", "Floresta de Sambúrdia", "Moinhos Sagrados de Lena"],
            "cultura_sociedade": "Terras verdejantes e incrivelmente férteis que alimentam grande parte dos reinos de Arton. Uma confederação de cidades pacíficas protegidas por druidas e patrulheiros da natureza.",
            "ganchos_aventura": "Ataques de monstros saídos das matas profundas, pragas mágicas na colheita, ganância de comerciantes puristas e proteção a santuários de cura de Lena.",
            "pagina": 377,
        },
        {
            "id": "reino_trebuck",
            "nome": "Os Feudos de Trebuck",
            "titulo_descritivo": "A Fronteira Devastada e os Cavaleiros da Resistência",
            "tipo_regiao": "Além do Reinado",
            "capital": "Forte Trebuck",
            "regente_lider": "Lorde Barão de Trebuck e Nobres Empobrecidos",
            "divindades_principais": ["Khalmyr", "Thyatis", "Valkaria"],
            "locais_destaque": ["Forte Trebuck", "A Linha de Trincheiras Rubras", "Vilas Queimadas de Trebuck"],
            "cultura_sociedade": "Reino que esteve na linha de frente contra a maior Área de Tormenta do Reinado. Apesar da devastação e da pobreza extrema, seu povo e cavaleiros exibem uma resiliência e bravura inquebrantáveis.",
            "ganchos_aventura": "Incursões contra lefeu desgarrados, recuperação de feudos invadidos por cultistas da Tormenta, resgate de refugiados e reconstrução de fortalezas.",
            "pagina": 378,
        },
        {
            "id": "reino_sckharshantallas",
            "nome": "Sckharshantallas",
            "titulo_descritivo": "O Reino do Dragão Vermelho",
            "tipo_regiao": "Além do Reinado",
            "capital": "Ghardur",
            "regente_lider": "Sckhar (O Rei Dragão Vermelho de Arton)",
            "divindades_principais": ["Kallyadranoch", "Sckhar (culto pessoal)"],
            "locais_destaque": ["Cidade de Ghardur", "O Vulcão de Sckhar", "O Palácio do Tesouro Draconiano", "Ninhos das Serpes"],
            "cultura_sociedade": "Uma monarquia draconiana absolutista onde o próprio monarca é um dragão ancião supremo. A ordem é mantida à base do medo e da lei implacável do fogo, mas a criminalidade comum é quase inexistente.",
            "ganchos_aventura": "Missões diplomáticas perigosas com o Rei Dragão, caçadores de tesouros tentando roubar o vulcão, dragões rebeldes e intrigas de sacerdotes de Kallyadranoch.",
            "pagina": 378,
        },
        {
            "id": "reino_salistick",
            "nome": "Salistick",
            "titulo_descritivo": "O Reino Sem Deuses e a Terra da Medicina",
            "tipo_regiao": "Além do Reinado",
            "capital": "Yudenil",
            "regente_lider": "Conselho dos Médicos Supremos e Reitores",
            "divindades_principais": ["Nenhuma (religião e magia divina são desestimuladas)"],
            "locais_destaque": ["O Hospital Geral de Salistick", "Academia de Medicina e Anatomia", "Jardins Botânicos Alquímicos"],
            "cultura_sociedade": "Única nação de Arton que rejeita a dependência dos Deuses. Em vez de orações e milagres divinos, Salistick desenvolveu a ciência médica, a cirurgia, a farmacologia e a higiene avançada. É o refúgio dos livre-pensadores.",
            "ganchos_aventura": "Investigação de epidemias biológicas raras, conflito com fanáticos religiosos de outros reinos, roubo de compostos curativos lendários e cirurgias de alto risco.",
            "pagina": 386,
        },
        {
            "id": "reino_svalas",
            "nome": "Svalas",
            "titulo_descritivo": "As Florestas Selvagens e as Catacumbas de Leverick",
            "tipo_regiao": "Além do Reinado",
            "capital": "Leverick",
            "regente_lider": "Lordes Silvestres e Chefes de Guilda",
            "divindades_principais": ["Hyninn", "Allihanna", "Nimb"],
            "locais_destaque": ["As Catacumbas de Leverick", "As Matas Fechadas de Svalas", "Ruínas dos Primeiros Povos"],
            "cultura_sociedade": "Região rústica e repleta de florestas antigas. Famosa pelas lendárias Catacumbas de Leverick, uma imensa rede subterrânea cheia de tesouros, ladrões e armadilhas mortais.",
            "ganchos_aventura": "Exploração de masmorras nas Catacumbas de Leverick, perseguição a bandidos foragidos e descoberta de relíquias dos povos antigos.",
            "pagina": 387,
        },
        {
            "id": "reino_doherimm",
            "nome": "Doherimm",
            "titulo_descritivo": "O Reino Subterrâneo dos Anões",
            "tipo_regiao": "Além do Reinado",
            "capital": "Doher-Am-Ghar",
            "regente_lider": "Rei dos Anões e o Conselho dos Clãs da Pedra",
            "divindades_principais": ["Khalmyr", "Tenebra"],
            "locais_destaque": ["Monte Paladon", "Os Grandes Salões de Pedra", "As Profundezas de Doherimm", "A Fenda dos Finntroll"],
            "cultura_sociedade": "Um império subterrâneo colossal sob as Montanhas Sanguinárias. Os anões esculpiram cidades inteiras na rocha viva, com forjas vulcânicas, pontes sobre abismos e exércitos formidáveis.",
            "ganchos_aventura": "Guerra nas profundezas contra os finntrolls, descoberta de veios de aço-rubi nas entranhas da terra e resgate de anões aprisionados.",
            "pagina": 388,
        },
        {
            "id": "reino_lenorienn",
            "nome": "Lenórienn (A Tragédia Élfica)",
            "titulo_descritivo": "As Ruínas do Antigo Reino dos Elfos",
            "tipo_regiao": "Além do Reinado",
            "capital": "Lenórienn (em ruínas)",
            "regente_lider": "Nenhum (território em ruínas dominado pela Aliança Negra)",
            "divindades_principais": ["Glórienn (Deusa caída)", "Valkaria", "Allihanna"],
            "locais_destaque": ["As Torres de Cristal Quebradas", "O Bosque das Lágrimas", "Templo Caído de Glórienn"],
            "cultura_sociedade": "A antiga joia da civilização élfica no continente sul, devastada durante a Guerra Infinita contra a Aliança Negra de Thwor Ironfist. Hoje os elfos são um povo disperso e sem lar.",
            "ganchos_aventura": "Expedições arriscadas para recuperar tomos de magia élfica antiga, lágrimas de cristal mágicas e memória dos antepassados.",
            "pagina": 389,
        },

        # 5. ERMOS, MONTANHAS, MARES E ILHAS
        {
            "id": "regiao_sanguinarias",
            "nome": "As Montanhas Sanguinárias",
            "titulo_descritivo": "A Maior Cordilheira e Fronteira Natural de Arton",
            "tipo_regiao": "Ermos e Montanhas",
            "capital": "Nenhuma (acampamentos bárbaros e postos de fronteira)",
            "regente_lider": "Chefes de Tribos Bárbaras e Senhores de Clã",
            "divindades_principais": ["Megalokk", "Arsenal", "Allihanna"],
            "locais_destaque": ["Pico da Morte", "Garganta do Dragão", "Passagens Altas das Sanguinárias"],
            "cultura_sociedade": "Cordilheira colossal e traiçoeira que divide o norte e o sul de Arton. Habitada por monstros gigantescos, dragões selvagens, wyverns e tribos bárbaras duras como a rocha.",
            "ganchos_aventura": "Cruzada perigosa pelas passagens montanhosas, caça a monstros épicos, emboscadas de bandidos das montanhas e avalanche de neve mágica.",
            "pagina": 379,
        },
        {
            "id": "regiao_uivantes",
            "nome": "As Montanhas Uivantes",
            "titulo_descritivo": "O Reino do Gelo Eterno e o Frio Polar",
            "tipo_regiao": "Ermos e Montanhas",
            "capital": "Beluhv (Acampamentos Uivantes)",
            "regente_lider": "A Rainha do Gelo e Chefes dos Gigantes do Gelo",
            "divindades_principais": ["Beluhv (Deus Menor do Frio)", "Megalokk", "Khalmyr"],
            "locais_destaque": ["Geleira do Gelo Eterno", "Cavernas dos Gigantes de Gelo", "O Abismo Congelado"],
            "cultura_sociedade": "Extremo norte congelado de Arton, onde tempestades de neve perpétuas rugem como uivos de feras. É a única fonte de Gelo Eterno no mundo.",
            "ganchos_aventura": "Expedições para minerar Gelo Eterno, sobrevivência contra temperaturas mortais, confronto com gigantes do gelo e dragões brancos.",
            "pagina": 380,
        },
        {
            "id": "regiao_ermos_purpuras",
            "nome": "Ermos Púrpuras & Deserto da Perdição",
            "titulo_descritivo": "As Areias Mutantes e a Terra da Tormenta Antiga",
            "tipo_regiao": "Ermos e Montanhas",
            "capital": "Nenhuma",
            "regente_lider": "Nenhum (território anárquico selvagem)",
            "divindades_principais": ["Aharadak", "Azgher", "Megalokk"],
            "locais_destaque": ["As Dunas Mutantes", "Oásis Amaldiçoado", "Cratera Rubra"],
            "cultura_sociedade": "Deserto inóspito atingido no passado por uma Área de Tormenta. A areia ganhou tons arroxeados e criaturas aberrantes rondam sob tempestades de calor sobrenatural.",
            "ganchos_aventura": "Busca por minerais mutagênicos raros, resgate de caravanas perdidas no deserto e batalha contra aberrações da areia.",
            "pagina": 381,
        },
        {
            "id": "local_smokestone",
            "nome": "O Covil dos Pistoleiros (Smokestone)",
            "titulo_descritivo": "A Cidade Sem Lei da Pólvora e dos Duelos",
            "tipo_regiao": "Ermos e Montanhas",
            "capital": "Smokestone",
            "regente_lider": "O Xerife e os Barões da Pólvora",
            "divindades_principais": ["Valkaria", "Hyninn", "Arsenal"],
            "locais_destaque": ["Saloon Central de Smokestone", "Rua do Duelo ao Meio-Dia", "Fábrica de Balas e Pólvora Negra"],
            "cultura_sociedade": "Uma cidade de fronteira rústica e poeirenta onde as leis são escritas com chumbo e fumaça de pólvora. É o berço dos pistoleiros de Arton.",
            "ganchos_aventura": "Duelos mortais na rua principal, caça a criminosos com recompensa pela cabeça, roubo de carregamentos de pólvora e defesa da cidade contra bandos selvagens.",
            "pagina": 384,
        },
        {
            "id": "regiao_tyrondir",
            "nome": "As Ruínas de Tyrondir",
            "titulo_descritivo": "A Terra Conquistada e a Ossada de Ragnar",
            "tipo_regiao": "Ermos e Montanhas",
            "capital": "Cidade dos Observatórios (em ruínas)",
            "regente_lider": "Senhores da Guerra Goblinoides",
            "divindades_principais": ["Thwor", "Ragnar (falecido)"],
            "locais_destaque": ["A Ossada Monumental de Ragnar", "Cidade dos Observatórios", "A Muralha de Tyrondir"],
            "cultura_sociedade": "Reino humano fronteiriço do sul totalmente arrasado pela marcha inicial da Aliança Negra. Hoje é um cemitério monumental de batalhas históricas.",
            "ganchos_aventura": "Exploração de templos caídos de Ragnar, batalha contra mortos-vivos da guerra e busca por armas lendárias perdidas no campo de batalha.",
            "pagina": 384,
        },
        {
            "id": "regiao_tres_mares_khubar",
            "nome": "Os Três Mares & Khubar",
            "titulo_descritivo": "O Arquipélago Pirata e as Águas de Arton",
            "tipo_regiao": "Ilhas e Mares",
            "capital": "Khubar",
            "regente_lider": "Príncipe de Khubar e Reis dos Piratas",
            "divindades_principais": ["Oceano", "Valkaria"],
            "locais_destaque": ["Porto de Khubar", "Ilha dos Monstros Marinhos", "O Triângulo das Serpentes"],
            "cultura_sociedade": "As águas que cercam Arton abrigam marinheiros intrépidos, bucaneiros, contrabandistas e povos submarinos. Khubar é a principal cidade insular do arquipélago.",
            "ganchos_aventura": "Combates navais contra frotas piratas, caça a leviatãs e monstros marinhos, busca por tesouros em ilhas misteriosas e naufrágios.",
            "pagina": 390,
        },
        {
            "id": "regiao_galrasia",
            "nome": "O Mundo Perdido (Galrasia)",
            "titulo_descritivo": "A Ilha Primordial dos Dinossauros",
            "tipo_regiao": "Ilhas e Mares",
            "capital": "Nenhuma (aldeias de elfos do céu e povos nativos)",
            "regente_lider": "Megalokk e Allihanna (governo da própria natureza)",
            "divindades_principais": ["Allihanna", "Megalokk"],
            "locais_destaque": ["O Vulcão Primordial", "O Ninho dos Tiranossauros", "Floresta dos Gigantes Pré-Históricos"],
            "cultura_sociedade": "Uma ilha isolada no mar onde o tempo parece não ter passado. Dinossauros colossais, plantas carnívoras e criaturas da era da criação dominam a selva impenetrável.",
            "ganchos_aventura": "Expedições científicas e de caça a dinossauros, resgate de exploradores náufragos e busca por flores de cura lendárias.",
            "pagina": 391,
        },
        {
            "id": "regiao_tamu_ra",
            "nome": "O Império de Jade (Tamu-ra)",
            "titulo_descritivo": "A Terra da Honra e o Renascimento Oriental",
            "tipo_regiao": "Ilhas e Mares",
            "capital": "Nivanal (Nova Nitamu-ra)",
            "regente_lider": "Imperador de Tamu-ra e o Shogunato",
            "divindades_principais": ["Lin-Wu", "Família Celestial"],
            "locais_destaque": ["Cidade de Nivanal", "Montanha do Dragão Celeste", "Monastérios dos Samurais e Kenshis"],
            "cultura_sociedade": "Ilha oriental totalmente destruída pela Tormenta no passado e purificada por heróis lendários. Seu povo valoriza a honra, o dever, a tradição samurai e a lealdade absoluta a Lin-Wu.",
            "ganchos_aventura": "Conflitos entre clãs de samurais e ninjas, purificação de bolsões de corrupção remanescente e defesa da ilha contra piratas.",
            "pagina": 394,
        },
        {
            "id": "regiao_moreania",
            "nome": "Moreania (As Ilhas dos Moreau)",
            "titulo_descritivo": "A Terra dos Doze Animais Sagrados",
            "tipo_regiao": "Ilhas e Mares",
            "capital": "Lariara",
            "regente_lider": "Reis das Castas e Conselho dos Moreau",
            "divindades_principais": ["Os Deuses Herdeiros (Os Doze Animais)"],
            "locais_destaque": ["Cidade de Lariara", "Santuário dos Doze Herdeiros", "As Três Ilhas de Moreania"],
            "cultura_sociedade": "Arquipélago distante habitado pelo povo moreau (humanos com traços animais sagrados: leão, lobo, coruja, serpente, touro, urso, etc.). Uma sociedade rica em espiritualidade e respeito aos ancestrais.",
            "ganchos_aventura": "Intrigas entre as doze castas animais, conspirações de cultistas sombrios e navegação entre as ilhas sagradas.",
            "pagina": 395,
        },
        {
            "id": "regiao_a_tormenta",
            "nome": "A Tormenta & Áreas de Tormenta",
            "titulo_descritivo": "A Tempestade Rubra Alienígena e a Corrupção da Realidade",
            "tipo_regiao": "Ameaça Global",
            "capital": "Corações da Tormenta (Gashk'allan e áreas ativas)",
            "regente_lider": "Aharadak (Deus Maior da Tormenta) e os Lordes da Tormenta (Lefeu)",
            "divindades_principais": ["Aharadak"],
            "locais_destaque": ["Área de Tormenta de Trebuck (purificada/cicatriz)", "Área de Tormenta de Zakharov", "O Olho Rubro"],
            "cultura_sociedade": "Uma realidade aberrante e demoníaca invasora vinda de fora do multiverso artoniano. Sob a chuva de sangue e céu vermelho, a matéria é distorcida, monstros lefeu nascem e a própria sanidade é consumida.",
            "ganchos_aventura": "Incursões suicidas ao interior de Áreas de Tormenta para destruir o Coração da tempestade, resgate de matéria vermelha e combate a cultistas da loucura.",
            "pagina": 396,
        },
    ]

    # Linha do Tempo de Arton
    linha_do_tempo = [
        {"ano": "0", "evento": "A Grande Batalha e Fundação do Reinado de Arton por refugiados de Lamnor liderados por Deheon."},
        {"ano": "1300+", "evento": "A Guerra Infinita no sul: A Aliança Negra de Thwor Ironfist invade e destrói o reino élfico de Lenórienn."},
        {"ano": "1400", "evento": "A Primeira Invasão da Tormenta em Tamu-ra e o massacre do povo tamuraniano."},
        {"ano": "1405", "evento": "A Libertação de Valkaria: Um grupo de aventureiros derrota o Labirinto e liberta a Deusa da Ambição."},
        {"ano": "1410", "evento": "As Guerras Táuricas: O Império de Tauron invade o Reinado e conquista metade dos reinos do norte."},
        {"ano": "1414", "evento": "A Guerra Artoniana e a Queda de Tauron. A ascensão de Thwor e Aharadak ao Panteão Maior."},
        {"ano": "1420 (Atual)", "evento": "A Conflagração do Aço: A Supremacia Purista entra em guerra contra o Reinado e alianças de Arton."},
    ]

    mundo_banco = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (Capítulo 9: O Mundo de Arton, págs 364–397)",
        "total_regioes": len(regioes),
        "total_marcos_historicos": len(linha_do_tempo),
        "regioes": regioes,
        "linha_do_tempo": linha_do_tempo,
    }

    OUT.write_text(json.dumps(mundo_banco, ensure_ascii=False, indent=2), encoding="utf-8")
    return mundo_banco


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Extraindo O Mundo de Arton de {PDF.name}...")
    banco = extrair_dados_mundo()
    print(f"Sucesso! Dados do Mundo de Arton salvos em {OUT}")
    print(f"• Regiões/Reinos extraídos: {banco['total_regioes']}")
    print(f"• Marcos Históricos: {banco['total_marcos_historicos']}")


if __name__ == "__main__":
    main()
