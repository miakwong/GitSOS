from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_admin
from app.schemas.reports import (
    OrderSummaryReport,
    DeliverySummaryReport,
    PaymentSummaryReport,
    ReviewSummaryReport,
    SystemSummaryReport,
)
from app.services import report_service

router = APIRouter(prefix="/admin/reports", tags=["reports"])


@router.get("/system", response_model=SystemSummaryReport)
def get_system_report(admin=Depends(get_current_admin)):
    return report_service.get_system_summary()


@router.get("/orders", response_model=OrderSummaryReport)
def get_orders_report(admin=Depends(get_current_admin)):
    return report_service.get_order_summary()


@router.get("/deliveries", response_model=DeliverySummaryReport)
def get_deliveries_report(admin=Depends(get_current_admin)):
    return report_service.get_delivery_summary()


@router.get("/payments", response_model=PaymentSummaryReport)
def get_payments_report(admin=Depends(get_current_admin)):
    return report_service.get_payment_summary()


@router.get("/reviews", response_model=ReviewSummaryReport)
def get_reviews_report(admin=Depends(get_current_admin)):
    return report_service.get_review_summary()
