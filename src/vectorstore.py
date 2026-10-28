"""
banco vetorial: cria e carrega a coleção Chroma com as avaliações.
Cada registro guarda: id (review_id), vetor, texto original e metadados
de rastreabilidade.
"""

from pathlib import Path

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from tqdm import tqdm

from src.embeddings import BASE_INDEXAVEL, NILCEmbeddings

RAIZ = Path(__file__).resolve().parent.parent
CHROMA_DIR = RAIZ / "data" / "chroma"
COLECAO = "avaliacoes_olist"
TAMANHO_LOTE = 1000


def carregar_colecao(embeddings: Embeddings | None = None) -> Chroma:
    """Abre (ou cria, se não existir) a coleção persistente no disco."""
    embeddings = embeddings or NILCEmbeddings()
    return Chroma(
        collection_name=COLECAO,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_configuration={"hnsw": {"space": "cosine"}},
    )


def construir_colecao() -> Chroma:
    """Indexa as avaliações no Chroma. Não recria se a coleção já existir."""
    store = carregar_colecao()

    if store.get(limit=1)["ids"]:
        print(f"A coleção '{COLECAO}' já existe em {CHROMA_DIR}. Apague a pasta para recriar.")
        return store

    df = pd.read_parquet(BASE_INDEXAVEL)
    textos = df["texto"].tolist()
    ids = df["review_id"].tolist()
    metadatas = [
        {
            "review_id": row.review_id,
            "order_id": row.order_id,
            "review_score": int(row.review_score),
            "review_creation_date": str(row.review_creation_date),
        }
        for row in df.itertuples(index=False)
    ]

    for inicio in tqdm(range(0, len(df), TAMANHO_LOTE), desc="Indexando no Chroma"):
        fim = inicio + TAMANHO_LOTE
        store.add_texts(
            texts=textos[inicio:fim],
            metadatas=metadatas[inicio:fim],
            ids=ids[inicio:fim],
        )

    print(f"Registros no Chroma: {store._collection.count()}")
    return store


if __name__ == "__main__":
    construir_colecao()