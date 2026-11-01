"""
transforma as evidências recuperadas em
um bloco de texto para a LLM e guarda o mapa para rastreabilidade.
"""

import re
from collections import Counter
from dataclasses import dataclass

from src.retrieval import Evidencia


@dataclass
class Contexto:
    texto: str                        # o que será enviado à LLM
    evidencias: dict[str, Evidencia]  # "E1" -> Evidencia (fica só no sistema)


def _formatar_notas(notas: list[int]) -> str:
    contagem = Counter(notas)
    if len(contagem) == 1:
        (nota,) = contagem
        return f"nota {nota}★"
    return "notas " + ", ".join(f"{n}★×{c}" for n, c in sorted(contagem.items()))


def construir_contexto(evidencias: list[Evidencia]) -> Contexto:
    """Uma linha por evidência: [E1] (N avaliações · nota/notas) texto."""
    linhas: list[str] = []
    mapa: dict[str, Evidencia] = {}

    for i, ev in enumerate(evidencias, 1):
        id_ev = f"E{i}"
        mapa[id_ev] = ev
        n = ev.ocorrencias
        quantidade = f"{n} avaliação" if n == 1 else f"{n} avaliações"
        linhas.append(f"[{id_ev}] ({quantidade} · {_formatar_notas(ev.notas)}) {ev.texto}")

    return Contexto(texto="\n".join(linhas), evidencias=mapa)


def extrair_citacoes(resposta: str) -> list[str]:
    """Identificadores (E1, E3...) citados entre colchetes, sem repetição, na ordem em que aparecem."""
    achados: list[str] = []
    for trecho in re.findall(r"\[([^\]]*)\]", resposta):
        achados.extend(re.findall(r"E\d+", trecho))
    return list(dict.fromkeys(achados))


def validar_citacoes(resposta: str, contexto: Contexto) -> tuple[list[str], list[str]]:
    """Retorna (citações válidas, citações inexistentes no contexto)."""
    citadas = extrair_citacoes(resposta)
    validas = [c for c in citadas if c in contexto.evidencias]
    invalidas = [c for c in citadas if c not in contexto.evidencias]
    return validas, invalidas