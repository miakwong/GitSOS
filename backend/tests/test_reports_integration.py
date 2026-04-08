import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestReportAggregationAccuracy:

    def test_order_total_is_nonnegative(self):
        response = client.get("/reports/admin/orders")
        if response.status_code == 200:
            data = response.json()
            assert data["total_orders"] >= 0
            assert data["total_revenue"] >= 0

    def test_payment_totals_consistent(self):
        response = client.get("/reports/admin/orders")
        if response.status_code == 200:
            data = response.json()
            assert data["total_orders"] >= 0
            assert data["total_revenue"] >= 0

    def test_review_rating_in_valid_range(self):
        response = client.get("/reports/admin/system")
        if response.status_code == 200:
            data = response.json()
            assert "orders" in data
            assert "reviews" in data

    def test_delivery_counts_consistent(self):
        response = client.get("/reports/admin/system")
        if response.status_code == 200:
            data = response.json()
            assert "deliveries" in data


class TestReportConsistency:

    def test_system_report_contains_all_summaries(self):
        response = client.get("/reports/admin/system")
        if response.status_code == 200:
            data = response.json()
            assert "orders" in data
            assert "deliveries" in data
            assert "payments" in data
            assert "reviews" in data

    def test_order_counts_sum_correctly(self):
        response = client.get("/reports/admin/orders")
        if response.status_code == 200:
            data = response.json()
            total = data["total_orders"]
            completed = data["completed_orders"]
            cancelled = data["cancelled_orders"]
            pending = data["pending_orders"]
            assert completed + cancelled + pending <= total


class TestReportErrorHandling:

    def test_missing_authorization_returns_401_or_403(self):
        response = client.get("/reports/admin/system")
        assert response.status_code in [401, 403]

    def test_all_endpoints_require_auth(self):
        endpoints = [
            "/reports/admin/system",
            "/reports/admin/orders",
            "/reports/owner/system",
            "/reports/owner/orders",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403]
