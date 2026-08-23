# -*- coding: utf-8 -*-
r"""Roda várias perguntas de teste no RAG carregando o modelo UMA vez só."""
from perguntar import carregar, responder

PERGUNTAS = [
    "o que é Tormenta20?",
    "como funciona o modelo de criação de personagem por pontos?",
    "quais os atributos possíveis de um personagem?",
    "me explique sobre a raça anão",
    "como funciona o poder Ataque Especial?",
    "que tipos de equipamento um personagem inicial pode ter?",
    "qual o dano e crítico da adaga?",
    "o que faz a Armadura Completa e quanto custa?",
    "como funciona o Bálsamo Restaurador?",
    "quais são os materiais especiais e o que o Aço-Rubi faz?",
]

if __name__ == "__main__":
    print("Carregando índice e embedder (uma vez)...")
    index, chunks, model, meta = carregar()
    print(f"  {meta['n_chunks']} chunks | {meta['modelo_embed']} | qwen3:8b\n")
    for i, q in enumerate(PERGUNTAS, 1):
        print("\n" + "#" * 72)
        print(f"# PERGUNTA {i}/{len(PERGUNTAS)}: {q}")
        print("#" * 72)
        responder(q, index, chunks, model, meta)
