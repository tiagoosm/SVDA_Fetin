"""Extensões Flask compartilhadas entre os blueprints."""

from flask import session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def rate_limit_user_key():
    # Usuário autenticado é limitado pelo ID; sem sessão, pelo IP
    user_id = session.get("user_id")
    return f"user:{user_id}" if user_id else get_remote_address()
