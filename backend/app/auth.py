"""Session-based authentication. The user always comes from the signed session, never from the client."""

from functools import wraps

from flask import g, jsonify, session


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            return jsonify({"error": "Usuário não autenticado"}), 401
        g.user_id = user_id
        return view(*args, **kwargs)

    return wrapper
