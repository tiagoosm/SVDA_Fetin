import pytest
from openai import APIConnectionError

from app.services.llm import create_llm
from conftest import conversation_messages, login, register, register_and_login, send

# ---------- Regression: user A must never read user B's data ----------


def test_user_cannot_read_other_users_conversations(make_client):
    alice, bob = make_client(), make_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")

    bob_conversation = send(bob, "Pergunta secreta do Bob").get_json()["conversation_id"]

    # Alice asks for Bob's conversation explicitly, and also tries the old
    # client-supplied session_id parameter/header with Bob's numeric ID.
    for query in ("", "?session_id=2"):
        response = alice.get(f"/conversations/{bob_conversation}/messages{query}", headers={"X-Session-Id": "2"})
        assert response.get_json()["messages"] == []
    assert alice.get("/conversations?session_id=2", headers={"X-Session-Id": "2"}).get_json()["conversations"] == []

    # An anonymous client supplying Bob's ID gets nothing either.
    anonymous = make_client()
    for path in (f"/conversations/{bob_conversation}/messages?session_id=2", "/conversations?session_id=2"):
        response = anonymous.get(path, headers={"X-Session-Id": "2"})
        assert response.status_code == 401
        assert not response.get_json().get("messages") and not response.get_json().get("conversations")

    # Bob still sees his own data.
    assert len(conversation_messages(bob, bob_conversation)) == 1
    assert len(bob.get("/conversations").get_json()["conversations"]) == 1


def test_message_cannot_be_attributed_to_another_user(make_client):
    alice, bob = make_client(), make_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")

    # Old exploit: send the id of another user in the body.
    assert send(alice, "Oi", session_id="2", user_id=2).status_code == 200
    assert bob.get("/conversations").get_json()["conversations"] == []
    assert len(alice.get("/conversations").get_json()["conversations"]) == 1


def test_cannot_continue_another_users_conversation(make_client, fake_llm):
    alice, bob = make_client(), make_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")
    bob_conversation = send(bob, "Segredo do Bob").get_json()["conversation_id"]

    # Alice reuses Bob's conversation id: Bob's messages must not reach the model.
    assert send(alice, "Oi", conversation_id=bob_conversation).status_code == 200
    sent = " ".join(m.content for m in fake_llm.calls[-1])
    assert "Segredo do Bob" not in sent
    assert len(conversation_messages(bob, bob_conversation)) == 1


# ---------- Authentication required ----------

A_CONVERSATION = "5f6c1a0e-0a53-4f0a-8d10-7e2d9f6d2b11"


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/conversations"),
        ("get", f"/conversations/{A_CONVERSATION}/messages"),
        ("post", f"/conversations/{A_CONVERSATION}/messages"),
        ("post", "/auth/logout"),
        ("get", "/auth/me"),
    ],
)
def test_protected_routes_require_authentication(client, fake_llm, method, path):
    kwargs = {"json": {"message": "oi"}} if method == "post" else {}
    response = getattr(client, method)(f"{path}?session_id=1", headers={"X-Session-Id": "1"}, **kwargs)
    assert response.status_code == 401
    assert fake_llm.calls == []


# ---------- Input validation ----------


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "sem-arroba", "password": "senha-segura-1"},
        {"email": "a@b", "password": "senha-segura-1"},
        {"email": "a@example.com", "password": "curta"},
        {"email": "a@example.com", "password": "x" * 200},
        {"email": "a@example.com"},
        {"email": 123, "password": "senha-segura-1"},
    ],
)
def test_register_rejects_invalid_input(client, payload):
    assert client.post("/auth/register", json=payload).status_code == 400


def test_register_rejects_non_json(client):
    response = client.post("/auth/register", data="email=a@example.com&password=senha-segura-1")
    assert response.status_code == 400


def test_message_length_limit(app, client, fake_llm):
    register_and_login(client)
    assert send(client, "x" * (app.config["MAX_MESSAGE_CHARS"] + 1)).status_code == 400
    assert send(client, "   ").status_code == 400
    assert fake_llm.calls == []
    assert send(client, "x" * app.config["MAX_MESSAGE_CHARS"]).status_code == 200


def test_invalid_conversation_id_rejected(client, fake_llm):
    register_and_login(client)
    assert send(client, conversation_id="not-a-uuid").status_code == 400
    assert client.get("/conversations/not-a-uuid/messages").status_code == 400
    assert fake_llm.calls == []


# ---------- Rate limiting ----------


def test_login_rate_limited(client):
    register(client)
    codes = [login(client, password="senha-errada-1").status_code for _ in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429
    assert "error" in login(client).get_json()


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


# ---------- LLM ----------


def test_llm_error_returns_friendly_message(client, fake_llm):
    register_and_login(client)
    fake_llm.error = APIConnectionError(request=None)
    response = send(client)
    assert response.status_code == 502
    error = response.get_json()["error"]
    assert "indisponível" in error
    assert "Connection" not in error


def test_llm_has_cost_limits_and_unchanged_model(app):
    llm = create_llm(app.config["LLM_MAX_TOKENS"])
    assert llm.model_name == "gpt-4o-mini"
    assert llm.temperature == 0.7
    assert llm.max_tokens == app.config["LLM_MAX_TOKENS"] == 1024


# ---------- Demo protection: invite code and global daily cap ----------


def test_invite_code_not_required_by_default(client):
    assert register(client).status_code == 201


@pytest.mark.parametrize("code", [None, "", "wrong", 123])
def test_invite_code_required_when_configured(make_app, code):
    client = make_app(INVITE_CODE="demo-secret").test_client()
    extra = {} if code is None else {"invite_code": code}
    response = register(client, **extra)
    assert response.status_code == 403
    assert response.get_json() == {"error": "Código de convite inválido"}
    assert login(client).status_code == 401  # no account was created


def test_valid_invite_code_allows_signup(make_app):
    client = make_app(INVITE_CODE="demo-secret").test_client()
    assert register(client, invite_code=" demo-secret ").status_code == 201
    assert login(client).status_code == 200


def test_daily_limit_is_global_and_skips_the_model(make_app, fake_llm):
    app = make_app(DAILY_MESSAGE_LIMIT=3)
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice@example.com")
    register_and_login(bob, "bob@example.com")

    assert [send(alice).status_code for _ in range(2)] == [200, 200]
    assert send(bob).status_code == 200  # third message of the day, from another user
    response = send(alice)
    assert response.status_code == 429
    assert "limite diário" in response.get_json()["error"]
    assert send(bob).status_code == 429
    assert len(fake_llm.calls) == 3  # blocked requests never reach the model


def test_daily_limit_ignores_previous_days(make_app):
    from app.db.connection import get_connection

    app = make_app(DAILY_MESSAGE_LIMIT=1)
    client = app.test_client()
    register_and_login(client)
    with get_connection(app.config["DATABASE_PATH"]) as conn:
        conn.execute(
            "INSERT INTO messages (user_id, conversation_id, question, answer, created_at) "
            "VALUES (1, 'x', 'p', 'r', '2000-01-01 10:00:00')"
        )
    assert send(client).status_code == 200  # yesterday's traffic does not count
    assert send(client).status_code == 429
