"""Criação e migração do schema."""

import logging
import os

from .connection import get_connection

logger = logging.getLogger(__name__)

PROFILE_COLUMNS = ("nome", "tamanho_rebanho", "tipo_gado")


def init_db(path):
    """Cria as tabelas caso ainda não existam e migra bancos antigos (idempotente)."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with get_connection(path) as conn:
        cursor = conn.cursor()

        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                nome TEXT,
                tamanho_rebanho TEXT,
                tipo_gado TEXT
            )
        """)

        # Migração para bancos criados antes dos campos de perfil
        colunas = {row[1] for row in cursor.execute("PRAGMA table_info(usuarios)")}
        for coluna in PROFILE_COLUMNS:
            if coluna not in colunas:
                cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {coluna} TEXT")
                logger.info("Database migrated: added usuarios.%s", coluna)

        # Tabela de histórico de conversas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                conversa_id TEXT,
                pergunta TEXT,
                resposta TEXT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)
