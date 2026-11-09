"""Cria o cliente do LLM (Gemini via LangChain), com limitador de taxa e cache em disco."""

import os

from dotenv import load_dotenv
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

from src.cache_llm import CacheEmDisco

# O modelo e o ritmo podem ser trocados no .env, sem mexer no código:
#   GEMINI_MODEL=gemini-3.5-flash-lite
#   GEMINI_RPM=4
MODELO_PADRAO = "gemini-3.5-flash-lite"
REQUISICOES_POR_MINUTO_PADRAO = 4


def criar_llm(temperatura: float = 0.0, usar_cache: bool = True) -> ChatGoogleGenerativeAI:
    load_dotenv()
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise RuntimeError("GEMINI_API_KEY não encontrada. Defina-a no arquivo .env")

    modelo = os.getenv("GEMINI_MODEL", MODELO_PADRAO)
    rpm = float(os.getenv("GEMINI_RPM", REQUISICOES_POR_MINUTO_PADRAO))

    limitador = InMemoryRateLimiter(
        requests_per_second=rpm / 60,
        check_every_n_seconds=0.5,
        max_bucket_size=1,  # uma chamada por vez, espaçadas
    )
    return ChatGoogleGenerativeAI(
        model=modelo,
        google_api_key=chave,
        temperature=temperatura,
        rate_limiter=limitador,
        max_retries=2,  
        cache=CacheEmDisco() if usar_cache else False,
    )


if __name__ == "__main__":
    # Teste rápido: confirma que o modelo existe e que há cota (gasta 1 chamada)
    llm = criar_llm(usar_cache=False)
    print("Modelo:", os.getenv("GEMINI_MODEL", MODELO_PADRAO))
    print("Resposta:", llm.invoke("Responda apenas: ok").content)