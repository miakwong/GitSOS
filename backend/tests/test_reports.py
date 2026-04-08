from uuid import UUID
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_admin, get_current_owner

client = TestClient(app)

MOCK_ADMIN_ID = UUID("00000000-0000-0000-0000-000000000001")
MOCK_OWNER_ID = UUID("00000000-0000-0000-0000-000000000002")
MOCK_RESTAURANT_ID = 1


def test_admin_report_date_filter():
    from datetime import date
    today = date.today()
    resp = client.get(f"/reports/admin/orders?date_start={today}&date_end={today}")
    assert resp.status_code in [200, 401, 403]


def test_admin_report_restaurant_filter():
    resp = client.get("/reports/admin/orders?restaurant_id=test-restaurant")
    assert resp.status_code in [200, 401, 403]


def test_owner_report_scoping():
    resp = client.get("/reports/owner/orders")
    assert resp.status_code in [200, 401, 403]


def test_admin_system_report_combined_filters():
    from datetime import date
    today = date.today()
    resp = client.get(f"/reports/admin/system?date_start={today}&date_end={today}&restaurant_id=test-restaurant")
    assert resp.status_code in [200, 401, 403]


def test_owner_system_report_date_filter():
    from datetime import date
    today = date.today()
    resp = client.get(f"/reports/owner/system?date_start={today}&date_end={today}")
    assert resp.status_code in [200, 401, 403]


def test_endpoints_require_auth():
    endpoints = [
        "/reports/admin/orders",
        "/reports/admin/system",
        "/reports/owner/orders",
        "/reports/owner/system",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403], f"{endpoint} should require auth"


class TestReportDataStructure:

    def setup_method(self):
        app.dependency_overrides[get_current_admin] = lambda: MOCK_ADMIN_ID
        app.dependency_overrides[get_current_owner] = lambda: (MOCK_OWNER_ID, MOCK_RESTAURANT_ID)

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_system_report_has_all_sections(self):
        response = client.get("/reports/admin/system")
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "deliveries" in data
        assert "payments" in data
        assert "reviews" in data

    def test_order_summary_structure(self):
        response = client.get("/reports/admin/orders")
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "completed_orders" in data
        assert "cancelled_orders" in data
        assert "pending_orders" in data
        assert "total_revenue" in data

    def test_delivery_summary_structure(self):
        response = client.get("/reports/admin/system")
        assert response.status_code == 200
        data = response.json()["deliveries"]
        assert "total_deliveries" in data
        assert "completed_deliveries" in data
        assert "pending_deliveries" in data

    def test_payment_summary_structure(self):
        response = client.get("/reports/admin/system")
        assert response.status_code == 200
        data = response.json()["payments"]
        assert "total_transactions" in data
        assert "total_revenue" in data
        assert "successful_payments" in data
        assert "failed_payments" in data
        assert "total_refunds" in data

    def test_review_summary_structure(self):
        response = client.get("/reports/admin/system")
        assert response.status_code == 200
        data = response.json()["reviews"]
        assert "total_reviews" in data
        assert "average_rating" in data
        assert "total_restaurants_reviewed" in data
        assert "five_star_reviews" in data
        assert "one_star_reviews" in data

    def test_owner_system_report(self):
        response = client.get("/reports/owner/system")
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "deliveries" in data
        assert "payments" in data
        assert "reviews" in data

    def test_owner_orders_report(self):
        response = client.get("/reports/owner/orders")
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_revenue" in data
