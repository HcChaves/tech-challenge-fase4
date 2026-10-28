"""
processa a pergunta, busca no Chroma e devolve
evidências agrupadas (textos equivalentes viram uma só, com contagem).
Inclui a busca simples e a busca com reescrita da pergunta pelo LLM (multi-query).
"""

import re
from collections import Counter
from dataclasses import dataclass, field

from langchain_chroma import Chroma

from src.embeddings import tokenizar

CANDIDATOS = 50
TOP_EVIDENCIAS = 10
CANDIDATOS_POR_CONSULTA = 20
MAX_CONSULTAS = 6

# Palavras de pergunta e funcionais que não ajudam a busca.
# ATENÇÃO: "não", "sem", "nunca", "nenhum" ficam de fora da lista de propósito,
# porque a negação muda o sentido de uma reclamação.
PALAVRAS_IGNORADAS = {
    "quais", "qual", "quem", "quando", "onde", "como", "que", "porque",
    "são", "é", "foi", "foram", "ser", "está", "estão", "existem", "existe",
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "pelo", "pela", "pelos", "pelas", "por", "para", "com", "e", "ou", "ao", "aos",
}

PROMPT_REESCRITA = """Você ajuda a buscar avaliações de clientes de um e-commerce brasileiro.
As avaliações são comentários curtos, em português informal.

Dada uma PERGUNTA, escreva de 4 a 6 frases curtas de busca (3 a 8 palavras cada), \
no estilo de um comentário real de cliente, cada uma cobrindo um tema DIFERENTE relacionado à pergunta.

Regras:
- Se a pergunta for sobre problemas ou reclamações, use frases com sentido negativo explícito \
(ex.: "produto chegou quebrado", "não recebi o pedido").
- Se for sobre elogios, use frases com sentido positivo explícito.
- Não invente temas sem relação com a pergunta.
- Responda APENAS com as frases, uma por linha, sem numeração e sem comentários.

PERGUNTA: {pergunta}"""


@dataclass
class Evidencia:
    """Um grupo de avaliações com o mesmo texto, pronto para virar contexto."""

    texto: str
    similaridade: float
    notas: list[int] = field(default_factory=list)
    review_ids: list[str] = field(default_factory=list)
    order_ids: list[str] = field(default_factory=list)
    consultas: list[str] = field(default_factory=list)  # buscas que encontraram este grupo

    @property
    def ocorrencias(self) -> int:
        """Quantas avaliações com esse texto apareceram entre os candidatos."""
        return len(self.review_ids)


def _chave(texto: str) -> str:
    """Dois textos são 'equivalentes' se têm as mesmas palavras na mesma ordem."""
    return " ".join(tokenizar(texto))


def processar_pergunta(pergunta: str) -> str:
    """Limpeza leve: minúsculas, sem pontuação e sem palavras de pergunta/funcionais."""
    palavras = tokenizar(pergunta)
    uteis = [p for p in palavras if p not in PALAVRAS_IGNORADAS]
    # Se a limpeza removeu tudo, melhor buscar com a pergunta original do que com nada
    return " ".join(uteis if uteis else palavras)


def _buscar_e_agrupar(store: Chroma, consulta: str, candidatos: int) -> list[Evidencia]:
    """Busca os `candidatos` mais próximos de UMA consulta e agrupa textos equivalentes."""
    resultados = store.similarity_search_with_score(consulta, k=candidatos)

    grupos: dict[str, Evidencia] = {}
    for doc, distancia in resultados:  # já vêm do mais próximo ao mais distante
        chave = _chave(doc.page_content)
        if chave not in grupos:
            # Chroma com cosseno devolve DISTÂNCIA (1 - cosseno); convertemos de volta
            grupos[chave] = Evidencia(
                texto=doc.page_content, similaridade=1 - distancia, consultas=[consulta]
            )
        ev = grupos[chave]
        ev.notas.append(doc.metadata["review_score"])
        ev.review_ids.append(doc.metadata["review_id"])
        ev.order_ids.append(doc.metadata["order_id"])

    return list(grupos.values())


def recuperar(
    store: Chroma,
    pergunta: str,
    candidatos: int = CANDIDATOS,
    top: int = TOP_EVIDENCIAS,
    processar: bool = True,
) -> list[Evidencia]:
    """
    Busca simples: uma única consulta (a pergunta, processada ou crua).

    Observação: `ocorrencias` conta só as cópias que apareceram entre os
    candidatos; se um texto existir mais vezes na base que o número de
    candidatos, a contagem real é maior.
    """
    consulta = processar_pergunta(pergunta) if processar else pergunta
    return _buscar_e_agrupar(store, consulta, candidatos)[:top]


def expandir_pergunta(pergunta: str, llm) -> list[str]:
    """Pede ao LLM várias buscas específicas. Se falhar, cai para a pergunta processada."""
    try:
        resposta = llm.invoke(PROMPT_REESCRITA.format(pergunta=pergunta))
        linhas = [
            re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", linha).strip()
            for linha in resposta.content.splitlines()
        ]
        consultas = list(dict.fromkeys(l for l in linhas if l))[:MAX_CONSULTAS]
        if consultas:
            return consultas
        print("Aviso: o LLM não devolveu buscas; usando a pergunta processada.")
    except Exception as erro:
        print(f"Aviso: falha ao reescrever a pergunta ({erro}); usando a pergunta processada.")
    return [processar_pergunta(pergunta)]


def recuperar_multiconsulta(
    store: Chroma,
    pergunta: str,
    llm,
    candidatos_por_consulta: int = CANDIDATOS_POR_CONSULTA,
    top: int = TOP_EVIDENCIAS,
) -> tuple[list[str], list[Evidencia]]:
    """
    Busca com reescrita: o LLM gera várias consultas, cada uma é buscada no Chroma
    e os resultados são unidos em rodízio (melhor de cada consulta, depois o 2º
    melhor de cada uma...), para cobrir temas diferentes. A similaridade NÃO é usada
    para ordenar entre consultas, porque não é comparável entre consultas de
    tamanhos diferentes.

    Retorna (consultas geradas, evidências).
    """
    consultas = expandir_pergunta(pergunta, llm)
    rankings = [_buscar_e_agrupar(store, c, candidatos_por_consulta) for c in consultas]

    escolhidas: dict[str, Evidencia] = {}
    for posicao in range(max(len(r) for r in rankings)):
        for consulta, ranking in zip(consultas, rankings):
            if posicao >= len(ranking):
                continue
            ev = ranking[posicao]
            chave = _chave(ev.texto)
            if chave in escolhidas:
                # Mesmo texto achado por outra busca: só registramos a convergência
                if consulta not in escolhidas[chave].consultas:
                    escolhidas[chave].consultas.append(consulta)
            elif len(escolhidas) < top:
                escolhidas[chave] = ev
        if len(escolhidas) >= top:
            break

    return consultas, list(escolhidas.values())


def imprimir_evidencias(evidencias: list[Evidencia], consultas: list[str] | None = None) -> None:
    """Mostra as evidências de forma legível. Com `consultas`, indica qual busca achou cada uma."""
    for i, ev in enumerate(evidencias, 1):
        notas = ", ".join(f"{n}★×{c}" for n, c in sorted(Counter(ev.notas).items()))
        origem = ""
        if consultas:
            idx = [str(consultas.index(c) + 1) for c in ev.consultas if c in consultas]
            origem = f" | b{'+b'.join(idx)}"
        print(f"{i:2}. sim={ev.similaridade:.3f} | {ev.ocorrencias}x | {notas}{origem} | {ev.texto}")