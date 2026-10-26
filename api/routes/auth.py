"""Cadastro, login, logout e usuário atual."""
import logging
import secrets
import sqlite3

from flask import Blueprint, current_app, g, jsonify, session
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import repositories
from ..extensions import limiter
from ..security import json_body, login_required, validar_credenciais, validar_nova_senha, validar_perfil

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)

# Hash usado quando o e-mail não existe, para o tempo de resposta do login
# não revelar quais e-mails estão cadastrados.
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_hex(16))


@bp.route("/register", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT_REGISTER"])
def register():
    data = json_body()
    if data is None:
        return jsonify({"erro": "Requisição inválida"}), 400

    email, senha, erro = validar_credenciais(data)
    if erro:
        return jsonify({"erro": erro}), 400
    erro = validar_nova_senha(senha)
    if erro:
        return jsonify({"erro": erro}), 400
    perfil, erro = validar_perfil(data)
    if erro:
        return jsonify({"erro": erro}), 400

    try:
        repositories.create_user(email, generate_password_hash(senha), **perfil)
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Email já cadastrado"}), 409
    return jsonify({"mensagem": "Usuário registrado com sucesso"}), 201


@bp.route("/login", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT_LOGIN"])
def login():
    data = json_body()
    if data is None:
        return jsonify({"erro": "Requisição inválida"}), 400

    email, senha, erro = validar_credenciais(data)
    if erro:
        return jsonify({"erro": erro}), 400

    user = repositories.get_credentials(email)

    # Verifica senha (sempre calcula um hash, exista o usuário ou não)
    senha_ok = check_password_hash(user[1] if user else DUMMY_PASSWORD_HASH, senha)
    if not (user and senha_ok):
        logger.info("Failed login attempt from %s", get_remote_address())
        return jsonify({"erro": "Credenciais inválidas"}), 401

    session.clear()  # Evita fixação de sessão
    session["usuario_id"] = user[0]
    return jsonify({"mensagem": "Login realizado com sucesso"})


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"mensagem": "Logout realizado com sucesso"})


@bp.route("/me", methods=["GET"])
@login_required
def me():
    usuario = repositories.get_user(g.usuario_id)
    if not usuario:
        session.clear()
        return jsonify({"erro": "Usuário não autenticado"}), 401
    return jsonify(usuario)
