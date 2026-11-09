"""
Interface em terminal: pergunte e veja a resposta com as evidências.

Uso:
    python -m src.cli              # modo interativo
    python -m src.cli --detalhes   # mostra também as buscas geradas e as evidências não citadas
Digite 'sair' para encerrar.
"""

import argparse
from collections import Counter

from src.embeddings import NILCEmbeddings
from src.llm import criar_llm
from src.pipeline import Resultado, responder
from src.vectorstore import carregar_colecao


def _notas(notas: list[int]) -> str:
    return ", ".join(f"nota {n} (x{c})" for n, c in sorted(Counter(notas).items()))


def _mostrar(r: Resultado, detalhes: bool) -> None:
    res = r.resposta
    print()
    if r.motivo:
        print(f"[sem resposta | motivo: {r.motivo}]")
    print(res.texto)

    if res.citadas:
        print("\nEvidências citadas:")
        for id_ev, ev in res.citadas.items():
            print(f"  [{id_ev}] {ev.ocorrencias} avaliação(ões) | {_notas(ev.notas)}")
            print(f"        {ev.texto}")
            print(f"        review_id: {', '.join(ev.review_ids[:3])}")

    if detalhes:
        if r.similaridade_pergunta is not None:
            print(f"\nSimilaridade da pergunta com a base: {r.similaridade_pergunta:.3f}")
        if r.consultas:
            print("\nBuscas geradas pelo LLM:")
            for c in r.consultas:
                print(f"  - {c}")
        if res.nao_citadas:
            print("\nRecuperadas e não citadas:")
            for id_ev, ev in res.nao_citadas.items():
                print(f"  [{id_ev}] {ev.texto}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Voice of Customer Intelligence com RAG")
    parser.add_argument("--detalhes", action="store_true",
                        help="mostra buscas geradas e evidências não citadas")
    args = parser.parse_args()

    print("Carregando modelo de embeddings e banco vetorial...")
    store = carregar_colecao(NILCEmbeddings())
    llm = criar_llm()
    print("Pronto. Digite sua pergunta (ou 'sair').")

    while True:
        try:
            pergunta = input("\nPergunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if pergunta.lower() in {"sair", "exit", "quit"}:
            break
        if not pergunta:
            continue
        _mostrar(responder(pergunta, store, llm), args.detalhes)


if __name__ == "__main__":
    main()