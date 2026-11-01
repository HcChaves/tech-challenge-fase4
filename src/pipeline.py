"""Pipeline completo: pergunta -> buscas -> evidências -> contexto -> resposta."""

from collections import Counter
from dataclasses import dataclass

from langchain_chroma import Chroma

from src.context import Contexto, construir_contexto
from src.generation import Resposta, gerar_resposta
from src.retrieval import recuperar_multiconsulta


@dataclass
class Resultado:
    pergunta: str
    consultas: list[str]   # buscas geradas pelo LLM (só para auditoria)
    contexto: Contexto
    resposta: Resposta


def responder(pergunta: str, store: Chroma, llm) -> Resultado:
    consultas, evidencias = recuperar_multiconsulta(store, pergunta, llm)
    contexto = construir_contexto(evidencias)
    resposta = gerar_resposta(pergunta, contexto, llm)
    return Resultado(pergunta, consultas, contexto, resposta)


def _linha_evidencia(id_ev, ev) -> str:
    notas = ", ".join(f"{n}★×{c}" for n, c in sorted(Counter(ev.notas).items()))
    ids = ", ".join(ev.review_ids[:2]) + (f" (+{ev.ocorrencias - 2})" if ev.ocorrencias > 2 else "")
    return f"  [{id_ev}] {ev.ocorrencias}x | {notas} | {ev.texto}\n        review_id: {ids}"


def imprimir_resultado(r: Resultado) -> None:
    res = r.resposta
    print("=" * 110)
    print(f"PERGUNTA: {r.pergunta}")
    print(f"Buscas geradas: {r.consultas}")
    print(f"\nRESPOSTA (tentativas: {res.tentativas}, fundamentada: {res.fundamentada}):")
    print(res.texto)
    if res.citacoes_invalidas:
        print(f"\nCitações inválidas: {res.citacoes_invalidas}")
    print("\nEVIDÊNCIAS CITADAS:")
    for id_ev, ev in res.citadas.items():
        print(_linha_evidencia(id_ev, ev))
    print("\nRECUPERADAS E NÃO CITADAS:")
    for id_ev, ev in res.nao_citadas.items():
        print(f"  [{id_ev}] {ev.texto}")