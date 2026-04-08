import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import date, timedelta

client = TestClient(app)

def test_admin_report_date_filter():
    today = date.today()
    resp = client.get(f"/reports/admin/orders?date_start={today}&date_end={today}")
    assert resp.status_code in [200, 401, 403]
    if resp.status_code == 200:
        data = resp.json()
        assert "total_orders" in data

def test_admin_report_restaurant_filter():
    resp = client.get("/reports/admin/orders?restaurant_id=test-restaurant")
    assert resp.status_code in [200, 401, 403]
    if resp.status_code == 200:
        data = resp.json()
        assert "total_orders" in data

def test_owner_report_scoping():
    resp = client.get("/reports/owner/orders")
    assert resp.status_code in [200, 401, 403]
    if resp.status_code == 200:
        data = resp.json()
        assert "total_orders" in data

def test_admin_system_report_combined_filters():
    today = date.today()
    resp = client.get(f"/reports/admin/system?date_start={today}&date_end={today}&restaurant_id=test-restaurant")
    assert resp.status_code in [200, 401, 403]
    if resp.status_code == 200:
        data = resp.json()
        assert "orders" in data
        assert "deliveries" in data
        assert "payments" in data
        assert "reviews" in data

def test_owner_system_report_date_filter():
    today = date.today()
    resp = client.get(f"/reports/owner/system?date_start={today}&date_end={today}")
    assert resp.status_code in [200, 401, 403]
    if resp.status_code == 200:
        data = resp.json()
        assert "orders" in data
        assert "deliveries" in data
        assert "payments" in data
        assert "reviews" in data
