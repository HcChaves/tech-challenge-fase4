"""Barreiras de ausência de evidências que rodam em código, sem chamar a LLM."""

import re

from langchain_chroma import Chroma

from src.retrieval import processar_pergunta

# Calibrados no notebooks/07_calibracao_sem_evidencia.ipynb.
PISO_SIMILARIDADE = 0.70  # dado os testes, abaixo disso não há evidência na base
MIN_CITADAS = 2           # uma única avaliação é anedota, não evidência de um tema

PADRAO_QUANTITATIVA = re.compile(
    r"\b(quantas|quantos|quantidade|média|percentual|porcentagem|percentagem|proporção)\b",
    re.IGNORECASE,
)


def eh_quantitativa(pergunta: str) -> bool:
    """Detecta pedidos de contagem, média ou percentual (o sistema só recupera exemplos)."""
    return bool(PADRAO_QUANTITATIVA.search(pergunta))


def similaridade_com_a_base(pergunta: str, store: Chroma) -> float | None:
    """
    Similaridade do melhor resultado para a pergunta processada.
    Devolve None se a pergunta não tem nenhuma palavra do vocabulário NILC.
    """
    try:
        melhor = store.similarity_search_with_score(processar_pergunta(pergunta), k=1)
    except ValueError:
        return None
    return 1 - melhor[0][1]