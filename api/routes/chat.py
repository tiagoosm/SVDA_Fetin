"""Envio de mensagens ao assistente."""

import logging
import sqlite3
import uuid

from flask import Blueprint, current_app, g, jsonify
from openai import APITimeoutError, OpenAIError, RateLimitError

from ..db import repositories
from ..extensions import limiter, rate_limit_user_key
from ..security import conversa_id_valido, json_body, login_required, validar_mensagem
from ..services.history import carregar_historico, contexto_do_produtor
from ..services.llm import gerar_resposta

logger = logging.getLogger(__name__)

bp = Blueprint("chat", __name__)


@bp.route("/mensagem", methods=["POST"])
@login_required
@limiter.limit(lambda: current_app.config["RATE_LIMIT_MESSAGE"], key_func=rate_limit_user_key)
def responder():
    data = json_body()
    if data is None:
        return jsonify({"erro": "Requisição inválida"}), 400

    usuario_id = g.usuario_id
    pergunta_usuario, erro = validar_mensagem(data.get("mensagem"))
    if erro:
        return jsonify({"erro": erro}), 400
    conversa_id = data.get("conversa_id") or str(uuid.uuid4())  # Cria ID da conversa se não tiver
    if not conversa_id_valido(conversa_id):
        return jsonify({"erro": "conversa_id inválido"}), 400

    # Chama o modelo com o histórico desta conversa (últimas N mensagens)
    try:
        texto_resposta = gerar_resposta(
            pergunta_usuario,
            carregar_historico(usuario_id, conversa_id),
            contexto_do_produtor(repositories.get_user(usuario_id)),
        )
    except (RateLimitError, APITimeoutError):
        logger.exception("LLM busy or timed out (user_id=%s)", usuario_id)
        return jsonify({"erro": "O assistente está muito ocupado agora. Tente novamente em instantes."}), 503
    except OpenAIError:
        # Detalhes (chave inválida, cota etc.) ficam só no log do servidor
        logger.exception("LLM request failed (user_id=%s)", usuario_id)
        return jsonify({"erro": "O assistente está indisponível no momento. Tente novamente em instantes."}), 502

    # Salva no banco
    try:
        repositories.add_message(usuario_id, conversa_id, pergunta_usuario, texto_resposta)
    except sqlite3.Error:
        logger.exception("Failed to save message history (user_id=%s)", usuario_id)

    return jsonify({"resposta": texto_resposta, "conversa_id": conversa_id})
