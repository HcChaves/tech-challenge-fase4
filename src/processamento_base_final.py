"""
Módulo de processamento de dados para a análise de comentários de avaliações.
Carrega a base olist, aplica limpeza definida no EDA e salvca df final em parquet
"""

import re
from pathlib import Path
import pandas as pd

RAW_PATH = Path(r'data\raw\olist_order_reviews_dataset.csv')
PROCESSED_PATH = Path(r'data\processed\base_limpa_final.parquet')

# Regex usado para detectar se existe ao menos uma letra no texto
# evita comentarios com emojis e simbolos
LETRA_REGEX = re.compile(r'[a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]')

def carregar_base_olist(caminho: Path = RAW_PATH) -> pd.DataFrame:
    """carrega csv bruto do olist reviews"""
    return pd.read_csv(caminho)

def limpar_avaliacoes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica limpeza conforme definido no EDA:

    - Remove registros com review_comment_message nulo
    - Remove registros com review_comment_message vazio ou apenas espaços
    - Remove registros com review_comment_message sem letras (apenas emojis ou simbolos)
    - Remove registros duplicados de review_comment_message (mesma avaliação a order_id diferentes)
    """
    df = df.copy()

    # remove nulos
    df = df[df['review_comment_message'].notnull()]

    # normaliza texto
    df['texto'] = (
        df['review_comment_message']
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()  
    )

    # remove string vazias
    df = df[df['texto'] != '']

    # remove comentarios sem nenhuma letra
    tem_letra = df['texto'].str.contains(LETRA_REGEX, regex=True)
    df = df[tem_letra]

    # deduplicação
    df = df.drop_duplicates(subset='review_id', keep='first')

    return df

def selecionar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define as colunas finais que serão mantidas no dataset.
    """
    colunas = ["review_id", "order_id", "review_score", "review_creation_date", "texto"]
    return df[colunas].reset_index(drop=True)

def executa_pipeline(
    caminho_raw: Path = RAW_PATH, 
    caminho_saida: Path = PROCESSED_PATH,
) -> pd.DataFrame:
    """ Executa todas as funcoes acima e salva df final em parquet """
    df = carregar_base_olist(caminho_raw)
    df = limpar_avaliacoes(df)
    df_final = selecionar_colunas(df)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(caminho_saida, index=False)

    return df_final

# permite rodar o script diretamente para gerar a base final e importar funcoes para outros scripts
if __name__ == "__main__":
    df_final = executa_pipeline()
    print(f"Base final construída: {len(df_final)} avaliações únicas com texto")
    print(f"Salva em: {PROCESSED_PATH}")
    print()
    print(df_final.head())

"""
Base final construída: 40482 avaliações únicas com texto
Salva em: data

                          review_id  ...                                              texto
0  e64fb393e7b32834bb789ff8bb30750e  ...              Recebi bem antes do prazo estipulado.
1  f7c4243c7fe1938f181bec41a392bdeb  ...  Parabéns lojas lannister adorei comprar pela I...
2  8670d52e15e00043ae7de4c01cc2fe06  ...  aparelho eficiente. no site a marca do aparelh...
3  4b49719c8a200003f700d3d986ea1a19  ...        Mas um pouco ,travando...pelo valor ta Boa.
4  3948b09f7c818e2d86c9a546758b2335  ...  Vendedor confiável, produto ok e entrega antes...
"""