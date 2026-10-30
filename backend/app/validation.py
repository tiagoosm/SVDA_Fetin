"""Request parsing and input validation. User-facing messages are in Portuguese."""

import hmac
import re
import uuid

from flask import current_app, request

from .config import CATTLE_TYPES, HERD_SIZES, MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MAX_PASSWORD_LENGTH

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def parse_json_body():
    """Return the JSON object of the request, or None.

    Requiring application/json also forces a CORS preflight on cross-origin calls.
    """
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def validate_credentials(data):
    """Return (email, password, error)."""
    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or not email.strip() or not password:
        return None, None, "Informe e-mail e senha"
    email = email.strip()
    if len(email) > MAX_EMAIL_LENGTH or not EMAIL_RE.match(email):
        return None, None, "E-mail inválido"
    if len(password) > MAX_PASSWORD_LENGTH:
        return None, None, f"A senha deve ter no máximo {MAX_PASSWORD_LENGTH} caracteres"
    return email, password, None


def validate_new_password(password):
    minimum = current_app.config["MIN_PASSWORD_LENGTH"]
    if len(password) < minimum:
        return f"A senha deve ter pelo menos {minimum} caracteres"
    return None


def validate_invite_code(data):
    """Require the invite code when INVITE_CODE is configured (constant-time comparison)."""
    expected = current_app.config["INVITE_CODE"]
    if not expected:
        return None
    given = data.get("invite_code")
    if not isinstance(given, str) or not hmac.compare_digest(given.strip().encode(), expected.encode()):
        return "Código de convite inválido"
    return None


def validate_profile(data):
    """Return (profile dict, error)."""
    name = data.get("name")
    herd_size = data.get("herd_size")
    cattle_type = data.get("cattle_type")
    if not isinstance(name, str) or not name.strip():
        return None, "Informe seu nome"
    if len(name.strip()) > MAX_NAME_LENGTH:
        return None, f"O nome deve ter no máximo {MAX_NAME_LENGTH} caracteres"
    if herd_size not in HERD_SIZES:
        return None, "Tamanho do rebanho inválido"
    if cattle_type not in CATTLE_TYPES:
        return None, "Tipo de gado inválido"
    return {"name": name.strip(), "herd_size": herd_size, "cattle_type": cattle_type}, None


def validate_message(text):
    """Return (message, error)."""
    if not isinstance(text, str) or not text.strip():
        return None, "Digite uma mensagem"
    text = text.strip()
    maximum = current_app.config["MAX_MESSAGE_CHARS"]
    if len(text) > maximum:
        return None, f"A mensagem deve ter no máximo {maximum} caracteres"
    return text, None


def is_valid_conversation_id(value):
    try:
        return str(uuid.UUID(value)) == value.lower()
    except (ValueError, AttributeError, TypeError):
        return False
