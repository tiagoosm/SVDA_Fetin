"""Schema creation and migrations. Everything here is idempotent."""

import logging
import os

from .connection import get_connection

logger = logging.getLogger(__name__)

# Legacy (Portuguese) schema -> current schema.
LEGACY_TABLES = {"usuarios": "users", "historico": "messages"}
LEGACY_COLUMNS = {
    "users": {
        "senha": "password_hash",
        "nome": "name",
        "tamanho_rebanho": "herd_size",
        "tipo_gado": "cattle_type",
    },
    "messages": {
        "usuario_id": "user_id",
        "conversa_id": "conversation_id",
        "pergunta": "question",
        "resposta": "answer",
        "data": "created_at",
    },
}
LEGACY_VALUES = {
    "herd_size": {"Pequeno": "small", "Médio": "medium", "Grande": "large"},
    "cattle_type": {"Leite": "dairy", "Corte": "beef", "Outro": "other"},
}
PROFILE_COLUMNS = ("name", "herd_size", "cattle_type")


def _tables(cursor):
    return {row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def _columns(cursor, table):
    return {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}


def migrate_legacy_schema(cursor):
    """Rename the Portuguese tables, columns and values of older databases."""
    tables = _tables(cursor)
    for old, new in LEGACY_TABLES.items():
        if old in tables and new not in tables:
            cursor.execute(f"ALTER TABLE {old} RENAME TO {new}")
            logger.info("Database migrated: renamed table %s to %s", old, new)
        # An old database may hold the new table too only if it was half-migrated; leave it alone.

    for table, mapping in LEGACY_COLUMNS.items():
        if table not in _tables(cursor):
            continue
        existing = _columns(cursor, table)
        for old, new in mapping.items():
            if old in existing and new not in existing:
                cursor.execute(f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}")
                logger.info("Database migrated: renamed %s.%s to %s", table, old, new)

    if "users" in _tables(cursor):
        existing = _columns(cursor, "users")
        for column, mapping in LEGACY_VALUES.items():
            if column in existing:
                cases = " ".join(f"WHEN '{old}' THEN '{new}'" for old, new in mapping.items())
                cursor.execute(f"UPDATE users SET {column} = CASE {column} {cases} ELSE {column} END")


def init_db(path):
    """Create the tables if missing and migrate older databases."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with get_connection(path) as conn:
        cursor = conn.cursor()
        migrate_legacy_schema(cursor)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                herd_size TEXT,
                cattle_type TEXT
            )
        """)

        # Databases created before the profile fields existed
        existing = _columns(cursor, "users")
        for column in PROFILE_COLUMNS:
            if column not in existing:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
                logger.info("Database migrated: added users.%s", column)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                conversation_id TEXT,
                question TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_user_conversation ON messages (user_id, conversation_id)"
        )
