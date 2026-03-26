# Order repository for data access layer
import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.schemas.order import (
    Order,
    OrderCreate,
    OrderStatus,
    OrderUpdate,
    TrafficCondition,
    WeatherCondition,
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

    # Retrieve all system created orders
    def get_all_orders(self) -> list[Order]:
        orders = self._load_orders()
        return [Order(**o) for o in orders]

    def get_orders_by_restaurant_id(self, rest_id: int) -> list[Order]:
        orders = self._load_orders()
        return [Order(**o) for o in orders if o.get("restaurant_id") == rest_id]

    def get_orders_by_customer_id(self, customer_id: str) -> list[Order]:
        orders = self._load_orders()
        return [Order(**o) for o in orders if o.get("customer_id") == customer_id]

    def get_orders_by_conditions(
        self,
        traffic_condition: Optional[str] = None,
        weather_condition: Optional[str] = None,
    ) -> list[Order]:
        orders = self._load_orders()
        result = []
        for o in orders:
            if traffic_condition and o.get("traffic_condition") != traffic_condition:
                continue
            if weather_condition and o.get("weather_condition") != weather_condition:
                continue
            result.append(Order(**o))
        return result

    # Update a system order by ID
    def update_order(self, order_id: str, update_data: OrderUpdate) -> Optional[Order]:
        orders = self._load_orders()
        for i, order in enumerate(orders):
            if order["order_id"] == order_id:
                # Apply updates only for non-None fields
                if update_data.food_item is not None:
                    orders[i]["food_item"] = update_data.food_item
                if update_data.order_value is not None:
                    orders[i]["order_value"] = update_data.order_value
                if update_data.delivery_distance is not None:
                    orders[i]["delivery_distance"] = update_data.delivery_distance
                if update_data.delivery_method is not None:
                    orders[i]["delivery_method"] = update_data.delivery_method.value
                if update_data.traffic_condition is not None:
                    orders[i]["traffic_condition"] = update_data.traffic_condition.value
                if update_data.weather_condition is not None:
                    orders[i]["weather_condition"] = update_data.weather_condition.value
                self._save_orders(orders)
                return Order(**orders[i])
        return None

    # Update order status by ID
    def update_order_status(
        self, order_id: str, new_status: OrderStatus
    ) -> Optional[Order]:
        orders = self._load_orders()
        for i, order in enumerate(orders):
            if order["order_id"] == order_id:
                orders[i]["order_status"] = new_status.value
                self._save_orders(orders)
                return Order(**orders[i])
        return None

    # Record actual delivery time and delay for a delivered order
    def record_delivery_outcome(
        self, order_id: str, actual_delivery_time: float, delivery_delay: float
    ) -> Optional[Order]:
        orders = self._load_orders()
        for i, order in enumerate(orders):
            if order["order_id"] == order_id:
                orders[i]["actual_delivery_time"] = actual_delivery_time
                orders[i]["delivery_delay"] = delivery_delay
                self._save_orders(orders)
                return Order(**orders[i])
        return None


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

    @staticmethod
    def _parse_restaurant_id(raw: str) -> Optional[int]:
        """Parse restaurant ID — handles plain integers and 'R<n>' prefix format."""
        try:
            return int(raw)
        except (ValueError, TypeError):
            pass
        try:
            return int(str(raw).lstrip("R"))
        except (ValueError, TypeError):
            return None

    # Get all unique restaurant IDs from Kaggle data
    def get_restaurants(self) -> set[int]:
        orders = self._load_orders()
        result = set()
        for o in orders:
            parsed = self._parse_restaurant_id(o.get("restaurant_id", ""))
            if parsed is not None:
                result.add(parsed)
        return result

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
            if self._parse_restaurant_id(o.get("restaurant_id", "")) == restaurant_id
        }

    # Retrieve a Kaggle order by ID (read-only)
    def get_order_by_id(self, order_id: str) -> Optional[dict]:
        orders = self._load_orders()
        for order in orders:
            if order["order_id"] == order_id:
                return order
        return None

    # Get all Kaggle orders
    def get_all_orders(self) -> list[dict]:
        return self._load_orders()

    # Get Kaggle orders for a specific restaurant
    def get_orders_by_restaurant(self, restaurant_id: int) -> list[dict]:
        orders = self._load_orders()
        return [
            o
            for o in orders
            if self._parse_restaurant_id(o.get("restaurant_id", "")) == restaurant_id
        ]
