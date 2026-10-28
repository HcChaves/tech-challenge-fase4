"""Cria o cliente do LLM (Gemini via LangChain)."""

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

MODELO_LLM = "gemini-3.6-flash"


def criar_llm(temperatura: float = 0.0) -> ChatGoogleGenerativeAI:
    load_dotenv()
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise RuntimeError("GEMINI_API_KEY não encontrada. Defina-a no arquivo .env")
    return ChatGoogleGenerativeAI(
        model=MODELO_LLM, google_api_key=chave, temperature=temperatura
    )