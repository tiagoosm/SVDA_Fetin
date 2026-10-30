"""LLM layer: system prompt and the call to the model."""

import os

from flask import current_app
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "system_prompt.md")


def load_system_template(path=PROMPT_PATH):
    # The prompt text lives in prompts/system_prompt.md; only the producer-context
    # placeholder is appended here.
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return text.rstrip("\n") + "\n{producer_context}"


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", load_system_template()),  # fixed context
        MessagesPlaceholder(variable_name="history"),  # last N messages of the conversation
        ("human", "{input}"),  # the user's question
    ]
)


def create_llm(max_tokens, timeout=30):
    # OpenAI GPT-4o-mini. max_tokens bounds the cost of each answer.
    return ChatOpenAI(temperature=0.7, model="gpt-4o-mini", max_tokens=max_tokens, timeout=timeout)


def get_llm():
    # Created lazily, once per app (tests inject a fake model)
    llm = current_app.extensions.get("svda_llm")
    if llm is None:
        llm = create_llm(current_app.config["LLM_MAX_TOKENS"], current_app.config["LLM_TIMEOUT_SECONDS"])
        current_app.extensions["svda_llm"] = llm
    return llm


def generate_answer(question, history, producer_context=""):
    """Make ONE model call and return (answer, truncated).

    truncated is True when the model stopped because it reached LLM_MAX_TOKENS.
    """
    chain = prompt | get_llm()
    response = chain.invoke({"input": question, "history": history, "producer_context": producer_context})
    truncated = (getattr(response, "response_metadata", None) or {}).get("finish_reason") == "length"
    return response.content, truncated
