import pytest
from fastapi.testclient import TestClient
from app.main import app
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403], f"{endpoint} should require auth"


class TestReportDataStructure:
    
    def test_system_report_has_all_sections(self):
        response = client.get("/admin/reports/system")
        if response.status_code == 200:
            data = response.json()
            assert "orders" in data
            assert "deliveries" in data
            assert "payments" in data
            assert "reviews" in data
    
    def test_order_summary_structure(self):
        response = client.get("/admin/reports/orders")
        if response.status_code == 200:
            data = response.json()
            assert "total_orders" in data
            assert "completed_orders" in data
            assert "cancelled_orders" in data
            assert "pending_orders" in data
            assert "total_revenue" in data
    
    def test_delivery_summary_structure(self):
        response = client.get("/admin/reports/deliveries")
        if response.status_code == 200:
            data = response.json()
            assert "total_deliveries" in data
            assert "completed_deliveries" in data
            assert "pending_deliveries" in data
    
    def test_payment_summary_structure(self):
        response = client.get("/admin/reports/payments")
        if response.status_code == 200:
            data = response.json()
            assert "total_transactions" in data
            assert "total_revenue" in data
            assert "successful_payments" in data
            assert "failed_payments" in data
            assert "total_refunds" in data
    
    def test_review_summary_structure(self):
        response = client.get("/admin/reports/reviews")
        if response.status_code == 200:
            data = response.json()
            assert "total_reviews" in data
            assert "average_rating" in data
            assert "total_restaurants_reviewed" in data
            assert "five_star_reviews" in data
            assert "one_star_reviews" in data
=======
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
>>>>>>> feat/10-B2-scoped-reports
