"""
Carregando os vetores de palavras do NILC/USP
"""

import numpy as np
from huggingface_hub import hf_hub_download
from safetensors.numpy import load_file
import pandas as pd

import re
from pathlib import Path
from tqdm import tqdm

REPO_NILC = "nilc-nlp/fasttext-skip-gram-300d"
BASE_PROCESSADA = Path(r"data/processed/base_limpa_final.parquet")
BASE_INDEXAVEL = Path(r"data/processed/reviews_indexed.parquet")
EMBEDDINGS_PATH = Path(r"data/processed/embeddings.npy")

def carregar_nilc(repo_id: str = REPO_NILC) -> tuple[np.ndarray, dict[str,int]]:
    """
    baixa e carrega modelo NILC
    retorna matriz de vetoes
    dicionario de palavras para indices
    """
    caminho_vetores = hf_hub_download(repo_id=repo_id, filename="embeddings.safetensors")
    caminho_vocab = hf_hub_download(repo_id=repo_id, filename="vocab.txt")

    vetores = load_file(caminho_vetores)['embeddings']

    with open(caminho_vocab, encoding='utf-8') as f:
        vocab = [linha.rstrip("\n") for linha in f]

    palavra_para_indice = {palavra: i for i, palavra in enumerate(vocab)}
    return vetores, palavra_para_indice

def tokenizar(texto: str) -> list[str]:
    """
    Normalizando, vocab do NILC é todo minuscul, como no teste em verificando_embeddings.ipynb
    """
    return re.findall(r"\w+", texto.lower())

def vetor_da_frase(texto: str, vetores: np.ndarray, vocab: dict[str, int]) -> np.ndarray | None:
    """
    Média dos vetores das palavras conhecidas + normalização L2.
    Palavras fora do vocabulário são ignoradas.
    Retorna None se nenhuma palavra do texto existir no vocabulário.
    """
    indices = [vocab[t] for t in tokenizar(texto) if t in vocab]
    if not indices:
        return None

    media = vetores[indices].mean(axis=0)
    norma = np.linalg.norm(media)
    if norma == 0:
        return None
    return media / norma

def gerar_embeddings(
    textos: list[str], vetores: np.ndarray, vocab: dict[str, int]
) -> tuple[np.ndarray, np.ndarray]:
    """
    Gera um vetor por texto. Retorna:
      - matriz [n_textos, 300] (linhas inválidas ficam zeradas)
      - máscara booleana indicando quais textos geraram vetor válido
    """
    saida = np.zeros((len(textos), vetores.shape[1]), dtype=np.float32)
    validos = np.zeros(len(textos), dtype=bool)

    for i, texto in enumerate(tqdm(textos, desc="Gerando embeddings")):
        v = vetor_da_frase(texto, vetores, vocab)
        if v is not None:
            saida[i] = v
            validos[i] = True

    return saida, validos

def construir_embeddings() -> None:
    """Gera os embeddings da base limpa e salva base indexável + matriz de vetores."""
    df = pd.read_parquet(BASE_PROCESSADA)
    vetores, vocab = carregar_nilc()

    emb, validos = gerar_embeddings(df["texto"].tolist(), vetores, vocab)

    descartados = df[~validos]
    print(f"\nComentários sem nenhuma palavra no vocabulário (descartados): {len(descartados)}")
    if len(descartados) > 0:
        print(descartados["texto"].head(5).tolist())

    # Mantém df e embeddings alinhados: linha i do parquet <-> linha i da matriz
    df_final = df[validos].reset_index(drop=True)
    emb_final = emb[validos]

    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(BASE_INDEXAVEL, index=False)
    np.save(EMBEDDINGS_PATH, emb_final)

    normas = np.linalg.norm(emb_final, axis=1)
    print(f"\nFormato dos embeddings: {emb_final.shape}")
    print(f"Normas dos vetores (min / max): {normas.min():.4f} / {normas.max():.4f}")
    print(f"Salvos em: {EMBEDDINGS_PATH} e {BASE_INDEXAVEL}")


if __name__ == "__main__":
    construir_embeddings()