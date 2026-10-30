def test_frontend_not_served_by_default(client):
    assert client.get("/").get_data(as_text=True) == "Servidor rodando!"
    assert client.get("/index.html").status_code == 404
    assert client.get("/healthz").get_data(as_text=True) == "ok"


def test_frontend_served_when_enabled(make_app):
    client = make_app(SERVE_FRONTEND=True).test_client()
    assert "<form" in client.get("/").get_data(as_text=True)
    assert client.get("/cadastro.html").status_code == 200
    assert client.get("/style.css").mimetype == "text/css"
    assert client.get("/healthz").get_data(as_text=True) == "ok"

    config = client.get("/config.js")
    assert config.mimetype == "text/javascript"
    assert "API_BASE: ''" in config.get_data(as_text=True)


def test_frontend_serving_does_not_break_the_api_or_leak_files(make_app):
    client = make_app(SERVE_FRONTEND=True).test_client()
    assert client.get("/conversas").status_code == 401  # API route wins over files
    assert client.get("/nao-existe.html").is_json
    for path in ("/../api/config.py", "/..%2fapi%2fconfig.py", "/%2e%2e/.env"):
        assert client.get(path).status_code == 404
