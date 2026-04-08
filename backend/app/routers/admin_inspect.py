from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_admin
from app.repositories.order_repository import OrderRepository
from app.repositories import payment_repository
from app.repositories import review_repository
from app.schemas.order import Order
from app.schemas.payment import PaymentRecord
from app.schemas.review import ReviewRecord
from app.schemas.delivery import DeliveryInfo
from app.services.delivery_inspect_service import DeliveryInspectService

router = APIRouter(prefix="/admin/inspect", tags=["admin-inspect"])

@router.get("/orders", response_model=list[Order])
def inspect_orders(admin=Depends(get_current_admin)):
    repo = OrderRepository()
    return repo.get_all_orders()

@router.get("/payments", response_model=list[PaymentRecord])
def inspect_payments(admin=Depends(get_current_admin)):
    repo = payment_repository
    return repo.list_all()

@router.get("/reviews", response_model=list[ReviewRecord])
def inspect_reviews(admin=Depends(get_current_admin)):
    repo = review_repository
    return repo.list_all()

@router.get("/deliveries", response_model=list[DeliveryInfo])
def inspect_deliveries(admin=Depends(get_current_admin)):
    service = DeliveryInspectService()
    return service.get_all_delivery_info()
