import os
import sys
import tempfile
from types import SimpleNamespace

import pytest

# Environment must be set before the app module is imported.
_TMP_DIR = tempfile.mkdtemp(prefix="svda-tests-")
os.environ["APP_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_PATH"] = os.path.join(_TMP_DIR, "import.db")
# Dummy key and unroutable base URL: a real OpenAI call can never succeed from tests.
os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:9/v1"

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "api"))

import main  # noqa: E402


class FakeChain:
    """Stands in for the LLM chain; records every call."""

    def __init__(self, reply="Resposta de teste"):
        self.reply = reply
        self.calls = []
        self.error = None

    def invoke(self, inputs, config=None):
        self.calls.append((inputs, config))
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.reply)


@pytest.fixture
def app(tmp_path, monkeypatch):
    main.app.config.update(TESTING=True, DATABASE_PATH=str(tmp_path / "test.db"))
    main.init_db()
    main.store.clear()
    main.limiter.reset()
    yield main.app


@pytest.fixture
def fake_chain(monkeypatch):
    chain = FakeChain()
    monkeypatch.setattr(main, "chain_with_history", chain)
    return chain


@pytest.fixture
def client(app, fake_chain):
    return app.test_client()


@pytest.fixture
def make_client(app, fake_chain):
    return app.test_client


def register(client, email="a@example.com", senha="senha-segura-1"):
    return client.post("/register", json={"email": email, "senha": senha})


def login(client, email="a@example.com", senha="senha-segura-1"):
    return client.post("/login", json={"email": email, "senha": senha})


def register_and_login(client, email="a@example.com", senha="senha-segura-1"):
    assert register(client, email, senha).status_code == 201
    assert login(client, email, senha).status_code == 200
