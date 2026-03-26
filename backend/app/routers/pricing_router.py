from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user
from app.schemas.pricing import PriceBreakdownResponse, PricingAnalyticsResponse
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing", tags=["Pricing"])

pricing_service = PricingService()


@router.get("/orders/{order_id}/breakdown", response_model=PriceBreakdownResponse)
def get_price_breakdown(
    order_id: str,
    current_user=Depends(get_current_user),
):
    return pricing_service.get_price_breakdown(order_id, current_user)


@router.get("/analytics", response_model=PricingAnalyticsResponse)
def get_pricing_analytics(
    current_user=Depends(get_current_user),
):
    return pricing_service.get_pricing_analytics(current_user)
