import os
import uuid

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

# Dummy key and unroutable base URL: a real OpenAI call can never succeed from tests.
os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:9/v1"
os.environ["APP_ENV"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key"

from app import create_app  # noqa: E402
from app.extensions import limiter  # noqa: E402


class FakeLLM:
    """Stands in for ChatOpenAI; records the exact messages sent to the model."""

    def __init__(self, reply="Resposta de teste"):
        self.reply = reply
        self.calls = []
        self.error = None
        self.finish_reason = "stop"
        self.runnable = RunnableLambda(self._invoke)

    def _invoke(self, prompt_value):
        self.calls.append(prompt_value.to_messages())
        if self.error:
            raise self.error
        return AIMessage(content=self.reply, response_metadata={"finish_reason": self.finish_reason})


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
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_client(app):
    return app.test_client


PROFILE = {"name": "Produtor Teste", "herd_size": "small", "cattle_type": "dairy"}


def register(client, email="a@example.com", password="senha-segura-1", **fields):
    return client.post("/auth/register", json={"email": email, "password": password, **PROFILE, **fields})


def login(client, email="a@example.com", password="senha-segura-1"):
    return client.post("/auth/login", json={"email": email, "password": password})


def register_and_login(client, email="a@example.com", password="senha-segura-1"):
    assert register(client, email, password).status_code == 201
    assert login(client, email, password).status_code == 200


def send(client, message="Como alimentar bezerros?", conversation_id=None, **extra):
    """Send a message; a new conversation id is generated when none is given."""
    conversation_id = conversation_id or str(uuid.uuid4())
    return client.post(f"/conversations/{conversation_id}/messages", json={"message": message, **extra})


def conversation_messages(client, conversation_id):
    return client.get(f"/conversations/{conversation_id}/messages").get_json()["messages"]
