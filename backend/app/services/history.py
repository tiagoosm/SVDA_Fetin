"""Conversation memory and producer context sent to the model.

Memory is per (user, conversation) and rebuilt from the messages table, so it
survives restarts. Only the last HISTORY_MAX_MESSAGES messages reach the model
(cost control).
"""

from flask import current_app
from langchain_core.messages import AIMessage, HumanMessage

from ..config import CATTLE_TYPES, HERD_SIZES
from ..db import repositories


def load_history(user_id, conversation_id, limit=None):
    limit = current_app.config["HISTORY_MAX_MESSAGES"] if limit is None else limit
    if limit <= 0:
        return []
    pairs = (limit + 1) // 2  # each stored row holds one question and one answer

    messages = []
    for question, answer in repositories.recent_turns(user_id, conversation_id, pairs):
        messages.append(HumanMessage(content=question or ""))
        messages.append(AIMessage(content=answer or ""))
    return messages[-limit:]


def producer_context(user):
    """One line of context built only from the closed lists."""
    if not user:
        return ""
    size = HERD_SIZES.get(user.get("herd_size"))
    cattle = CATTLE_TYPES.get(user.get("cattle_type"))
    if not size or not cattle:
        return ""
    return f"O produtor tem rebanho {cattle}, de porte {size}."
