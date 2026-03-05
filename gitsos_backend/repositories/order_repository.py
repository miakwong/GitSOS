# Order repository for data access layer
import json
import csv
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from schemas.order import (
    Order, OrderCreate, OrderStatus,
    DeliveryMethod, TrafficCondition, WeatherCondition
)

# Path to data files
DATA_DIR = Path(__file__).parent.parent / "data"
ORDERS_JSON_PATH = DATA_DIR / "orders.json"
KAGGLE_CSV_PATH = DATA_DIR / "food_delivery.csv"


# Repository for system-created orders (read/write)
class OrderRepository:

    def __init__(self, orders_path: Path = ORDERS_JSON_PATH):
        self.orders_path = orders_path

    # Load orders from JSON file
    def _load_orders(self) -> list[dict]:
        if not self.orders_path.exists():
            return []
        with open(self.orders_path, "r") as f:
            data = json.load(f)
            return data if data else []

    # Save orders to JSON file
    def _save_orders(self, orders: list[dict]) -> None:
        with open(self.orders_path, "w") as f:
            json.dump(orders, f, indent=2, default=str)

    # Create and persist a new system order
    def create_order(self, order_data: OrderCreate) -> Order:
        orders = self._load_orders()

        # Generate UUID and set initial status
        new_order = Order(
            order_id=uuid.uuid4(),
            customer_id=order_data.customer_id,
            restaurant_id=order_data.restaurant_id,
            food_item=order_data.food_item,
            order_time=datetime.now(timezone.utc),
            order_value=order_data.order_value,
            delivery_distance=order_data.delivery_distance,
            delivery_method=order_data.delivery_method,
            traffic_condition=order_data.traffic_condition or TrafficCondition.LOW,
            weather_condition=order_data.weather_condition or WeatherCondition.SUNNY,
            order_status=OrderStatus.PLACED,
        )

        orders.append(new_order.model_dump(mode="json"))
        self._save_orders(orders)
        return new_order

    # Retrieve a system order by ID
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        orders = self._load_orders()
        for order in orders:
            if order["order_id"] == order_id:
                return Order(**order)
        return None

    # Retrieve all system-created orders
    def get_all_orders(self) -> list[Order]:
        orders = self._load_orders()
        return [Order(**o) for o in orders]


# Repository for Kaggle historical orders (read-only)
class KaggleOrderRepository:

    def __init__(self, csv_path: Path = KAGGLE_CSV_PATH):
        self.csv_path = csv_path
        self._orders: Optional[list[dict]] = None

    # Load and cache Kaggle orders from CSV
    def _load_orders(self) -> list[dict]:
        if self._orders is not None:
            return self._orders

        self._orders = []
        if not self.csv_path.exists():
            return self._orders

        with open(self.csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self._orders.append(row)
        return self._orders

    # Get all unique restaurant IDs from Kaggle data
    def get_restaurants(self) -> set[int]:
        orders = self._load_orders()
        return {int(o["restaurant_id"]) for o in orders if o.get("restaurant_id")}

    # Get all unique customer IDs from Kaggle data
    def get_customers(self) -> set[str]:
        orders = self._load_orders()
        return {o["customer_id"] for o in orders if o.get("customer_id")}

    # Get all food items offered by a specific restaurant
    def get_food_items_by_restaurant(self, restaurant_id: int) -> set[str]:
        orders = self._load_orders()
        return {
            o["food_item"]
            for o in orders
            if o.get("restaurant_id") and int(o["restaurant_id"]) == restaurant_id
        }

    # Retrieve a Kaggle order by ID (read-only)
    def get_order_by_id(self, order_id: str) -> Optional[dict]:
        orders = self._load_orders()
        for order in orders:
            if order["order_id"] == order_id:
                return order
        return None
