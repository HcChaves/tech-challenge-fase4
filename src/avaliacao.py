"""
Avaliação mínima (Etapa 12): roda o pipeline em perguntas NOVAS (não usadas para calibrar
nenhuma barreira) e gera um relatório em avaliacao/relatorio_avaliacao.md.

Uso:  python -m src.avaliacao
"""

import re
from collections import Counter
from pathlib import Path

from src.embeddings import NILCEmbeddings
from src.llm import criar_llm
from src.pipeline import Resultado, responder
from src.vectorstore import carregar_colecao

RAIZ = Path(__file__).resolve().parent.parent
RELATORIO = RAIZ / "avaliacao" / "relatorio_avaliacao.md"

# (tipo, comportamento esperado, pergunta)
PERGUNTAS_AVALIACAO = [
    ("reembolso", "responder", "Quais reclamações existem sobre reembolso e cancelamento de pedidos?"),
    ("entrega_rapida", "responder", "Os clientes elogiam a rapidez da entrega?"),
    ("anuncio", "responder", "O que os clientes dizem sobre produtos diferentes do anunciado?"),
    ("frete", "responder", "Há reclamações sobre o valor do frete?"),
    ("defeito", "responder", "Quais problemas aparecem em produtos que vieram com defeito ou não funcionam?"),
    ("recomendacao", "responder", "Os clientes recomendam a loja e os vendedores?"),
    ("rastreio", "responder", "Há queixas sobre o código de rastreamento do pedido?"),
    ("cor_tamanho", "responder", "Existem reclamações sobre cor ou tamanho errado do produto?"),
    ("fora_escopo", "recusar", "Quem ganhou a Copa do Mundo de 2022?"),
    ("fora_escopo", "recusar", "Como fazer um bolo de chocolate?"),
    ("ausente", "recusar", "Os clientes relatam problemas com passagens aéreas?"),
    ("quantitativa", "recusar", "Qual é a porcentagem de clientes insatisfeitos?"),
]

PADRAO_LINHA = re.compile(r"^- \*\*[^*]+\*\*: .+(\[E\d+\])+[.]?\s*$")


def _veredito(r: Resultado, esperado: str) -> str:
    if r.motivo == "erro_llm":
        return "falha_llm"  
    recusou = r.motivo is not None
    return "ok" if recusou == (esperado == "recusar") else "ERRO"


def _formato_ok(texto: str) -> bool:
    linhas = [l for l in texto.splitlines() if l.strip()]
    return bool(linhas) and all(PADRAO_LINHA.match(l) for l in linhas)


def _aproveitamento(r: Resultado) -> float:
    citadas = len(r.resposta.citadas)
    return citadas / max(1, citadas + len(r.resposta.nao_citadas))


def _linha_evidencia(id_ev, ev) -> str:
    notas = ", ".join(f"{n}★×{c}" for n, c in sorted(Counter(ev.notas).items()))
    ids = ", ".join(ev.review_ids[:3]) + (f" (+{ev.ocorrencias - 3})" if ev.ocorrencias > 3 else "")
    return f"- **[{id_ev}]** ({ev.ocorrencias}x · {notas}) {ev.texto}  \n  `review_id`: {ids}"


def gerar_relatorio(resultados: list[tuple[str, str, str, Resultado]]) -> str:
    total = len(resultados)
    vereditos = [_veredito(r, esperado) for _, esperado, _, r in resultados]
    respondidas = [(p, r) for _, _, p, r in resultados if r.motivo is None]

    md = ["# Relatório de avaliação", ""]
    md.append(f"Perguntas inéditas avaliadas: **{total}** (não foram usadas para calibrar nenhuma barreira).")
    md += ["", "## Resumo", ""]
    md.append(f"- Comportamento correto (responder ou recusar como esperado): **{vereditos.count('ok')} de {total}**")
    if vereditos.count("falha_llm"):
        md.append(f"- Falhas de infraestrutura (cota ou rede), não contadas como erro: {vereditos.count('falha_llm')}")
    if respondidas:
        n = len(respondidas)
        aprov = sum(_aproveitamento(r) for _, r in respondidas) / n
        md.append(f"- Aproveitamento médio das evidências recuperadas (citadas ÷ recuperadas): **{aprov:.0%}**")
        md.append(f"- Respondidas na 1ª tentativa: {sum(r.resposta.tentativas == 1 for _, r in respondidas)} de {n}")
        md.append(f"- Formato padronizado seguido: {sum(_formato_ok(r.resposta.texto) for _, r in respondidas)} de {n}")
        md.append(f"- Respostas com citações válidas: {sum(r.resposta.fundamentada for _, r in respondidas)} de {n}")

    md += ["", "## Resultado por pergunta", ""]
    md.append("| Tipo | Esperado | Resultado | Veredito | Citadas/recuperadas | Tentativas | Pergunta |")
    md.append("|---|---|---|---|---|---|---|")
    for (tipo, esperado, pergunta, r), veredito in zip(resultados, vereditos):
        citadas = len(r.resposta.citadas)
        recuperadas = citadas + len(r.resposta.nao_citadas)
        md.append(
            f"| {tipo} | {esperado} | {r.motivo or 'respondida'} | {veredito} | "
            f"{citadas}/{recuperadas} | {r.resposta.tentativas} | {pergunta} |"
        )

    md += ["", "## Respostas e evidências (para conferir a fundamentação)", ""]
    for pergunta, r in respondidas:
        res = r.resposta
        md.append(f"### {pergunta}")
        md += ["", res.texto, "", "**Evidências citadas:**", ""]
        md += [_linha_evidencia(i, ev) for i, ev in res.citadas.items()]
        if res.nao_citadas:
            md += ["", "**Recuperadas e não citadas:**", ""]
            md += [f"- [{i}] {ev.texto}" for i, ev in res.nao_citadas.items()]
        md.append("")

    recusadas = [(p, r) for _, _, p, r in resultados if r.motivo is not None]
    if recusadas:
        md += ["## Perguntas recusadas", ""]
        md += [f"- {p} → **{r.motivo}**: {r.resposta.texto}" for p, r in recusadas]
        md.append("")

    return "\n".join(md)


def main() -> None:
    store = carregar_colecao(NILCEmbeddings())
    llm = criar_llm()

    resultados = []
    for tipo, esperado, pergunta in PERGUNTAS_AVALIACAO:
        r = responder(pergunta, store, llm)
        resultados.append((tipo, esperado, pergunta, r))
        print(f"{_veredito(r, esperado):9} | {tipo:14} | {r.motivo or 'respondida':24} | {pergunta}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO.write_text(gerar_relatorio(resultados), encoding="utf-8")
    print(f"\nRelatório salvo em {RELATORIO}")


if __name__ == "__main__":
    main()