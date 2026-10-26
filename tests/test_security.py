import pytest
from openai import APIConnectionError

from api.services.llm import create_llm
from conftest import login, register, register_and_login


def send(client, mensagem="Como alimentar bezerros?", **extra):
    return client.post("/mensagem", json={"mensagem": mensagem, **extra})


# ---------- Regression: user A must never read user B's data ----------

def test_user_cannot_read_other_users_history_or_conversations(make_client):
    alice, bob = make_client(), make_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")

    resp = send(bob, "Pergunta secreta do Bob")
    assert resp.status_code == 200
    bob_conversa = resp.get_json()["conversa_id"]

    # Alice asks for Bob's conversation explicitly, and also tries the old
    # client-supplied session_id parameter/header with Bob's numeric ID.
    for query in (
        f"/historico?conversa_id={bob_conversa}",
        f"/historico?conversa_id={bob_conversa}&session_id=2",
        "/historico?session_id=2",
    ):
        data = alice.get(query, headers={"X-Session-Id": "2"}).get_json()
        assert data["historico"] == []

    data = alice.get("/conversas?session_id=2", headers={"X-Session-Id": "2"}).get_json()
    assert data["conversas"] == []

    # An anonymous client supplying Bob's ID gets nothing either.
    anonymous = make_client()
    for query in (f"/historico?conversa_id={bob_conversa}&session_id=2", "/conversas?session_id=2"):
        resp = anonymous.get(query, headers={"X-Session-Id": "2"})
        assert resp.status_code == 401
        assert not resp.get_json().get("historico") and not resp.get_json().get("conversas")

    # Bob still sees his own data.
    assert len(bob.get(f"/historico?conversa_id={bob_conversa}").get_json()["historico"]) == 1
    assert len(bob.get("/conversas").get_json()["conversas"]) == 1


def test_message_cannot_be_attributed_to_another_user(make_client, fake_llm):
    alice, bob = make_client(), make_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")

    # Old exploit: send session_id of another user in the body.
    assert send(alice, "Oi", session_id="2").status_code == 200
    assert bob.get("/conversas").get_json()["conversas"] == []
    assert len(alice.get("/conversas").get_json()["conversas"]) == 1


def test_cannot_continue_another_users_conversation(make_client, fake_llm):
    alice, bob = make_client(), make_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")
    bob_conversa = send(bob, "Segredo do Bob").get_json()["conversa_id"]

    # Alice reuses Bob's conversa_id: Bob's messages must not reach the model.
    assert send(alice, "Oi", conversa_id=bob_conversa).status_code == 200
    sent = " ".join(m.content for m in fake_llm.calls[-1])
    assert "Segredo do Bob" not in sent
    assert len(bob.get(f"/historico?conversa_id={bob_conversa}").get_json()["historico"]) == 1


# ---------- Authentication required ----------

@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/historico"),
        ("get", "/conversas"),
        ("post", "/mensagem"),
        ("post", "/logout"),
        ("get", "/me"),
    ],
)
def test_protected_routes_require_authentication(client, fake_llm, method, path):
    kwargs = {"json": {"mensagem": "oi", "session_id": "1"}} if method == "post" else {}
    resp = getattr(client, method)(f"{path}?session_id=1", headers={"X-Session-Id": "1"}, **kwargs)
    assert resp.status_code == 401
    assert fake_llm.calls == []


def test_logout_ends_session(client):
    register_and_login(client)
    assert client.get("/me").status_code == 200
    assert client.post("/logout").status_code == 200
    assert client.get("/historico").status_code == 401


def test_login_does_not_return_user_id(client):
    register(client)
    data = login(client).get_json()
    assert "session_id" not in data


def test_session_cookie_is_httponly(client):
    register(client)
    cookie = login(client).headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


# ---------- Input validation ----------

@pytest.mark.parametrize(
    "payload",
    [
        {"email": "sem-arroba", "senha": "senha-segura-1"},
        {"email": "a@b", "senha": "senha-segura-1"},
        {"email": "a@example.com", "senha": "curta"},
        {"email": "a@example.com", "senha": "x" * 200},
        {"email": "a@example.com"},
        {"email": 123, "senha": "senha-segura-1"},
    ],
)
def test_register_rejects_invalid_input(client, payload):
    assert client.post("/register", json=payload).status_code == 400


def test_register_rejects_non_json(client):
    resp = client.post("/register", data="email=a@example.com&senha=senha-segura-1")
    assert resp.status_code == 400


def test_register_duplicate_email(client):
    assert register(client).status_code == 201
    assert register(client).status_code == 409


def test_login_wrong_password(client):
    register(client)
    assert login(client, senha="senha-errada-1").status_code == 401
    assert login(client, email="ninguem@example.com").status_code == 401


def test_message_length_limit(app, client, fake_llm):
    register_and_login(client)
    assert send(client, "x" * (app.config["MAX_MESSAGE_CHARS"] + 1)).status_code == 400
    assert send(client, "   ").status_code == 400
    assert fake_llm.calls == []
    assert send(client, "x" * app.config["MAX_MESSAGE_CHARS"]).status_code == 200


def test_invalid_conversa_id_rejected(client, fake_llm):
    register_and_login(client)
    assert send(client, conversa_id="../../etc").status_code == 400
    assert fake_llm.calls == []


# ---------- Rate limiting ----------

def test_login_rate_limited(client):
    register(client)
    codes = [login(client, senha="senha-errada-1").status_code for _ in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429
    assert "erro" in login(client).get_json()


def test_message_rate_limited_per_user(make_client, fake_llm):
    alice, bob = make_client(), make_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")

    codes = [send(alice).status_code for _ in range(11)]
    assert codes[:10] == [200] * 10
    assert codes[10] == 429
    # Another user is not affected.
    assert send(bob).status_code == 200
    assert len(fake_llm.calls) == 11


# ---------- LLM errors ----------

def test_llm_error_returns_friendly_message(client, fake_llm):
    register_and_login(client)
    fake_llm.error = APIConnectionError(request=None)
    resp = send(client)
    assert resp.status_code == 502
    body = resp.get_json()
    assert "indisponível" in body["erro"]
    assert "Connection" not in body["erro"]


def test_llm_has_cost_limits_and_unchanged_model(app):
    llm = create_llm(app.config["LLM_MAX_TOKENS"])
    assert llm.model_name == "gpt-4o-mini"
    assert llm.temperature == 0.7
    assert llm.max_tokens == app.config["LLM_MAX_TOKENS"] == 1024
