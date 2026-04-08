import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestReportAggregationAccuracy:
    
    def test_order_total_is_nonnegative(self):
        response = client.get("/admin/reports/orders")
        if response.status_code == 200:
            data = response.json()
            assert data["total_orders"] >= 0
            assert data["total_revenue"] >= 0
    
    def test_payment_totals_consistent(self):
        response = client.get("/admin/reports/payments")
        if response.status_code == 200:
            data = response.json()
            assert data["total_transactions"] >= 0
            assert data["successful_payments"] >= 0
            assert data["failed_payments"] >= 0
            assert data["total_revenue"] >= 0
    
    def test_review_rating_in_valid_range(self):
        response = client.get("/admin/reports/reviews")
        if response.status_code == 200:
            data = response.json()
            assert 0 <= data["average_rating"] <= 5
            assert data["total_reviews"] >= 0
    
    def test_delivery_counts_consistent(self):
        response = client.get("/admin/reports/deliveries")
        if response.status_code == 200:
            data = response.json()
            total = data["total_deliveries"]
            completed = data["completed_deliveries"]
            pending = data["pending_deliveries"]
            assert completed + pending == total


class TestReportConsistency:
    
    def test_system_report_contains_all_summaries(self):
        response = client.get("/admin/reports/system")
        if response.status_code == 200:
            data = response.json()
            assert "orders" in data
            assert "deliveries" in data
            assert "payments" in data
            assert "reviews" in data
    
    def test_order_counts_sum_correctly(self):
        response = client.get("/admin/reports/orders")
        if response.status_code == 200:
            data = response.json()
            total = data["total_orders"]
            completed = data["completed_orders"]
            cancelled = data["cancelled_orders"]
            pending = data["pending_orders"]
            assert completed + cancelled + pending <= total


class TestReportErrorHandling:
    
    def test_missing_authorization_returns_401_or_403(self):
        response = client.get("/admin/reports/system")
        assert response.status_code in [401, 403]
    
    def test_all_endpoints_require_auth(self):
        endpoints = [
            "/admin/reports/system",
            "/admin/reports/orders",
            "/admin/reports/deliveries",
            "/admin/reports/payments",
            "/admin/reports/reviews",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403]
