"""Camada do LLM: prompt do sistema e chamada ao modelo."""

import os

from flask import current_app
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "system_prompt.md")


def load_system_template(path=PROMPT_PATH):
    # O texto do prompt fica em prompts/system_prompt.md; aqui só se acrescenta
    # o espaço reservado para a linha de contexto do produtor.
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return text.rstrip("\n") + "\n{contexto_produtor}"


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", load_system_template()),  # Mensagem inicial (contexto fixo)
        MessagesPlaceholder(variable_name="history"),  # Histórico da conversa (últimas N mensagens)
        ("human", "{input}"),  # Entrada do usuário
    ]
)


def create_llm(max_tokens, timeout=30):
    # Modelo OpenAI usado (GPT-4o-mini). max_tokens limita o custo de cada resposta.
    return ChatOpenAI(temperature=0.7, model="gpt-4o-mini", max_tokens=max_tokens, timeout=timeout)


def get_llm():
    # Criado sob demanda, uma vez por app (testes injetam um modelo falso)
    llm = current_app.extensions.get("svda_llm")
    if llm is None:
        llm = create_llm(current_app.config["LLM_MAX_TOKENS"], current_app.config["LLM_TIMEOUT_SECONDS"])
        current_app.extensions["svda_llm"] = llm
    return llm


def gerar_resposta(pergunta, historico, contexto_produtor=""):
    """Faz UMA chamada ao LLM e devolve o texto da resposta."""
    chain = prompt | get_llm()
    resposta = chain.invoke(
        {
            "input": pergunta,
            "history": historico,
            "contexto_produtor": contexto_produtor,
        }
    )
    return resposta.content
