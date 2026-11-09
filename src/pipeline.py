"""Pipeline completo, com as barreiras de ausência de evidências."""

from collections import Counter
from dataclasses import dataclass

from langchain_chroma import Chroma

from src.context import Contexto, construir_contexto
from src.generation import Resposta, gerar_resposta, resposta_recusa
from src.guardas import (
    MIN_CITADAS,
    PISO_SIMILARIDADE,
    eh_quantitativa,
    similaridade_com_a_base,
)
from src.mensagens import (
    MENSAGEM_FORA_DOMINIO,
    MENSAGEM_INSUFICIENTE,
    MENSAGEM_INVALIDA,
    MENSAGEM_QUANTITATIVA,
    MENSAGEM_FALHA,
    MENSAGEM_ERRO_LLM
)
from src.retrieval import recuperar_multiconsulta


@dataclass
class Resultado:
    pergunta: str
    consultas: list[str]                 # buscas geradas pelo LLM (só para auditoria)
    contexto: Contexto
    resposta: Resposta
    motivo: str | None                   # None = respondida; senão, por que o sistema recusou
    similaridade_pergunta: float | None  # sinal da Camada 1


def _recusar(pergunta, texto, motivo, similaridade=None) -> Resultado:
    contexto = Contexto(texto="", evidencias={})
    return Resultado(pergunta, [], contexto, resposta_recusa(texto, contexto), motivo, similaridade)


def responder(pergunta: str, store: Chroma, llm) -> Resultado:
    # Camada 0 (código): pedidos de estatística, que o sistema não calcula
    if eh_quantitativa(pergunta):
        return _recusar(pergunta, MENSAGEM_QUANTITATIVA, "quantitativa")

    # Camada 1 (código): a pergunta tem alguma relação com a base?
    sim = similaridade_com_a_base(pergunta, store)
    if sim is None:
        return _recusar(pergunta, MENSAGEM_INVALIDA, "pergunta_invalida")
    if sim < PISO_SIMILARIDADE:
        return _recusar(pergunta, MENSAGEM_FORA_DOMINIO, "fora_do_dominio", sim)

    try:
        consultas, evidencias = recuperar_multiconsulta(store, pergunta, llm)
        contexto = construir_contexto(evidencias)

        # Camada 2 (LLM): regras 7 e 8 do prompt
        resposta = gerar_resposta(pergunta, contexto, llm)
    except Exception as erro:  # cota esgotada, rede, chave inválida...
        print(f"Aviso: falha ao chamar o LLM ({type(erro).__name__}): {str(erro)[:150]}")
        return _recusar(pergunta, MENSAGEM_ERRO_LLM, "erro_llm", sim)

    # Camada 3 (código): mínimo de evidências realmente citadas
    motivo = None
    if not resposta.fundamentada:
        motivo = "falha_fundamentacao"
    elif resposta.texto == MENSAGEM_QUANTITATIVA:
        motivo = "quantitativa"
    elif resposta.sem_evidencia:
        motivo = "sem_evidencia_llm"
    elif len(resposta.citadas) < MIN_CITADAS:
        motivo = "evidencias_insuficientes"
        resposta = resposta_recusa(MENSAGEM_INSUFICIENTE, contexto)

    return Resultado(pergunta, consultas, contexto, resposta, motivo, sim)


def _linha_evidencia(id_ev, ev) -> str:
    notas = ", ".join(f"{n}★×{c}" for n, c in sorted(Counter(ev.notas).items()))
    ids = ", ".join(ev.review_ids[:2]) + (f" (+{ev.ocorrencias - 2})" if ev.ocorrencias > 2 else "")
    return f"  [{id_ev}] {ev.ocorrencias}x | {notas} | {ev.texto}\n        review_id: {ids}"


def imprimir_resultado(r: Resultado) -> None:
    res = r.resposta
    print("=" * 110)
    print(f"PERGUNTA: {r.pergunta}")
    print(f"Motivo da recusa: {r.motivo or '— (respondida)'} | similaridade da pergunta: {r.similaridade_pergunta}")
    if r.consultas:
        print(f"Buscas geradas: {r.consultas}")
    print(f"\nRESPOSTA (tentativas: {res.tentativas}, fundamentada: {res.fundamentada}):")
    print(res.texto)
    if res.citacoes_invalidas:
        print(f"\nCitações inválidas: {res.citacoes_invalidas}")
    if res.citadas:
        print("\nEVIDÊNCIAS CITADAS:")
        for id_ev, ev in res.citadas.items():
            print(_linha_evidencia(id_ev, ev))
    if res.nao_citadas:
        print("\nRECUPERADAS E NÃO CITADAS:")
        for id_ev, ev in res.nao_citadas.items():
            print(f"  [{id_ev}] {ev.texto}")