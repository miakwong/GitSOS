from pathlib import Path
import tempfile

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_auth_service, SECRET_KEY, ALGORITHM
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService, TOKEN_BLACKLIST


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

        def override_auth_service():
            return auth_service

        app.dependency_overrides[get_auth_service] = override_auth_service

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()
        TOKEN_BLACKLIST.clear()


def register_user(client, email="user@test.com", password="secret12"):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "customer"
        }
    )


def login_user(client, email="user@test.com", password="secret12"):
    return client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password
        }
    )


def test_register_success(client):
    response = register_user(client, "a@test.com")

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "a@test.com"
    assert body["role"] == "customer"
    assert "id" in body


def test_register_duplicate_email(client):
    register_user(client, "dup@test.com")
    response = register_user(client, "dup@test.com")

    assert response.status_code == 409


def test_login_success_returns_token(client):
    register_user(client, "login@test.com")
    response = login_user(client, "login@test.com")

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    register_user(client, "bad@test.com")
    response = login_user(client, "bad@test.com", "wrongpass")

    assert response.status_code == 401


def test_logout_success(client):
    register_user(client, "logout@test.com")
    login_response = login_user(client, "logout@test.com")
    token = login_response.json()["access_token"]

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


def test_access_rejected_after_logout(client):
    register_user(client, "afterlogout@test.com")
    login_response = login_user(client, "afterlogout@test.com")
    token = login_response.json()["access_token"]

    client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_access_rejected_with_expired_token(client):
    register_user(client, "expired@test.com")
    login_response = login_user(client, "expired@test.com")
    token = login_response.json()["access_token"]

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"verify_exp": False}
    )

    expired_auth_service = AuthService(
        user_repo=UserRepository(Path(tempfile.gettempdir()) / "dummy_users.json"),
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        access_token_minutes=-1,
    )

    expired_token = expired_auth_service.create_access_token(
        payload["sub"],
        payload["role"]
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401