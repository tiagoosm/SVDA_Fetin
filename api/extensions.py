"""Extensões Flask compartilhadas entre os blueprints."""

from flask import session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def rate_limit_user_key():
    # Usuário autenticado é limitado pelo ID; sem sessão, pelo IP
    usuario_id = session.get("usuario_id")
    return f"user:{usuario_id}" if usuario_id else get_remote_address()
