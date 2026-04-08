from app.repositories.order_repository import OrderRepository
from app.schemas.delivery import DeliveryInfo
from app.schemas.user import UserInDB
from typing import List

class DeliveryInspectService:
    def __init__(self, order_repo=None):
        self.order_repo = order_repo or OrderRepository()

    def get_all_delivery_info(self) -> List[DeliveryInfo]:
        orders = self.order_repo.get_all_orders()
        deliveries = []
        for order in orders:
            deliveries.append(DeliveryInfo(
                order_id=str(order.order_id),
                delivery_distance=order.delivery_distance,
                delivery_method=getattr(order, 'delivery_method', None),
                traffic_condition=getattr(order, 'traffic_condition', None),
                weather_condition=getattr(order, 'weather_condition', None),
                is_historical=False
            ))
        return deliveries
