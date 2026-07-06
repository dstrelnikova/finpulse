import pytest

from app.infrastructure.security.auth_jwt import create_refresh_token


@pytest.mark.integration
def test_register_login_logout_flow(client, fake_user_repo):
    reg = client.post(
        "/auth/register",
        json={"name": "New User", "email": "new@example.com", "password": "123456"},
    )
    assert reg.status_code == 200
    assert reg.json()["email"] == "new@example.com"

    login = client.post(
        "/auth/login",
        json={"email": "new@example.com", "password": "123456"},
    )
    assert login.status_code == 200
    payload = login.json()
    assert payload["access_token"]
    assert payload["refresh_token"]

    me = client.get("/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200

    out = client.post("/auth/logout", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert out.status_code == 200
    u = fake_user_repo.get_by_email("new@example.com")
    assert u is not None
    assert fake_user_repo.get_by_refresh_token(payload["refresh_token"]) is None


@pytest.mark.integration
def test_register_duplicate_email_returns_400(client):
    first = client.post("/auth/register", json={"name": "AA", "email": "dup@x.com", "password": "123456"})
    assert first.status_code == 200

    second = client.post("/auth/register", json={"name": "BB", "email": "dup@x.com", "password": "123456"})
    assert second.status_code == 400


@pytest.mark.integration
def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={"name": "A", "email": "u@x.com", "password": "123456"})
    bad = client.post("/auth/login", json={"email": "u@x.com", "password": "badbad"})
    assert bad.status_code == 401


@pytest.mark.integration
def test_refresh_returns_new_tokens_when_refresh_is_valid(client, fake_user_repo, future_expiry):
    u = fake_user_repo.get_by_email("user@example.com")
    assert u is not None
    refresh_token, _ = create_refresh_token(u.id, u.email)
    fake_user_repo.update_refresh_token(u.id, refresh_token, future_expiry)

    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.integration
def test_refresh_returns_401_when_token_expired(client, fake_user_repo, past_expiry):
    u = fake_user_repo.get_by_email("user@example.com")
    assert u is not None
    refresh_token, _ = create_refresh_token(u.id, u.email)
    fake_user_repo.update_refresh_token(u.id, refresh_token, past_expiry)

    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 401
    assert res.json()["detail"] == "Refresh token expired"
