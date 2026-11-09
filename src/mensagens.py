"""Mensagens exibidas ao usuário quando o sistema não responde, uma por motivo."""

MENSAGEM_SEM_EVIDENCIA = (
    "Não há evidências suficientes nas avaliações para responder a esta pergunta."
)
MENSAGEM_FALHA = (
    "Não foi possível gerar uma resposta fundamentada nas avaliações recuperadas."
)
MENSAGEM_QUANTITATIVA = (
    "Esta pergunta pede números ou estatísticas, e o sistema só recupera exemplos de "
    "avaliações, sem calcular métricas sobre toda a base."
)
MENSAGEM_FORA_DOMINIO = (
    "Esta pergunta não parece relacionada às avaliações de clientes da base, "
    "então não há evidências para respondê-la."
)
MENSAGEM_INVALIDA = (
    "Não consegui interpretar a pergunta. Reformule usando palavras sobre produtos, "
    "entrega, atendimento ou outras experiências de compra."
)
MENSAGEM_INSUFICIENTE = (
    "As evidências encontradas são insuficientes para responder com segurança: "
    "menos de duas avaliações sustentam uma resposta."
)
MENSAGEM_ERRO_LLM = (
    "O serviço de linguagem está indisponível no momento (por exemplo, cota esgotada). "
    "Tente novamente mais tarde."
)