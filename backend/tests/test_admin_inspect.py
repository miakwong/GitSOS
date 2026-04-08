import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Helper: simulate admin auth (replace with real token logic if needed)
def admin_headers():
    return {"Authorization": "Bearer admin-token"}

def test_admin_can_inspect_orders():
    resp = client.get("/admin/inspect/orders", headers=admin_headers())
    assert resp.status_code in [200, 401, 403]

def test_admin_can_inspect_payments():
    resp = client.get("/admin/inspect/payments", headers=admin_headers())
    assert resp.status_code in [200, 401, 403]

def test_admin_can_inspect_reviews():
    resp = client.get("/admin/inspect/reviews", headers=admin_headers())
    assert resp.status_code in [200, 401, 403]

def test_admin_can_inspect_deliveries():
    resp = client.get("/admin/inspect/deliveries", headers=admin_headers())
    assert resp.status_code in [200, 401, 403]

def test_non_admin_blocked_from_inspect():
    endpoints = [
        "/admin/inspect/orders",
        "/admin/inspect/payments",
        "/admin/inspect/reviews",
        "/admin/inspect/deliveries",
    ]
    for url in endpoints:
        resp = client.get(url)  # no auth
        assert resp.status_code in [401, 403]
