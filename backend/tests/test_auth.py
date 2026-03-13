import tempfile
from pathlib import Path

import pytest
from app.dependencies import get_auth_service
from app.main import app
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as temp_dir:
        users_file = Path(temp_dir) / "users.json"
        user_repo = UserRepository(users_file)
        auth_service = AuthService(
            user_repo=user_repo,
            secret_key="test-secret-key-for-gitsos-authentication-12345",
        )

        def override_auth_service():
            return auth_service

        app.dependency_overrides[get_auth_service] = override_auth_service

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()


def test_register_success(client):
    r = client.post(
        "/auth/register",
        json={"email": "a@test.com", "password": "secret12", "role": "customer"},
    )
    print(r.json())
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@test.com"
    assert body["role"] == "customer"
    assert "id" in body


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={"email": "dup@test.com", "password": "secret12", "role": "customer"},
    )
    r = client.post(
        "/auth/register",
        json={"email": "dup@test.com", "password": "secret12", "role": "customer"},
    )
    assert r.status_code == 409


def test_login_success_returns_token(client):
    client.post(
        "/auth/register",
        json={"email": "login@test.com", "password": "secret12", "role": "customer"},
    )
    r = client.post(
        "/auth/login", json={"email": "login@test.com", "password": "secret12"}
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    client.post(
        "/auth/register",
        json={"email": "bad@test.com", "password": "secret12", "role": "customer"},
    )
    r = client.post(
        "/auth/login", json={"email": "bad@test.com", "password": "wrongpass"}
    )
    assert r.status_code == 401
