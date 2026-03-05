from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_success():
    r = client.post("/auth/register", json={"email": "a@test.com", "password": "secret12", "role": "customer"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@test.com"
    assert body["role"] == "customer"
    assert "id" in body


def test_register_duplicate_email():
    client.post("/auth/register", json={"email": "dup@test.com", "password": "secret12", "role": "customer"})
    r = client.post("/auth/register", json={"email": "dup@test.com", "password": "secret12", "role": "customer"})
    assert r.status_code == 409


def test_login_success_returns_token():
    client.post("/auth/register", json={"email": "login@test.com", "password": "secret12", "role": "customer"})
    r = client.post("/auth/login", json={"email": "login@test.com", "password": "secret12"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_invalid_credentials():
    client.post("/auth/register", json={"email": "bad@test.com", "password": "secret12", "role": "customer"})
    r = client.post("/auth/login", json={"email": "bad@test.com", "password": "wrongpass"})
    assert r.status_code == 401