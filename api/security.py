"""Autenticação por sessão e validação de entrada."""

import hmac
import re
import uuid
from functools import wraps

from flask import current_app, g, jsonify, request, session

from .config import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MAX_PASSWORD_LENGTH, TAMANHOS_REBANHO, TIPOS_GADO

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view):
    # O usuário vem SEMPRE da sessão assinada no servidor, nunca do cliente
    @wraps(view)
    def wrapper(*args, **kwargs):
        usuario_id = session.get("usuario_id")
        if not isinstance(usuario_id, int):
            return jsonify({"erro": "Usuário não autenticado"}), 401
        g.usuario_id = usuario_id
        return view(*args, **kwargs)

    return wrapper


def json_body():
    # Exige JSON (Content-Type: application/json), o que também força o
    # preflight de CORS em requisições vindas de outras origens.
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def validar_credenciais(data):
    email = data.get("email")
    senha = data.get("senha")
    if not isinstance(email, str) or not isinstance(senha, str) or not email.strip() or not senha:
        return None, None, "Email e senha são obrigatórios"
    email = email.strip()
    if len(email) > MAX_EMAIL_LENGTH or not EMAIL_RE.match(email):
        return None, None, "Email inválido"
    if len(senha) > MAX_PASSWORD_LENGTH:
        return None, None, f"A senha deve ter no máximo {MAX_PASSWORD_LENGTH} caracteres"
    return email, senha, None


def validar_nova_senha(senha):
    minimo = current_app.config["MIN_PASSWORD_LENGTH"]
    if len(senha) < minimo:
        return f"A senha deve ter pelo menos {minimo} caracteres"
    return None


def validar_convite(data):
    """Exige o código de convite quando INVITE_CODE está configurado."""
    esperado = current_app.config["INVITE_CODE"]
    if not esperado:
        return None
    enviado = data.get("codigo_convite")
    if not isinstance(enviado, str) or not hmac.compare_digest(enviado.strip().encode(), esperado.encode()):
        return "Código de convite inválido"
    return None


def validar_perfil(data):
    nome = data.get("nome")
    tamanho = data.get("tamanho_rebanho")
    tipo = data.get("tipo_gado")
    if not isinstance(nome, str) or not nome.strip():
        return None, "Nome é obrigatório"
    if len(nome.strip()) > MAX_NAME_LENGTH:
        return None, f"O nome deve ter no máximo {MAX_NAME_LENGTH} caracteres"
    if tamanho not in TAMANHOS_REBANHO:
        return None, "Tamanho do rebanho inválido"
    if tipo not in TIPOS_GADO:
        return None, "Tipo de gado inválido"
    return {"nome": nome.strip(), "tamanho_rebanho": tamanho, "tipo_gado": tipo}, None


def validar_mensagem(texto):
    if not isinstance(texto, str) or not texto.strip():
        return None, "mensagem não fornecida"
    texto = texto.strip()
    maximo = current_app.config["MAX_MESSAGE_CHARS"]
    if len(texto) > maximo:
        return None, f"A mensagem deve ter no máximo {maximo} caracteres"
    return texto, None


def conversa_id_valido(valor):
    try:
        return str(uuid.UUID(valor)) == valor.lower()
    except (ValueError, AttributeError, TypeError):
        return False
