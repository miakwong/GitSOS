from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException

from app.repositories.order_repository import OrderRepository, KaggleOrderRepository
from app.repositories.kaggle_order_repository import get_median_price
from app.schemas.pricing import DeliveryFeeBreakdown, PriceBreakdownResponse, PricingAnalyticsResponse


class PricingService:
    BASE_FEE = 3.00

    TAX_RATE = 0.05

    def __init__(
        self,
        order_repo: OrderRepository | None = None,
        kaggle_repo: KaggleOrderRepository | None = None,
    ) -> None:
        self.order_repo = order_repo or OrderRepository()
        self.kaggle_repo = kaggle_repo or KaggleOrderRepository()

    # ------------------------------------------------------------------ #
    # This is to round a dollar amount to 2 decimal places
    # ------------------------------------------------------------------ #
    def _round_money(self, value: float) -> float:
        return round(value, 2)

    # ------------------------------------------------------------------ #
    # Access control: Only the order's customer or an admin can see the price breakdown
    # ------------------------------------------------------------------ #
    def _check_access(self, order, current_user) -> None:
        if current_user.role == "admin":
            return
        if str(order.customer_id) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this order breakdown",
            )

    # ------------------------------------------------------------------ #
    # This is to determine food base price from Kaggle data
    # ------------------------------------------------------------------ #
    def _get_food_price(self, restaurant_id: int, food_item: str) -> float:
        """
        Uses a 3-tier fallback to find the food price:
          1. Median price for restaurant_id, food_item in Kaggle data
          2. Global median price for food_item across all restaurants
          3. $25.00 default if the item is not in Kaggle at all
        """
        return get_median_price(restaurant_id, food_item)

    # ------------------------------------------------------------------ #
    # Delivery fee sub-components
    # ------------------------------------------------------------------ #
    def _calculate_distance_fee(self, delivery_distance: float) -> float:
        """
        Progressive distance tiers:
          2.0 <= distance <  3.0 : $0.00
          3.0 <= distance <  8.0 : (distance - 3.0) x $0.50
          8.0 <= distance <= 15.0 : $2.50 + (distance - 8.0) x $0.80
        """
        if 2.0 <= delivery_distance < 3.0:
            return 0.00
        elif 3.0 <= delivery_distance < 8.0:
            return (delivery_distance - 3.0) * 0.50
        elif 8.0 <= delivery_distance <= 15.0:
            return 2.50 + (delivery_distance - 8.0) * 0.80
        # Distance is outside the defined tiers (< 2.0 or > 15.0).
        # The dataset make sure that all distances are within 2.0–15.0 km,
        # so this fallback should never be hit in normal usage.
        return 0.00

    def _calculate_method_surcharge(self, delivery_method) -> float:
        """
        Method surcharge:
          Walk -> $0.00 | Bike -> $1.00 | Car -> $2.50
        """
        method = delivery_method.value
        if method == "Walk":
            return 0.00
        elif method == "Bike":
            return 1.00
        elif method == "Car":
            return 2.50
        return 0.00

    def _calculate_traffic_surcharge(self, traffic_condition) -> float:
        """
        Traffic surcharge:
          Low -> $0.00 | Medium -> $1.00 | High -> $2.00
        """
        traffic = traffic_condition.value
        if traffic == "Low":
            return 0.00
        elif traffic == "Medium":
            return 1.00
        elif traffic == "High":
            return 2.00
        return 0.00

    def _calculate_weather_surcharge(self, weather_condition) -> float:
        """
        Weather surcharge:
          Sunny -> $0.00 | Rainy -> $1.50 | Snowy -> $2.00
        """
        weather = weather_condition.value
        if weather == "Sunny":
            return 0.00
        elif weather == "Rainy":
            return 1.50
        elif weather == "Snowy":
            return 2.00
        return 0.00

    def _calculate_delivery_fee(self, order) -> DeliveryFeeBreakdown:
        """
        Below is to build the full delivery fee breakdown for an order:
          delivery_fee = base_fee + distance_fee + method_surcharge + condition_surcharge
          condition_surcharge = traffic_surcharge + weather_surcharge
        """
        base_fee = self.BASE_FEE
        distance_fee = self._calculate_distance_fee(order.delivery_distance)
        method_surcharge = self._calculate_method_surcharge(order.delivery_method)
        traffic_surcharge = self._calculate_traffic_surcharge(order.traffic_condition)
        weather_surcharge = self._calculate_weather_surcharge(order.weather_condition)

        condition_surcharge = traffic_surcharge + weather_surcharge
        total_delivery_fee = base_fee + distance_fee + method_surcharge + condition_surcharge

        return DeliveryFeeBreakdown(
            base_fee=self._round_money(base_fee),
            distance_fee=self._round_money(distance_fee),
            method_surcharge=self._round_money(method_surcharge),
            traffic_surcharge=self._round_money(traffic_surcharge),
            weather_surcharge=self._round_money(weather_surcharge),
            condition_surcharge=self._round_money(condition_surcharge),
            total_delivery_fee=self._round_money(total_delivery_fee),
        )

    # ------------------------------------------------------------------ #
    # Main public method: compute the full price breakdown for an order
    # ------------------------------------------------------------------ #
    def get_price_breakdown(self, order_id: str, current_user) -> PriceBreakdownResponse:
        """
        Return the computed price breakdown for a system-created order.

        Steps:
          1. Look up the system order and reject Kaggle historical orders
          2. Check that the current user has access
          3. Get food price from Kaggle data
          4. Calculate delivery fee from order parameters
          5. Apply tax and return the full breakdown
        """
        # Step 1: Find the order in the system-created orders store
        order = self.order_repo.get_order_by_id(order_id)

        if order:
            # Step 2: Access control
            self._check_access(order, current_user)

            # Step 3: Food base price from Kaggle data
            food_price = self._round_money(
                self._get_food_price(order.restaurant_id, order.food_item)
            )

            # Step 4: Delivery fee breakdown
            delivery_fee = self._calculate_delivery_fee(order)

            # Step 5: Subtotal, tax, and final total
            subtotal = self._round_money(food_price + delivery_fee.total_delivery_fee)
            tax = self._round_money(subtotal * self.TAX_RATE)
            total = self._round_money(subtotal + tax)

            return PriceBreakdownResponse(
                order_id=str(order.order_id),
                food_price=food_price,
                delivery_fee=delivery_fee,
                subtotal=subtotal,
                tax=tax,
                total=total,
            )

        # If the order_id belongs to a Kaggle historical order it will return 404.
        historical_order = self.kaggle_repo.get_order_by_id(order_id)
        if historical_order:
            raise HTTPException(status_code=404, detail="Order not found")

        raise HTTPException(status_code=404, detail="Order not found")

    def get_pricing_analytics(self, current_user) -> PricingAnalyticsResponse:
        # Only admins can view pricing analytics
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can view pricing analytics",
            )

        # Load all system-created orders
        orders = self.order_repo.get_all_orders()

        # If no orders exist, return zero/None response
        if not orders:
            return PricingAnalyticsResponse(
                total_orders=0,
                total_revenue=0.0,
                avg_order_value=None,
                min_order_value=None,
                max_order_value=None,
            )

        # Compute the full total which is food + delivery + tax for each order
        order_totals = []
        total_revenue = 0.0

        for order in orders:
            food_price = self._round_money(order.order_value)
            delivery_fee = self._calculate_delivery_fee(order)
            subtotal = self._round_money(food_price + delivery_fee.total_delivery_fee)
            tax = self._round_money(subtotal * self.TAX_RATE)
            order_total = self._round_money(subtotal + tax)
            order_totals.append(order_total)
            total_revenue += order_total

        return PricingAnalyticsResponse(
            total_orders=len(orders),
            total_revenue=self._round_money(total_revenue),
            avg_order_value=self._round_money(total_revenue / len(orders)),
            min_order_value=self._round_money(min(order_totals)),
            max_order_value=self._round_money(max(order_totals)),
        )
