import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Carrega as variáveis do .env 
load_dotenv()

# Confirma que a chave foi lida (sem imprimir ela inteira, por segurança)
chave = os.getenv("GEMINI_API_KEY")
print(f"Chave carregada: {chave[:6]}... (tamanho: {len(chave)})")

# Instancia o modelo Gemini via LangChain
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=chave)

# Faz uma chamada simples pra validar a conexão
resposta = llm.invoke("Responda em uma frase: o que é RAG?")
print("\nResposta do Gemini:")
print(resposta.content)