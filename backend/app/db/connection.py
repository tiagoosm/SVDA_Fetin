"""SQLite connection handling."""

import sqlite3
from contextlib import contextmanager

from flask import current_app


@contextmanager
def get_connection(path=None):
    """Open a connection; commit on success, roll back on error, always close."""
    conn = sqlite3.connect(path or current_app.config["DATABASE_PATH"])
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
