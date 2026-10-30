import sqlite3
from contextlib import closing

from app.db.schema import init_db

LEGACY_V1 = """
CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, senha TEXT NOT NULL);
CREATE TABLE historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, conversa_id TEXT, pergunta TEXT, resposta TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
INSERT INTO usuarios (email, senha) VALUES ('old@example.com', 'hash');
INSERT INTO historico (usuario_id, conversa_id, pergunta, resposta) VALUES (1, 'c1', 'pergunta', 'resposta');
"""

LEGACY_V2 = """
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, senha TEXT NOT NULL,
    nome TEXT, tamanho_rebanho TEXT, tipo_gado TEXT
);
CREATE TABLE historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, conversa_id TEXT, pergunta TEXT, resposta TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
INSERT INTO usuarios (email, senha, nome, tamanho_rebanho, tipo_gado) VALUES ('a@example.com', 'h1', 'Ana', 'Médio', 'Corte');
INSERT INTO usuarios (email, senha, nome, tamanho_rebanho, tipo_gado) VALUES ('b@example.com', 'h2', 'Bia', 'Pequeno', 'Leite');
INSERT INTO usuarios (email, senha, nome, tamanho_rebanho, tipo_gado) VALUES ('c@example.com', 'h3', 'Cris', 'Grande', 'Outro');
INSERT INTO historico (usuario_id, conversa_id, pergunta, resposta) VALUES (1, 'c1', 'p1', 'r1');
"""


def build(path, script):
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.executescript(script)


def rows(path, sql):
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute(sql).fetchall()


def columns(path, table):
    return [row[1] for row in rows(path, f"PRAGMA table_info({table})")]


def test_fresh_database_has_the_current_schema(tmp_path):
    path = str(tmp_path / "new.db")
    init_db(path)
    assert columns(path, "users") == ["id", "email", "password_hash", "name", "herd_size", "cattle_type"]
    assert columns(path, "messages") == ["id", "user_id", "conversation_id", "question", "answer", "created_at"]


def test_migrates_the_original_portuguese_schema_keeping_the_data(tmp_path):
    path = str(tmp_path / "legacy.db")
    build(path, LEGACY_V1)
    init_db(path)

    assert columns(path, "users") == ["id", "email", "password_hash", "name", "herd_size", "cattle_type"]
    assert rows(path, "SELECT email, password_hash, name, herd_size, cattle_type FROM users") == [
        ("old@example.com", "hash", None, None, None)
    ]
    assert rows(path, "SELECT user_id, conversation_id, question, answer FROM messages") == [
        (1, "c1", "pergunta", "resposta")
    ]


def test_migrates_profile_values_to_codes(tmp_path):
    path = str(tmp_path / "legacy2.db")
    build(path, LEGACY_V2)
    init_db(path)

    assert rows(path, "SELECT name, herd_size, cattle_type FROM users ORDER BY id") == [
        ("Ana", "medium", "beef"),
        ("Bia", "small", "dairy"),
        ("Cris", "large", "other"),
    ]
    assert rows(path, "SELECT question FROM messages") == [("p1",)]


def test_migration_is_idempotent(tmp_path):
    path = str(tmp_path / "legacy3.db")
    build(path, LEGACY_V2)
    init_db(path)
    first = rows(path, "SELECT * FROM users ORDER BY id")
    init_db(path)
    init_db(path)
    assert rows(path, "SELECT * FROM users ORDER BY id") == first
    assert rows(path, "SELECT COUNT(*) FROM messages") == [(1,)]


def test_foreign_key_still_points_to_users(tmp_path):
    path = str(tmp_path / "legacy4.db")
    build(path, LEGACY_V2)
    init_db(path)
    assert [row[2] for row in rows(path, "PRAGMA foreign_key_list(messages)")] == ["users"]
