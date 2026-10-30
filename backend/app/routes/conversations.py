"""Conversations: list, read and send messages. Always scoped to the authenticated user."""

from flask import Blueprint, current_app, g, jsonify

from ..auth import login_required
from ..db import repositories
from ..extensions import limiter, rate_limit_user_key
from ..services import chat
from ..validation import is_valid_conversation_id, parse_json_body, validate_message

bp = Blueprint("conversations", __name__, url_prefix="/conversations")


@bp.get("")
@login_required
def list_conversations():
    conversations = []
    for conversation_id, question, answer, created_at in repositories.list_conversations(g.user_id):
        conversations.append(
            {
                "id": conversation_id,
                "title": (question[:40] + "...") if question else "Conversa",
                "preview": (answer[:80] + "...") if answer else "",
                "created_at": created_at,
            }
        )
    return jsonify({"conversations": conversations})


@bp.get("/<conversation_id>/messages")
@login_required
def list_messages(conversation_id):
    if not is_valid_conversation_id(conversation_id):
        return jsonify({"error": "Conversa inválida"}), 400
    rows = repositories.get_conversation_messages(g.user_id, conversation_id)
    return jsonify(
        {
            "messages": [
                {"question": question, "answer": answer, "created_at": created_at}
                for question, answer, created_at in rows
            ]
        }
    )


@bp.post("/<conversation_id>/messages")
@login_required
@limiter.limit(lambda: current_app.config["RATE_LIMIT_MESSAGE"], key_func=rate_limit_user_key)
def send_message(conversation_id):
    """Send a question. The conversation id is a UUID chosen by the client; the conversation
    exists as soon as it has a message."""
    data = parse_json_body()
    if data is None:
        return jsonify({"error": "Requisição inválida"}), 400
    if not is_valid_conversation_id(conversation_id):
        return jsonify({"error": "Conversa inválida"}), 400
    message, error = validate_message(data.get("message"))
    if error:
        return jsonify({"error": error}), 400

    try:
        result = chat.send_message(g.user_id, conversation_id, message)
    except chat.DailyLimitReached:
        return jsonify({"error": "O limite diário de mensagens da demo foi atingido. Volte amanhã."}), 429
    except chat.AssistantBusy:
        return jsonify({"error": "O assistente está muito ocupado agora. Tente novamente em instantes."}), 503
    except chat.AssistantUnavailable:
        return jsonify({"error": "O assistente está indisponível no momento. Tente novamente em instantes."}), 502

    return jsonify({"conversation_id": result.conversation_id, "answer": result.answer, "truncated": result.truncated})
