import sqlite3

import pytest

from app.db import repositories as repo


def make_user(app, email="u@example.com"):
    with app.app_context():
        repo.create_user(email, "hash", "Nome", "small", "dairy")
        return repo.get_credentials(email)[0]


def test_create_and_read_user(app):
    user_id = make_user(app)
    with app.app_context():
        assert repo.get_credentials("u@example.com") == (user_id, "hash")
        assert repo.get_credentials("other@example.com") is None
        user = repo.get_user(user_id)
        assert user == {
            "id": user_id,
            "email": "u@example.com",
            "name": "Nome",
            "herd_size": "small",
            "cattle_type": "dairy",
        }
        assert "password_hash" not in user
        assert repo.get_user(999) is None


def test_duplicate_email_raises_integrity_error(app):
    make_user(app)
    with app.app_context(), pytest.raises(sqlite3.IntegrityError):
        repo.create_user("u@example.com", "hash", "N", "small", "dairy")


def test_messages_are_scoped_by_user_and_conversation(app):
    a, b = make_user(app, "a@example.com"), make_user(app, "b@example.com")
    with app.app_context():
        repo.add_message(a, "c1", "p1", "r1")
        repo.add_message(a, "c1", "p2", "r2")
        repo.add_message(a, "c2", "p3", "r3")
        repo.add_message(b, "c1", "pb", "rb")

        assert [(q, ans) for q, ans, _ in repo.get_conversation_messages(a, "c1")] == [("p1", "r1"), ("p2", "r2")]
        assert [q for q, _, _ in repo.get_conversation_messages(b, "c1")] == ["pb"]
        assert repo.get_conversation_messages(b, "c2") == []

        assert repo.recent_turns(a, "c1", 1) == [("p2", "r2")]
        assert repo.recent_turns(a, "c1", 5) == [("p1", "r1"), ("p2", "r2")]

        conversations = repo.list_conversations(a)
        assert [(c[0], c[1]) for c in conversations] == [("c2", "p3"), ("c1", "p1")]
        assert [c[0] for c in repo.list_conversations(b)] == ["c1"]


def test_connection_rolls_back_on_error(app):
    user_id = make_user(app)
    with app.app_context():
        with pytest.raises(RuntimeError), repo.get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (user_id, conversation_id, question, answer) VALUES (?, 'c', 'p', 'r')",
                (user_id,),
            )
            raise RuntimeError("boom")
        assert repo.get_conversation_messages(user_id, "c") == []
