<<<<<<< HEAD
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_admin
=======
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from app.dependencies import get_current_admin, get_current_owner
from app.services import report_service
>>>>>>> feat/10-B2-scoped-reports
from app.schemas.reports import (
    OrderSummaryReport,
    DeliverySummaryReport,
    PaymentSummaryReport,
    from fastapi import APIRouter, Depends, Query
    from typing import Optional
    from datetime import date
    from app.dependencies import get_current_admin, get_current_owner
    from app.services import report_service
    from app.schemas.reports import (
        OrderSummaryReport,
        DeliverySummaryReport,
        PaymentSummaryReport,
        ReviewSummaryReport,
        SystemSummaryReport,
    )

    router = APIRouter(prefix="/reports", tags=["reports"])

    @router.get("/admin/system", response_model=SystemSummaryReport)
    def admin_system_report(
        date_start: Optional[date] = Query(None),
        date_end: Optional[date] = Query(None),
        restaurant_id: Optional[str] = Query(None),
        admin=Depends(get_current_admin),
    ):
        return report_service.get_system_summary(date_start, date_end, restaurant_id)

    @router.get("/admin/orders", response_model=OrderSummaryReport)
    def admin_orders_report(
        date_start: Optional[date] = Query(None),
        date_end: Optional[date] = Query(None),
        restaurant_id: Optional[str] = Query(None),
        admin=Depends(get_current_admin),
    ):
        return report_service.get_order_summary(date_start, date_end, restaurant_id)

    @router.get("/owner/system", response_model=SystemSummaryReport)
    def owner_system_report(
        date_start: Optional[date] = Query(None),
        date_end: Optional[date] = Query(None),
        owner=Depends(get_current_owner),
    ):
        return report_service.get_system_summary(date_start, date_end, owner.restaurant_id)

    @router.get("/owner/orders", response_model=OrderSummaryReport)
    def owner_orders_report(
        date_start: Optional[date] = Query(None),
        date_end: Optional[date] = Query(None),
        owner=Depends(get_current_owner),
    ):
        return report_service.get_order_summary(date_start, date_end, owner.restaurant_id)

@router.get("/owner/orders", response_model=OrderSummaryReport)
def owner_orders_report(
    date_start: Optional[date] = Query(None),
    date_end: Optional[date] = Query(None),
    owner=Depends(get_current_owner),
):
    return report_service.get_order_summary(date_start, date_end, owner.restaurant_id)
>>>>>>> feat/10-B2-scoped-reports
