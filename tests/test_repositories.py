import sqlite3

import pytest

from api.db import repositories as repo


def make_user(app, email="u@example.com"):
    with app.app_context():
        repo.create_user(email, "hash", "Nome", "Pequeno", "Leite")
        return repo.get_credentials(email)[0]


def test_create_and_read_user(app):
    uid = make_user(app)
    with app.app_context():
        assert repo.get_credentials("u@example.com") == (uid, "hash")
        assert repo.get_credentials("outro@example.com") is None
        user = repo.get_user(uid)
        assert user == {
            "usuario_id": uid,
            "email": "u@example.com",
            "nome": "Nome",
            "tamanho_rebanho": "Pequeno",
            "tipo_gado": "Leite",
        }
        assert "senha" not in user
        assert repo.get_user(999) is None


def test_duplicate_email_raises_integrity_error(app):
    make_user(app)
    with app.app_context(), pytest.raises(sqlite3.IntegrityError):
        repo.create_user("u@example.com", "hash", "N", "Pequeno", "Leite")


def test_history_is_scoped_by_user_and_conversation(app):
    a, b = make_user(app, "a@example.com"), make_user(app, "b@example.com")
    with app.app_context():
        repo.add_message(a, "c1", "p1", "r1")
        repo.add_message(a, "c1", "p2", "r2")
        repo.add_message(a, "c2", "p3", "r3")
        repo.add_message(b, "c1", "pb", "rb")

        assert [(p, r) for p, r, _ in repo.get_history(a, "c1")] == [("p1", "r1"), ("p2", "r2")]
        assert [p for p, _, _ in repo.get_history(a)] == ["p1", "p2", "p3"]
        assert [p for p, _, _ in repo.get_history(b, "c1")] == ["pb"]
        assert repo.get_history(b, "c2") == []

        assert repo.recent_turns(a, "c1", 1) == [("p2", "r2")]
        assert repo.recent_turns(a, "c1", 5) == [("p1", "r1"), ("p2", "r2")]

        convs = repo.list_conversations(a)
        assert [(c[0], c[1]) for c in convs] == [("c2", "p3"), ("c1", "p1")]
        assert [c[0] for c in repo.list_conversations(b)] == ["c1"]


def test_connection_rolls_back_on_error(app):
    uid = make_user(app)
    with app.app_context():
        with pytest.raises(RuntimeError), repo.get_connection() as conn:
            conn.execute(
                "INSERT INTO historico (usuario_id, conversa_id, pergunta, resposta) VALUES (?, 'c', 'p', 'r')", (uid,)
            )
            raise RuntimeError("boom")
        assert repo.get_history(uid) == []
