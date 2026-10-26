"""Conexão com o SQLite."""
import sqlite3
from contextlib import contextmanager

from flask import current_app


@contextmanager
def get_connection(path=None):
    """Abre uma conexão, faz commit ao final (ou rollback em erro) e sempre fecha."""
    conn = sqlite3.connect(path or current_app.config["DATABASE_PATH"])
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
