"""Global error handling: always JSON, never leaking internal details."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

HTTP_MESSAGES = {
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
        return jsonify({"error": HTTP_MESSAGES.get(status, "Erro na requisição")}), status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Details go only to the server log; the client gets a generic message
        logger.exception("Unhandled error")
        return jsonify({"error": "Erro interno do servidor. Tente novamente mais tarde."}), 500
