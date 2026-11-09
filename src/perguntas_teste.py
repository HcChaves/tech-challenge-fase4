"""
Conjunto de perguntas de teste rotuladas.
Usado na calibração e na avaliação.

Cada item: (tipo, comportamento esperado, pergunta)
  esperado = "responder": existe evidência na base
  esperado = "recusar":   o sistema deve dizer que não há evidências suficientes
"""

PERGUNTAS = [
    # Dentro do escopo, amplas
    ("ampla", "responder", "Quais são os principais problemas relatados pelos clientes?"),
    ("ampla", "responder", "Quais reclamações estão relacionadas à entrega?"),
    ("ampla", "responder", "O que os clientes mais elogiam nos produtos?"),
    ("ampla", "responder", "Quais problemas aparecem nas avaliações de clientes insatisfeitos?"),
    ("ampla", "responder", "Existem padrões de reclamação sobre a qualidade dos produtos?"),
    # Dentro do escopo, específicas com evidência
    ("especifica", "responder", "Há reclamações sobre produtos que chegaram com a embalagem danificada?"),
    ("especifica", "responder", "Há queixas sobre falta de resposta do atendimento?"),
    ("especifica", "responder", "Clientes relatam dificuldade para trocar ou devolver produtos?"),
    # Específicas sem evidência (confirmar por palavra-chave no notebook)
    ("especifica_ausente", "recusar", "Os clientes relatam vazamento de dados pessoais?"),
    ("especifica_ausente", "recusar", "Há reclamações sobre a assinatura mensal do serviço de streaming?"),
    # Fora do escopo
    ("fora_escopo", "recusar", "Qual foi o desempenho financeiro da Olist em 2018?"),
    ("fora_escopo", "recusar", "Qual é a capital da França?"),
    ("fora_escopo", "recusar", "Qual será a cotação do dólar amanhã?"),
    # Quantitativas (o sistema só recupera exemplos, não calcula estatísticas)
    ("quantitativa", "recusar", "Qual é a nota média dos clientes?"),
    ("quantitativa", "recusar", "Quantas avaliações mencionam atraso na entrega?"),
    # Inválidas
    ("invalida", "recusar", "asdfgh"),
    ("invalida", "recusar", "???"),
    ("invalida", "recusar", "kkkkkkk"),
        # Curtas e legítimas (testam se o piso recusa perguntas boas por terem poucas palavras)
    ("curta", "responder", "Entrega atrasada?"),
    ("curta", "responder", "Produtos quebrados"),
    ("curta", "responder", "Atendimento ruim"),
    ("curta", "responder", "Qualidade dos produtos")
]