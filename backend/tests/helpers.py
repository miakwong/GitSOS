import uuid
from datetime import datetime, timezone
from typing import Optional

from app.repositories.order_repository import OrderRepository
from app.schemas.order import (
    DeliveryMethod,
    Order,
    OrderStatus,
    TrafficCondition,
    WeatherCondition,
)


def insert_analytics_order(
    order_repo: OrderRepository,
    traffic: TrafficCondition = TrafficCondition.LOW,
    weather: WeatherCondition = WeatherCondition.SUNNY,
    actual_delivery_time: Optional[float] = None,
    delivery_delay: Optional[float] = None,
) -> Order:
    order = Order(
        order_id=uuid.uuid4(),
        customer_id=str(uuid.uuid4()),
        restaurant_id=16,
        food_item="Tacos",
        order_time=datetime.now(timezone.utc),
        order_value=20.0,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=traffic,
        weather_condition=weather,
        order_status=OrderStatus.PLACED,
        actual_delivery_time=actual_delivery_time,
        delivery_delay=delivery_delay,
    )
    raw = order_repo._load_orders()
    raw.append(order.model_dump(mode="json"))
    order_repo._save_orders(raw)
    return order
