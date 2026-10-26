"""Ponto de entrada WSGI para servidores de produção (ex.: gunicorn wsgi:app)."""

from api import create_app

app = create_app()
