import json
import logging

import httpx
import pytest
from openai import APITimeoutError, AuthenticationError, RateLimitError

from app import create_app
from app.logging_config import JsonFormatter
from conftest import register_and_login, send


def _status_error(cls, status):
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx.Response(status, request=request, text="SECRET-PROVIDER-DETAIL sk-live-123")
    return cls("SECRET-PROVIDER-DETAIL sk-live-123", response=response, body=None)


@pytest.mark.parametrize(
    "error,status,fragment",
    [
        (_status_error(RateLimitError, 429), 503, "ocupado"),
        (APITimeoutError(request=httpx.Request("POST", "https://api.openai.com")), 503, "ocupado"),
        (_status_error(AuthenticationError, 401), 502, "indisponível"),
    ],
)
def test_llm_errors_become_friendly_messages_without_leaks(client, fake_llm, error, status, fragment):
    register_and_login(client)
    fake_llm.error = error
    resp = send(client)
    assert resp.status_code == status
    body = resp.get_data(as_text=True)
    assert fragment in resp.get_json()["error"]
    assert "SECRET-PROVIDER-DETAIL" not in body and "sk-live" not in body
    # The failed question is not stored as history
    assert client.get("/conversations").get_json()["conversations"] == []


def test_unexpected_error_returns_generic_json_500(app, client, fake_llm):
    register_and_login(client)
    app.config["PROPAGATE_EXCEPTIONS"] = False
    fake_llm.error = RuntimeError("database password is hunter2")
    resp = send(client)
    assert resp.status_code == 500
    assert resp.is_json
    assert "hunter2" not in resp.get_data(as_text=True)
    assert resp.get_json()["error"].startswith("Erro interno")


@pytest.mark.parametrize(
    "method,path,status",
    [("get", "/nao-existe", 404), ("get", "/auth/login", 405), ("delete", "/conversations", 405)],
)
def test_http_errors_are_json(client, method, path, status):
    resp = getattr(client, method)(path)
    assert resp.status_code == status
    assert resp.is_json and "error" in resp.get_json()


def test_malformed_json_is_rejected_as_json(client):
    resp = client.post("/auth/login", data="{nao é json", content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Requisição inválida"}


def test_request_is_logged_without_message_content(client, caplog):
    register_and_login(client)
    with caplog.at_level(logging.INFO, logger="svda.request"):
        send(client, "texto privado do produtor")
    record = next(r for r in caplog.records if r.path.endswith("/messages"))
    assert record.status == 200 and record.user_id == 1 and record.duration_ms >= 0
    assert "texto privado" not in caplog.text


def test_request_id_header(client):
    assert client.get("/health", headers={"X-Request-Id": "abc123"}).headers["X-Request-Id"] == "abc123"
    assert client.get("/health").headers["X-Request-Id"]


def test_json_formatter_outputs_one_json_object():
    record = logging.LogRecord("svda.request", logging.INFO, __file__, 1, "GET /x -> 200", None, None)
    record.status = 200
    record.user_id = 7
    data = json.loads(JsonFormatter().format(record))
    assert data["message"] == "GET /x -> 200" and data["status"] == 200 and data["user_id"] == 7


def test_json_log_format_is_configurable(monkeypatch, tmp_path):
    monkeypatch.setenv("LOG_FORMAT", "json")
    monkeypatch.setenv("APP_ENV", "testing")
    create_app({"DATABASE_PATH": str(tmp_path / "x.db")})
    assert isinstance(logging.getLogger().handlers[0].formatter, JsonFormatter)
    monkeypatch.setenv("LOG_FORMAT", "text")
    create_app({"DATABASE_PATH": str(tmp_path / "x.db")})
