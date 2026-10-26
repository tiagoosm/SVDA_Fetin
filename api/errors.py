"""Tratamento global de erros: sempre JSON, sem vazar detalhes internos."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

MENSAGENS = {
    400: "Requisição inválida",
    401: "Usuário não autenticado",
    404: "Recurso não encontrado",
    405: "Método não permitido",
    413: "Requisição grande demais",
    415: "Tipo de conteúdo não suportado",
    429: "Muitas requisições. Aguarde um pouco e tente novamente.",
}


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        status = error.code or 500
        return jsonify({"erro": MENSAGENS.get(status, "Erro na requisição")}), status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Detalhes só no log do servidor; o cliente recebe uma mensagem genérica
        logger.exception("Unhandled error")
        return jsonify({"erro": "Erro interno do servidor. Tente novamente mais tarde."}), 500
