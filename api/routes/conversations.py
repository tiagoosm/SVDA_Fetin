"""Lista de conversas e histórico do usuário autenticado."""
from flask import Blueprint, g, jsonify, request

from ..db import repositories
from ..security import login_required

bp = Blueprint("conversations", __name__)


@bp.route("/conversas", methods=["GET"])
@login_required
def listar_conversas():
    # Monta resposta resumida
    conversas = []
    for conversa_id, pergunta, resposta, data in repositories.list_conversations(g.usuario_id):
        titulo = (pergunta[:40] + "...") if pergunta else "Conversa"
        previa = (resposta[:80] + "...") if resposta else ""
        conversas.append({
            "conversa_id": conversa_id,
            "titulo": titulo,
            "previa": previa,
            "data": data
        })
    return jsonify({"conversas": conversas})


@bp.route("/historico", methods=["GET"])
@login_required
def historico():
    # Busca histórico específico ou todos
    registros = repositories.get_history(g.usuario_id, request.args.get("conversa_id"))
    return jsonify({
        "historico": [
            {"pergunta": p, "resposta": r, "data": d}
            for p, r, d in registros
        ]
    })
