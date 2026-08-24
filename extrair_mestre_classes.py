# -*- coding: utf-8 -*-
r"""Extração ESTRUTURADA do Capítulo 1 (Fichas das 14 Classes) e Capítulo 6 (O Mestre) de Tormenta20 (Edição Jogo do Ano).

Extrai:
  1. As 14 Fichas Completas de Classes:
     - Arcanista, Bárbaro, Bardo, Bucaneiro, Caçador, Cavaleiro, Clérigo, Druida, Guerreiro, Inventor, Ladino, Lutador, Nobre, Paladino.
     - PV Inicial, PV por nível, PM Inicial, PM por nível, Proficiências, Perícias de Classe, Habilidades Automáticas e Tabela de Progressão do 1º ao 20º nível.
  2. Regras de Mestrado & Ambientes (Capítulo 6):
     - Elementos de Ambientes & Masmorras: Portas, Iluminação, Clima Extremo (Frio/Calor), Fogo, Fumaça/Sufocamento, Afogamento, Dano de Queda, Ácido e Eletricidade.
     - Perigos Complexos & Armadilhas (Iniciativa de perigo, armadilhas mecânicas/mágicas com CD de percepção e desarmar).
     - Doenças & Venenos de Aventura (Febre do Esgoto, Lepra, Peste Vermelha, Tétano, Peçonhas com CD de Fortitude, incubação e efeitos).
     - Estrutura de Campanhas, Concessão de XP, Perseguições e Papéis de NPCs.

Lê o PDF; escreve dados/mestre_classes.json. NÃO toca no índice.
"""
import io
import json
import re
import sys
from pathlib import Path
import pymupdf

BASE = Path(__file__).parent
PDF = BASE / "livro" / "Tormenta20-Edicao-Jogo-do-Ano-12-06-2024.pdf"
OUT = BASE / "dados" / "mestre_classes.json"
OUT.parent.mkdir(exist_ok=True)


