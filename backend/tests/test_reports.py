import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.order import OrderStatus
from app.schemas.constants import PAYMENT_STATUS_SUCCESS


client = TestClient(app)


class TestSystemReportEndpoints:
    
    def test_system_report_endpoint_exists(self):
        response = client.get("/admin/reports/system")
        assert response.status_code in [200, 403, 401]
    
    def test_orders_report_endpoint_exists(self):
        response = client.get("/admin/reports/orders")
        assert response.status_code in [200, 403, 401]
    
    def test_deliveries_report_endpoint_exists(self):
        response = client.get("/admin/reports/deliveries")
        assert response.status_code in [200, 403, 401]
    
    def test_payments_report_endpoint_exists(self):
        response = client.get("/admin/reports/payments")
        assert response.status_code in [200, 403, 401]
    
    def test_reviews_report_endpoint_exists(self):
        response = client.get("/admin/reports/reviews")
        assert response.status_code in [200, 403, 401]


class TestReportAccessControl:
    
    def test_reports_require_authentication(self):
        endpoints = [
            "/admin/reports/system",
            "/admin/reports/orders",
            "/admin/reports/deliveries",
            "/admin/reports/payments",
            "/admin/reports/reviews",
        ]
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
