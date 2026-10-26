import os
import sys
import tempfile
import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

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


class FakeLLM:
    """Stands in for ChatOpenAI; records the exact messages sent to the model."""

    def __init__(self, reply="Resposta de teste"):
        self.reply = reply
        self.calls = []
        self.error = None
        self.runnable = RunnableLambda(self._invoke)

    def _invoke(self, prompt_value):
        self.calls.append(prompt_value.to_messages())
        if self.error:
            raise self.error
        return AIMessage(content=self.reply)


@pytest.fixture
def app(tmp_path, monkeypatch):
    main.app.config.update(TESTING=True, DATABASE_PATH=str(tmp_path / "test.db"))
    main.init_db()
    main.limiter.reset()
    yield main.app


@pytest.fixture
def fake_llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(main, "llm", fake.runnable)
    return fake


@pytest.fixture
def client(app, fake_llm):
    return app.test_client()


@pytest.fixture
def make_client(app, fake_llm):
    return app.test_client


PERFIL = {"nome": "Produtor Teste", "tamanho_rebanho": "Pequeno", "tipo_gado": "Leite"}


def register(client, email="a@example.com", senha="senha-segura-1", **perfil):
    return client.post("/register", json={"email": email, "senha": senha, **PERFIL, **perfil})


def login(client, email="a@example.com", senha="senha-segura-1"):
    return client.post("/login", json={"email": email, "senha": senha})


def register_and_login(client, email="a@example.com", senha="senha-segura-1"):
    assert register(client, email, senha).status_code == 201
    assert login(client, email, senha).status_code == 200