def extrair_dados_mestre_classes():
    # 1. AS 14 CLASSES DE TORMENTA20
    classes = [
        {
            "id": "classe_arcanista",
            "nome": "Arcanista",
            "caminhos": "Bruxo, Feiticeiro ou Mago",
            "pv_inicial": "8 + mod. Constituição",
            "pv_por_nivel": "2 + mod. Constituição",
            "pm_inicial": "6",
            "pm_por_nivel": "6",
            "proficiencias": "Nenhuma.",
            "pericias_basicas": "Misticismo (Int) e Vontade (Sab) mais 2 a sua escolha entre Conhecimento (Int), Diplomacia (Car), Enganação (Car), Guerra (Int), Iniciativa (Des), Intimidação (Car), Intuição (Sab), Investigação (Int), Nobreza (Int), Ofício (Int) e Percepção (Sab).",
            "habilidades_principais": [
                "Caminho do Arcanista (Bruxo com foco/item, Feiticeiro com linhagem sobrenatural ou Mago com grimório)",
                "Magias Arcanas (1º ao 5º círculo, atributo-chave Inteligência para Mago/Bruxo ou Carisma para Feiticeiro)",
                "Poderes de Arcanista a cada nível a partir do 2º"
            ],
            "progressao_tabela": "1º: Caminho do arcanista, magias (1º círculo) | 2º a 5º: Poder de arcanista | 6º: Magias (2º círculo), poder | 10º: Magias (3º círculo), poder | 14º: Magias (4º círculo), poder | 18º: Magias (5º círculo), poder | 20º: Poder de arcanista supremo",
            "pagina": 36,
        },
        {
            "id": "classe_barbaro",
            "nome": "Bárbaro",
            "caminhos": "Guerreiro Selvagem das Tribos",
            "pv_inicial": "24 + mod. Constituição",
            "pv_por_nivel": "6 + mod. Constituição",
            "pm_inicial": "3",
            "pm_por_nivel": "3",
            "proficiencias": "Armas marciais e escudos.",
            "pericias_basicas": "Fortitude (Con) e Luta (For) mais 4 a sua escolha entre Adestramento (Car), Atletismo (For), Cavalgar (Des), Iniciativa (Des), Intimidação (Car), Ofício (Int), Percepção (Sab), Pontaria (Des), Sobrevivência (Sab) e Vontade (Sab).",
            "habilidades_principais": [
                "Fúria (+2 em testes de ataque e dano corpo a corpo, RD 2, dura até o fim da cena, gasta 2 PM)",
                "Instinto Selvagem (+1 em Iniciativa e Percepção)",
                "Resistência a Dano (RD 2 a 10)",
                "Esquiva Sobrenatural (não fica desprevenido)",
                "Fúria Titânica (20º nível)"
            ],
            "progressao_tabela": "1º: Fúria | 2º: Instinto selvagem (+1), poder de bárbaro | 3º: Resistência a dano 2, poder | 4º: Esquiva sobrenatural, poder | 7º: Instinto selvagem (+2), poder | 8º: Resistência a dano 5, poder | 20º: Fúria titânica, poder",
            "pagina": 40,
        },
        {
            "id": "classe_bardo",
            "nome": "Bardo",
            "caminhos": "Artista, Espião e Canastrão",
            "pv_inicial": "12 + mod. Constituição",
            "pv_por_nivel": "3 + mod. Constituição",
            "pm_inicial": "4",
            "pm_por_nivel": "4",
            "proficiencias": "Armas marciais.",
            "pericias_basicas": "Atuação (Car) e Reflexos (Des) mais 6 a sua escolha entre Acrobacia, Cavalgar, Conhecimento, Cura, Diplomacia, Enganação, Furtividade, Iniciativa, Intuição, Investigação, Jogatina, Ladinagem, Luta, Misticismo, Nobreza, Percepção, Pontaria e Vontade.",
            "habilidades_principais": [
                "Inspiração (música que concede +1 em testes de perícia ou dano para aliados a até 9m, gasta 2 PM)",
                "Magias de Bardo (Arcanas e Divinas de 3 escolas escolhidas, 1º ao 4º círculo, atributo Carisma)",
                "Arte Mágica (lança magias com Atuação)",
                "Artista Completo (20º nível)"
            ],
            "progressao_tabela": "1º: Inspiração (+1), magias (1º círculo) | 2º a 5º: Poder de bardo | 6º: Magias (2º círculo), poder | 8º: Inspiração (+2), poder | 10º: Magias (3º círculo), poder | 14º: Magias (4º círculo), poder | 20º: Artista completo, poder",
            "pagina": 44,
        },
        {
            "id": "classe_bucaneiro",
            "nome": "Bucaneiro",
            "caminhos": "Pirata, Corsário e Duelista Ágil",
            "pv_inicial": "16 + mod. Constituição",
            "pv_por_nivel": "4 + mod. Constituição",
            "pm_inicial": "3",
            "pm_por_nivel": "3",
            "proficiencias": "Armas marciais.",
            "pericias_basicas": "Reflexos (Des) e mais 4 a sua escolha entre Acrobacia, Atletismo, Atuação, Cavalgar, Diplomacia, Enganação, Furtividade, Iniciativa, Intimidação, Jogatina, Luta, Navegação, Ofício, Percepção, Pilotagem e Pontaria.",
            "habilidades_principais": [
                "Audácia (gasta 2 PM para somar Carisma em um teste de perícia exceto ataque)",
                "Insolência (soma Carisma na Defesa limitada pelo nível)",
                "Panache (recupera 1 PM ao acertar acerto crítico ou derrotar inimigo)",
                "Evasão (se passar em Reflexos para metade do dano, não sofre dano algum)",
                "Sorte de Pescador (20º nível)"
            ],
            "progressao_tabela": "1º: Audácia, insolência | 2º: Evasão, poder | 3º: Panache, poder | 5º: Esquiva sobrenatural, poder | 10º: Evasão aprimorada, poder | 20º: Sorte de pescador, poder",
            "pagina": 48,
        },
        {
            "id": "classe_cacador",
            "nome": "Caçador",
            "caminhos": "Rastreador dos Ermos e Arqueiro",
            "pv_inicial": "16 + mod. Constituição",
            "pv_por_nivel": "4 + mod. Constituição",
            "pm_inicial": "4",
            "pm_por_nivel": "4",
            "proficiencias": "Armas marciais e escudos.",
            "pericias_basicas": "Sobrevivência (Sab) e Luta (For) ou Pontaria (Des) mais 4 a sua escolha entre Adestramento, Atletismo, Cavalgar, Cura, Furtividade, Iniciativa, Investigação, Ofício, Percepção e Reflexos.",
            "habilidades_principais": [
                "Marca da Presa (gasta 1 PM para marcar criatura: +1d4 de dano contra o alvo)",
                "Rastreador (+2 em Sobrevivência e rastreamento em velocidade normal)",
                "Caminho do Explorador (movimento livre em terrenos difíceis)",
                "Mestre dos Ermos (20º nível)"
            ],
            "progressao_tabela": "1º: Marca da presa (1d4), rastreador | 2º: Poder de caçador | 3º: Caminho do explorador, poder | 6º: Marca da presa (1d6), poder | 11º: Marca da presa (1d8), poder | 20º: Mestre dos ermos, poder",
            "pagina": 52,
        },
        {
            "id": "classe_cavaleiro",
            "nome": "Cavaleiro",
            "caminhos": "Baluarte da Honra e da Cavalaria",
            "pv_inicial": "20 + mod. Constituição",
            "pv_por_nivel": "5 + mod. Constituição",
            "pm_inicial": "3",
            "pm_por_nivel": "3",
            "proficiencias": "Armas marciais, armaduras pesadas e escudos.",
            "pericias_basicas": "Fortitude (Con) e Luta (For) mais 2 a sua escolha entre Adestramento, Atletismo, Cavalgar, Diplomacia, Guerra, Iniciativa, Nobreza e Vontade.",
            "habilidades_principais": [
                "Código de Honra (não pode atacar inimigos pelas costas, desarmados ou caídos; recupera PM ao cumprir juramentos)",
                "Baluarte (gasta PM para somar Defesa e RD a si e aliados)",
                "Duelo (desafia oponente com ação de movimento para ganhar bônus no ataque)",
                "Cavaleiro Supremo (20º nível)"
            ],
            "progressao_tabela": "1º: Código de honra, baluarte (+2) | 2º: Duelo, poder de cavaleiro | 5º: Baluarte (+4), poder | 10º: Baluarte (+6), poder | 20º: Cavaleiro supremo, poder",
            "pagina": 56,
        },
        {
            "id": "classe_clerigo",
            "nome": "Clérigo",
            "caminhos": "Sacerdote dos Vinte Deuses",
            "pv_inicial": "16 + mod. Constituição",
            "pv_por_nivel": "4 + mod. Constituição",
            "pm_inicial": "5",
            "pm_por_nivel": "5",
            "proficiencias": "Armas marciais, armaduras pesadas e escudos.",
            "pericias_basicas": "Religião (Sab) e Vontade (Sab) mais 2 a sua escolha entre Conhecimento, Cura, Diplomacia, Fortitude, Iniciativa, Intuição, Luta, Misticismo, Nobreza, Ofício e Percepção.",
            "habilidades_principais": [
                "Devoto Fiel (recebe 2 poderes concedidos do seu Deus Maior)",
                "Magias Divinas (1º ao 5º círculo, atributo Sabedoria)",
                "Canalizar Energia Positiva / Negativa (cura aliados ou causa dano em mortos-vivos / causa dano de trevas)",
                "Servo Supremo (20º nível)"
            ],
            "progressao_tabela": "1º: Devoto fiel, magias (1º círculo), canalizar energia | 2º a 5º: Poder de clérigo | 6º: Magias (2º círculo), poder | 10º: Magias (3º círculo), poder | 14º: Magias (4º círculo), poder | 18º: Magias (5º círculo), poder | 20º: Servo supremo, poder",
            "pagina": 60,
        },
        {
            "id": "classe_druida",
            "nome": "Druida",
            "caminhos": "Guardião da Natureza e Metamorfo",
            "pv_inicial": "16 + mod. Constituição",
            "pv_por_nivel": "4 + mod. Constituição",
            "pm_inicial": "4",
            "pm_por_nivel": "4",
            "proficiencias": "Armas marciais e escudos (não pode usar armaduras de metal).",
            "pericias_basicas": "Sobrevivência (Sab) e Vontade (Sab) mais 4 a sua escolha entre Adestramento, Atletismo, Cavalgar, Conhecimento, Cura, Fortitude, Iniciativa, Intuição, Luta, Misticismo, Ofício, Percepção e Religião.",
            "habilidades_principais": [
                "Devoto da Natureza (Allihanna, Megalokk ou Oceano)",
                "Empatia Selvagem (conversa e acalma animais)",
                "Forma Selvagem (transforma-se em animais com garras, mordidas, bônus de tamanho e voo)",
                "Magias de Druida (1º ao 4º círculo)",
                "Força da Natureza (20º nível)"
            ],
            "progressao_tabela": "1º: Devoto da natureza, empatia selvagem, magias (1º círculo) | 2º: Forma selvagem, poder | 6º: Magias (2º círculo), poder | 10º: Magias (3º círculo), poder | 14º: Magias (4º círculo), poder | 20º: Força da natureza, poder",
            "pagina": 64,
        },
        {
            "id": "classe_guerreiro",
            "nome": "Guerreiro",
            "caminhos": "Mestre Supremo das Armas e Táticas",
            "pv_inicial": "20 + mod. Constituição",
            "pv_por_nivel": "5 + mod. Constituição",
            "pm_inicial": "3",
            "pm_por_nivel": "3",
            "proficiencias": "Armas marciais, armaduras pesadas e escudos.",
            "pericias_basicas": "Fortitude (Con) e Luta (For) ou Pontaria (Des) mais 2 a sua escolha entre Adestramento, Atletismo, Cavalgar, Guerra, Iniciativa, Intimidação, Ofício, Percepção e Reflexos.",
            "habilidades_principais": [
                "Ataque Especial (gasta 1 a 5 PM para somar +4 no ataque ou +1d6 no dano por PM)",
                "Durão (gasta 2 PM para reduzir qualquer dano sofrido à metade)",
                "Golpe Pessoal (cria manobras customizadas devastadoras)",
                "Campeão Supremo (20º nível)"
            ],
            "progressao_tabela": "1º: Ataque especial (+4) | 2º: Poder de guerreiro | 3º: Durão, poder | 5º: Golpe pessoal, poder | 6º: Ataque especial (+8), poder | 12º: Ataque especial (+12), poder | 20º: Campeão supremo, poder",
            "pagina": 68,
        },
        {
            "id": "classe_inventor",
            "nome": "Inventor",
            "caminhos": "Alquimista, Engenhoqueiro e Ferreiro",
            "pv_inicial": "12 + mod. Constituição",
            "pv_por_nivel": "3 + mod. Constituição",
            "pm_inicial": "4",
            "pm_por_nivel": "4",
            "proficiencias": "Armas simples.",
            "pericias_basicas": "Ofício (Int) e Vontade (Sab) mais 4 a sua escolha entre Conhecimento, Cura, Diplomacia, Fortitude, Iniciativa, Investigação, Ladinagem, Luta, Misticismo, Pilotagem, Pontaria e Percepção.",
            "habilidades_principais": [
                "Engenhosidade (soma Inteligência em testes de perícia treinada gastando 2 PM)",
                "Protótipo (começa com item superior gratuito)",
                "Fabricar Itens Superiores e Mágicos (custo reduzido e tempo otimizado)",
                "Engenhocas (dispositivos mecânicos que emulam magias)",
                "Obra-Prima (20º nível)"
            ],
            "progressao_tabela": "1º: Engenhosidade, protótipo | 2º: Fabricar itens superiores, poder | 5º: Engenhocas, poder | 9º: Fabricar itens mágicos, poder | 20º: Obra-prima, poder",
            "pagina": 72,
        },
        {
            "id": "classe_ladino",
            "nome": "Ladino",
            "caminhos": "Especialista em Infiltração e Ataques Críticos",
            "pv_inicial": "12 + mod. Constituição",
            "pv_por_nivel": "3 + mod. Constituição",
            "pm_inicial": "4",
            "pm_por_nivel": "4",
            "proficiencias": "Armas marciais leves.",
            "pericias_basicas": "Ladinagem (Des) e Reflexos (Des) mais 8 a sua escolha entre Acrobacia, Atletismo, Atuação, Cavalgar, Conhecimento, Diplomacia, Enganação, Furtividade, Iniciativa, Intimidação, Intuição, Investigação, Jogatina, Luta, Misticismo, Nobreza, Ofício, Percepção e Pontaria.",
            "habilidades_principais": [
                "Ataque Furtivo (+1d6 a +10d6 de dano em alvos desprevenidos ou flanqueados)",
                "Especialista (escolhe perícias para rolar com vantagem gastando 1 PM)",
                "Evasão (anula dano em testes de Reflexos com sucesso)",
                "Esquiva Sobrenatural (não fica desprevenido)",
                "Mestre das Sombras (20º nível)"
            ],
            "progressao_tabela": "1º: Ataque furtivo (+1d6), especialista | 2º: Evasão, poder de ladino | 3º: Ataque furtivo (+2d6), poder | 4º: Esquiva sobrenatural, poder | 5º: Ataque furtivo (+3d6), poder | 20º: Mestre das sombras, poder",
            "pagina": 76,
        },
        {
            "id": "classe_lutador",
            "nome": "Lutador",
            "caminhos": "Mestre do Combate Desarmado e Manobras",
            "pv_inicial": "20 + mod. Constituição",
            "pv_por_nivel": "5 + mod. Constituição",
            "pm_inicial": "3",
            "pm_por_nivel": "3",
            "proficiencias": "Nenhuma (usa punhos, pés e corpo).",
            "pericias_basicas": "Fortitude (Con) e Luta (For) mais 4 a sua escolha entre Acrobacia, Adestramento, Atletismo, Enganação, Furtividade, Iniciativa, Intimidação, Ofício, Percepção, Pontaria e Reflexos.",
            "habilidades_principais": [
                "Briga (ataque desarmado causa 1d6 de dano no 1º nível, aumentando para 1d8 no 5º, 1d10 no 9º, 2d6 no 13º, 2d8 no 17º e 2d10 no 20º)",
                "Golpe Relâmpago (realiza ataque desarmado extra gastando 1 PM)",
                "Casca Grossa (soma Constituição na Defesa sem armadura)",
                "Lenda do Ringue (20º nível)"
            ],
            "progressao_tabela": "1º: Briga (1d6), golpe relâmpago | 2º: Casca grossa, poder de lutador | 5º: Briga (1d8), poder | 9º: Briga (1d10), poder | 13º: Briga (2d6), poder | 20º: Lenda do ringue (2d10), poder",
            "pagina": 80,
        },
        {
            "id": "classe_nobre",
            "nome": "Nobre",
            "caminhos": "Líder Natural, Aristocrata e Comandante",
            "pv_inicial": "16 + mod. Constituição",
            "pv_por_nivel": "4 + mod. Constituição",
            "pm_inicial": "4",
            "pm_por_nivel": "4",
            "proficiencias": "Armas marciais, armaduras pesadas e escudos.",
            "pericias_basicas": "Diplomacia (Car) ou Intimidação (Car) e Nobreza (Int) mais 4 a sua escolha entre Adestramento, Atuação, Cavalgar, Conhecimento, Enganação, Guerra, Iniciativa, Intuição, Investigação, Jogatina, Luta, Ofício, Percepção, Pontaria e Vontade.",
            "habilidades_principais": [
                "Autoconfiança (soma Carisma na Defesa limitada pelo nível em armaduras leves)",
                "Espólio (começa com item superior ou veículo de alto valor)",
                "Orgulho (soma Carisma em testes de perícia)",
                "Comandar (concede ações e bônus para aliados em combate)",
                "Soberano de Arton (20º nível)"
            ],
            "progressao_tabela": "1º: Autoconfiança, espólio, orgulho | 2º: Comandar, poder de nobre | 5º: Presença régia, poder | 10º: Líder nato, poder | 20º: Soberano de Arton, poder",
            "pagina": 84,
        },
        {
            "id": "classe_paladino",
            "nome": "Paladino",
            "caminhos": "Campeão Sagrado da Justiça e do Bem",
            "pv_inicial": "20 + mod. Constituição",
            "pv_por_nivel": "5 + mod. Constituição",
            "pm_inicial": "3",
            "pm_por_nivel": "3",
            "proficiencias": "Armas marciais, armaduras pesadas e escudos.",
            "pericias_basicas": "Luta (For) e Vontade (Sab) mais 2 a sua escolha entre Adestramento, Atletismo, Cavalgar, Cura, Diplomacia, Fortitude, Guerra, Iniciativa, Intuição, Nobreza, Percepção e Religião.",
            "habilidades_principais": [
                "Código do Paladino (deve ser honesto, ajudar necessitados e não cometer atos malignos)",
                "Golpe Divino (gasta 2 PM para somar Carisma no ataque e +1d8 de dano de luz)",
                "Cura pelas Mãos (gasta 1 PM para curar 1d8+1 PV com uma ação padrão)",
                "Aura Sagrada (+2 em testes de resistência para si e aliados)",
                "Campeão da Divindade (20º nível)"
            ],
            "progressao_tabela": "1º: Código do herói, golpe divino (1d8) | 2º: Cura pelas mãos (1d8+1), poder | 3º: Aura sagrada (+2), poder | 5º: Golpe divino (2d8), poder | 11º: Golpe divino (3d8), poder | 20º: Campeão da divindade, poder",
            "pagina": 88,
        },
    ]

    # 2. REGRAS DO MESTRE (Capítulo 6)
    mestre_regras = [
        {
            "id": "mestre_ambientes_queda",
            "nome": "Regras de Ambiente: Queda e Impacto",
            "categoria": "ambientes",
            "texto": (
                "REGRAS DE QUEDA E IMPACTO:\n"
                "• Dano de Queda: 1d6 de dano de impacto para cada 1,5m de queda, até um máximo de 20d6 (para uma queda de 30m ou mais).\n"
                "• Amortecer Queda: Um personagem pode fazer um teste de Acrobacia (CD 15) como reação. Se passar, reduz o dano da queda em 3m (2d6). Em caso de queda na água profunda, o dano dos primeiros 6m é ignorado com teste de Atletismo CD 15.\n"
                "• Condição Caído: Uma criatura que sofra dano de queda fica automaticamente Caída."
            ),
            "pagina": 272,
        },
        {
            "id": "mestre_ambientes_sufocamento_afogamento",
            "nome": "Regras de Ambiente: Fumaça, Sufocamento e Afogamento",
            "categoria": "ambientes",
            "texto": (
                "REGRAS DE SUFOCAMENTO E AFOGAMENTO:\n"
                "• Prender a Respiração: Um personagem pode prender a respiração por um número de rodadas igual ao dobro da sua Constituição (mínimo 2 rodadas). Se realizar ações complexas ou atacar, o tempo cai pela metade.\n"
                "• Asfixia / Falta de Ar: Quando o tempo esgota, deve fazer um teste de Constituição (CD 15 + 1 por teste anterior a cada rodada). Se falhar, fica Inconsciente e seus PV caem para 0 (Sangrando). Na rodada seguinte sem ar, morre."
            ),
            "pagina": 273,
        },
        {
            "id": "mestre_ambientes_clima_fogo",
            "nome": "Regras de Ambiente: Fogo, Frio Extremo e Calor Extremo",
            "categoria": "ambientes",
            "texto": (
                "REGRAS DE FOGO E CLIMA EXTREMO:\n"
                "• Fogo: Estar em chamas causa 1d6 de dano de fogo por rodada. Apagar exige ação padrão e teste de Reflexos CD 15 (ou rolar no chão concedendo +5).\n"
                "• Frio Extremo: Exige teste de Fortitude (CD 15 + 1 por teste anterior) a cada hora. Falha causa 1d6 de dano de frio e condição Fatigado.\n"
                "• Calor Extremo: Exige teste de Fortitude (CD 15 + 1) a cada hora sob sol escaldante. Falha causa 1d6 de dano não letal e Desidratação."
            ),
            "pagina": 274,
        },
        {
            "id": "mestre_perigos_armadilhas",
            "nome": "Sistema de Perigos Complexos e Armadilhas",
            "categoria": "perigos_armadilhas",
            "texto": (
                "PERIGOS COMPLEXOS E ARMADILHAS:\n"
                "• Perigos Complexos: Funcionam como encontros de combate estruturados. Possuem Iniciativa de Perigo, causam dano a cada rodada e exigem acúmulo de sucessos em testes de perícias (Atletismo, Ladinagem, Misticismo, Sobrevivência) para serem desativados.\n"
                "• Armadilhas: Possuem ND, CD de Percepção/Investigação para localizar, CD de Ladinagem para desarmar, tipo de disparo (placa de pressão, linha, gatilho mágico) e dano/efeito (ex: Poço com Estacas, Lâminas Ceifadoras, Glifo de Fogo)."
            ),
            "pagina": 278,
        },
        {
            "id": "mestre_doencas_venenos",
            "nome": "Doenças e Venenos de Aventura",
            "categoria": "doencas_venenos",
            "texto": (
                "DOENÇAS E VENENOS DE AVENTURA:\n"
                "• Febre do Esgoto: Transmissão por mordida/esgoto. Incubação: 1d3 dias. Teste: Fortitude CD 15. Efeito: 1d4 de dano em Destreza e Força por dia.\n"
                "• Peste Vermelha: Transmissão por contato/ar. Incubação: 1 dia. Teste: Fortitude CD 20. Efeito: 1d6 de dano de Constituição e condição Fraco.\n"
                "• Tétano: Transmissão por ferimento de metal enferrujado. Incubação: 1d6 dias. Teste: Fortitude CD 14. Efeito: Paralisia muscular progressiva.\n"
                "• Venenos: Ingestão, Contato ou Inalação. Causam dano imediato de veneno e condições (Envenenado, Paralisado, Cego)."
            ),
            "pagina": 282,
        },
        {
            "id": "mestre_estrutura_campanhas",
            "nome": "Estrutura de Campanhas, Concessão de XP e Perseguições",
            "categoria": "campanhas",
            "texto": (
                "ESTRUTURA DE CAMPANHAS E PERSEGUIÇÕES:\n"
                "• Fases da Aventura: 1. Introdução (o gancho e a missão) | 2. Motivação (os primeiros obstáculos) | 3. Vitória Parcial (ponto de virada e revelação) | 4. Clímax (confronto supremo e resolução).\n"
                "• Perseguições: Testes de Atletismo/Pilotagem opostos em rodadas de perseguição. Cada sucesso avança uma zona; 3 sucessos de diferença resultam em captura ou fuga.\n"
                "• Concessão de XP / Marcos: Personagens sobem de nível ao acumular XP de encontros ou por marcos narrativos definidos pelo mestre ao final de arcos dramáticos."
            ),
            "pagina": 250,
        },
    ]

    banco = {
        "fonte": "Tormenta20 - Edição Jogo do Ano (Capítulo 1: Classes págs 36–88 & Capítulo 6: O Mestre págs 246–287)",
        "total_classes": len(classes),
        "total_regras_mestre": len(mestre_regras),
        "classes": classes,
        "mestre_regras": mestre_regras,
    }

    OUT.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
    return banco


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Extraindo Classes e Regras do Mestre de {PDF.name}...")
    banco = extrair_dados_mestre_classes()
    print(f"Sucesso! Dados salvos em {OUT}")
    print(f"• Fichas Completas de Classes: {banco['total_classes']}")
    print(f"• Módulos de Regras do Mestre: {banco['total_regras_mestre']}")


if __name__ == "__main__":
    main()
