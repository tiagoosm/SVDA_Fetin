"""Sign-up, login, logout and current user."""

import logging
import secrets
import sqlite3

from flask import Blueprint, current_app, g, jsonify, session
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash

from ..auth import login_required
from ..db import repositories
from ..extensions import limiter
from ..validation import (
    parse_json_body,
    validate_credentials,
    validate_invite_code,
    validate_new_password,
    validate_profile,
)

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__, url_prefix="/auth")

# Hash checked when the e-mail does not exist, so response time does not reveal
# which e-mails are registered.
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_hex(16))


@bp.post("/register")
@limiter.limit(lambda: current_app.config["RATE_LIMIT_REGISTER"])
def register():
    data = parse_json_body()
    if data is None:
        return jsonify({"error": "Requisição inválida"}), 400

    error = validate_invite_code(data)
    if error:
        return jsonify({"error": error}), 403

    email, password, error = validate_credentials(data)
    if error:
        return jsonify({"error": error}), 400
    error = validate_new_password(password)
    if error:
        return jsonify({"error": error}), 400
    profile, error = validate_profile(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        repositories.create_user(email, generate_password_hash(password), **profile)
    except sqlite3.IntegrityError:
        return jsonify({"error": "E-mail já cadastrado"}), 409
    return jsonify({"message": "Usuário registrado com sucesso"}), 201


@bp.post("/login")
@limiter.limit(lambda: current_app.config["RATE_LIMIT_LOGIN"])
def login():
    data = parse_json_body()
    if data is None:
        return jsonify({"error": "Requisição inválida"}), 400

    email, password, error = validate_credentials(data)
    if error:
        return jsonify({"error": error}), 400

    user = repositories.get_credentials(email)

    # Always compute a hash, whether or not the user exists
    password_ok = check_password_hash(user[1] if user else DUMMY_PASSWORD_HASH, password)
    if not (user and password_ok):
        logger.info("Failed login attempt from %s", get_remote_address())
        return jsonify({"error": "E-mail ou senha incorretos"}), 401

    session.clear()  # prevents session fixation
    session["user_id"] = user[0]
    return jsonify({"message": "Login realizado com sucesso"})


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logout realizado com sucesso"})


@bp.get("/me")
@login_required
def me():
    user = repositories.get_user(g.user_id)
    if not user:
        session.clear()
        return jsonify({"error": "Usuário não autenticado"}), 401
    return jsonify(user)
