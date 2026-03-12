import tempfile
from pathlib import Path

import pytest
from app.dependencies import ALGORITHM, SECRET_KEY, get_auth_service, get_user_repo
from app.main import app
from app.repositories.user_repository import UserRepository
from app.services.auth_service import TOKEN_BLACKLIST, AuthService
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as temp_dir:
        users_file = Path(temp_dir) / "users.json"
        user_repo = UserRepository(users_file)
        auth_service = AuthService(
            user_repo=user_repo,
            secret_key=SECRET_KEY,
            algorithm=ALGORITHM,
        )

        TOKEN_BLACKLIST.clear()

        # override both so get_current_user uses the same repo
        app.dependency_overrides[get_auth_service] = lambda: auth_service
        app.dependency_overrides[get_user_repo] = lambda: user_repo

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()
        TOKEN_BLACKLIST.clear()


def _register(client, email, password="secret12", role="customer"):
    payload = {"email": email, "password": password, "role": role}
    if role == "owner":
        payload["restaurant_id"] = 1
    return client.post("/auth/register", json=payload)


def _login(client, email, password="secret12"):
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_customer_cannot_access_admin(client):
    _register(client, "customer@test.com", role="customer")
    token = _login(client, "customer@test.com")

    r = client.get("/auth/admin/users", headers=_headers(token))

    assert r.status_code == 403
    assert "insufficient permissions" in r.json()["detail"]


def test_owner_cannot_access_admin(client):
    _register(client, "owner@test.com", role="owner")
    token = _login(client, "owner@test.com")

    r = client.get("/auth/admin/users", headers=_headers(token))

    assert r.status_code == 403


def test_admin_can_access_admin(client):
    _register(client, "admin@test.com", role="admin")
    token = _login(client, "admin@test.com")

    r = client.get("/auth/admin/users", headers=_headers(token))

    assert r.status_code == 200


def test_admin_list_users(client):
    _register(client, "admin@test.com", role="admin")
    _register(client, "c@test.com", role="customer")
    _register(client, "o@test.com", role="owner")
    token = _login(client, "admin@test.com")

    r = client.get("/auth/admin/users", headers=_headers(token))
    users = r.json()

    assert r.status_code == 200
    assert len(users) == 3

    emails = {u["email"] for u in users}
    assert emails == {"admin@test.com", "c@test.com", "o@test.com"}

    for u in users:
        assert "id" in u
        assert "email" in u
        assert "role" in u


def test_admin_list_hides_passwords(client):
    _register(client, "admin@test.com", role="admin")
    token = _login(client, "admin@test.com")

    r = client.get("/auth/admin/users", headers=_headers(token))

    for user in r.json():
        assert "password_hash" not in user
        assert "password" not in user


def test_no_token_returns_401(client):
    r = client.get("/auth/admin/users")
    assert r.status_code == 401


def test_no_token_me_returns_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_bad_token_returns_401(client):
    r = client.get("/auth/admin/users", headers=_headers("garbage"))
    assert r.status_code == 401


def test_customer_can_access_me(client):
    _register(client, "customer@test.com", role="customer")
    token = _login(client, "customer@test.com")

    r = client.get("/auth/me", headers=_headers(token))

    assert r.status_code == 200
    assert r.json()["role"] == "customer"


def test_owner_can_access_me(client):
    _register(client, "owner@test.com", role="owner")
    token = _login(client, "owner@test.com")

    r = client.get("/auth/me", headers=_headers(token))

    assert r.status_code == 200
    assert r.json()["role"] == "owner"


def test_admin_can_access_me(client):
    _register(client, "admin@test.com", role="admin")
    token = _login(client, "admin@test.com")

    r = client.get("/auth/me", headers=_headers(token))

    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_admin_list_roles_correct(client):
    _register(client, "admin@test.com", role="admin")
    _register(client, "c@test.com", role="customer")
    _register(client, "o@test.com", role="owner")
    token = _login(client, "admin@test.com")

    r = client.get("/auth/admin/users", headers=_headers(token))

    by_email = {u["email"]: u["role"] for u in r.json()}
    assert by_email["admin@test.com"] == "admin"
    assert by_email["c@test.com"] == "customer"
    assert by_email["o@test.com"] == "owner"
