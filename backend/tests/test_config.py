import os

import pytest

from app import create_app
from app.config import BASE_DIR, load_config


@pytest.fixture
def production_env(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "k")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "prod.db"))
    for name in ("CORS_ORIGINS", "SESSION_COOKIE_SAMESITE", "SESSION_COOKIE_SECURE"):
        monkeypatch.delenv(name, raising=False)


def test_production_requires_secret_key(production_env, monkeypatch):
    monkeypatch.delenv("SECRET_KEY")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()


def test_wildcard_cors_rejected(production_env, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        create_app()


def test_samesite_none_requires_secure(production_env, monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "None")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    with pytest.raises(RuntimeError, match="SESSION_COOKIE_SECURE"):
        create_app()


def test_production_defaults_are_safe(production_env):
    app = create_app()
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["CORS_ORIGINS"] == []
    assert app.debug is False


def test_cors_allowlist(production_env, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://svda.example.com")
    client = create_app().test_client()
    allowed = client.get("/health", headers={"Origin": "https://svda.example.com"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "https://svda.example.com"
    assert allowed.headers.get("Access-Control-Allow-Credentials") == "true"
    denied = client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert "Access-Control-Allow-Origin" not in denied.headers


def test_relative_database_path_is_resolved_from_project_root(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "data/svda.db")
    assert load_config()["DATABASE_PATH"] == os.path.join(BASE_DIR, "data", "svda.db")


def test_proxy_fix_uses_forwarded_client_ip(production_env, monkeypatch):
    monkeypatch.setenv("PROXY_FIX_X_FOR", "1")
    app = create_app()

    @app.route("/ip")
    def ip():
        from flask import request

        return request.remote_addr

    resp = app.test_client().get("/ip", headers={"X-Forwarded-For": "203.0.113.9"})
    assert resp.get_data(as_text=True) == "203.0.113.9"
