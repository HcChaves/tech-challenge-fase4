"""Cria o cliente do LLM (Gemini via LangChain)."""

import os

from dotenv import load_dotenv
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

MODELO_LLM = "gemini-3.6-flash"

# O plano gratuito permite ~5 requisições por minuto por modelo.
# Usamos 4 para ter folga.
REQUISICOES_POR_MINUTO = 4


def criar_llm(
    temperatura: float = 0.0, requisicoes_por_minuto: int = REQUISICOES_POR_MINUTO
) -> ChatGoogleGenerativeAI:
    load_dotenv()
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise RuntimeError("GEMINI_API_KEY não encontrada. Defina-a no arquivo .env")

    limitador = InMemoryRateLimiter(
        requests_per_second=requisicoes_por_minuto / 60,
        check_every_n_seconds=0.5,
        max_bucket_size=1,  # sem rajadas: uma chamada por vez, espaçadas
    )
    return ChatGoogleGenerativeAI(
        model=MODELO_LLM,
        google_api_key=chave,
        temperature=temperatura,
        rate_limiter=limitador,
    )