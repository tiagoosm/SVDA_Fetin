"""Memória da conversa e contexto do produtor enviados ao modelo.

A memória é por (usuário, conversa) e é reconstruída a partir da tabela
historico, então sobrevive a reinícios do servidor. Só as últimas
HISTORY_MAX_MESSAGES mensagens são enviadas ao modelo (controle de custo).
"""

from flask import current_app
from langchain_core.messages import AIMessage, HumanMessage

from ..config import TAMANHOS_REBANHO, TIPOS_GADO
from ..db import repositories


def carregar_historico(usuario_id, conversa_id, limite=None):
    limite = current_app.config["HISTORY_MAX_MESSAGES"] if limite is None else limite
    if limite <= 0:
        return []
    pares = (limite + 1) // 2  # Cada registro tem uma pergunta e uma resposta

    mensagens = []
    for pergunta, resposta in repositories.recent_turns(usuario_id, conversa_id, pares):
        mensagens.append(HumanMessage(content=pergunta or ""))
        mensagens.append(AIMessage(content=resposta or ""))
    return mensagens[-limite:]


def contexto_do_produtor(usuario):
    # Monta a linha de contexto apenas a partir das listas fechadas
    if not usuario:
        return ""
    porte = TAMANHOS_REBANHO.get(usuario.get("tamanho_rebanho"))
    tipo = TIPOS_GADO.get(usuario.get("tipo_gado"))
    if not porte or not tipo:
        return ""
    return f"O produtor tem rebanho {tipo}, de porte {porte}."
