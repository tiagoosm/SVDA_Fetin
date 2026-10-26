import os

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

# Dummy key and unroutable base URL: a real OpenAI call can never succeed from tests.
os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:9/v1"
os.environ["APP_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key"

from api import create_app  # noqa: E402
from api.extensions import limiter  # noqa: E402


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
def fake_llm():
    return FakeLLM()


@pytest.fixture
def make_app(tmp_path, fake_llm):
    def factory(**overrides):
        config = {"TESTING": True, "DATABASE_PATH": str(tmp_path / "test.db"), **overrides}
        return create_app(config, llm=fake_llm.runnable)

    return factory


@pytest.fixture
def app(make_app):
    app = make_app()
    limiter.reset()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_client(app):
    return app.test_client


PERFIL = {"nome": "Produtor Teste", "tamanho_rebanho": "Pequeno", "tipo_gado": "Leite"}


def register(client, email="a@example.com", senha="senha-segura-1", **perfil):
    return client.post("/register", json={"email": email, "senha": senha, **PERFIL, **perfil})


def login(client, email="a@example.com", senha="senha-segura-1"):
    return client.post("/login", json={"email": email, "senha": senha})


def register_and_login(client, email="a@example.com", senha="senha-segura-1"):
    assert register(client, email, senha).status_code == 201
    assert login(client, email, senha).status_code == 200
