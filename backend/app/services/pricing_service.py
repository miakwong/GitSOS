from __future__ import annotations

from fastapi import HTTPException

from app.repositories.order_repository import OrderRepository, KaggleOrderRepository
from app.schemas.pricing import DeliveryFeeBreakdown, PriceBreakdownResponse


class PricingService:
    """
    Handles the price breakdown view for system-created orders.
    """

    TAX_RATE = 0.05
    BASE_DELIVERY_FEE = 2.50
    DISTANCE_RATE_PER_KM = 0.75

    def __init__(
        self,
        order_repo: OrderRepository | None = None,
        kaggle_repo: KaggleOrderRepository | None = None,
    ) -> None:
        self.order_repo = order_repo or OrderRepository()
        self.kaggle_repo = kaggle_repo or KaggleOrderRepository()

    def _round_money(self, value: float) -> float:
        return round(value, 2)

    def _check_access(self, order, current_user) -> None:
        """
        Only the customer who owns the order or an admin can view the breakdown.
        """
        if current_user.role == "admin":
            return

        if str(order.customer_id) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this order breakdown",
            )

    def _calculate_method_fee(self, delivery_method) -> float:
        method = delivery_method.value

        if method == "Walk":
            return 0.00
        if method == "Bike":
            return 0.50
        if method == "Car":
            return 1.50

        return 0.00

    def _calculate_condition_fee(self, traffic_condition, weather_condition) -> float:
        fee = 0.0

        traffic = traffic_condition.value
        weather = weather_condition.value

        if traffic == "Medium":
            fee += 0.50
        elif traffic == "High":
            fee += 1.00

        if weather == "Rainy":
            fee += 0.75
        elif weather == "Snowy":
            fee += 1.25

        return fee

    def _calculate_delivery_fee(self, order) -> DeliveryFeeBreakdown:
        base_fee = self.BASE_DELIVERY_FEE
        distance_fee = order.delivery_distance * self.DISTANCE_RATE_PER_KM
        method_fee = self._calculate_method_fee(order.delivery_method)
        condition_fee = self._calculate_condition_fee(
            order.traffic_condition,
            order.weather_condition,
        )

        total_delivery_fee = base_fee + distance_fee + method_fee + condition_fee

        return DeliveryFeeBreakdown(
            base_fee=self._round_money(base_fee),
            distance_fee=self._round_money(distance_fee),
            method_fee=self._round_money(method_fee),
            condition_fee=self._round_money(condition_fee),
            total_delivery_fee=self._round_money(total_delivery_fee),
        )

    def get_price_breakdown(self, order_id: str, current_user) -> PriceBreakdownResponse:
        """
        Return a computed price breakdown for a system-created order.
        Kaggle historical orders should be rejected.
        """
        # First check system-created orders
        order = self.order_repo.get_order_by_id(order_id)

        if order:
            self._check_access(order, current_user)

            # Order_value is treated as the food subtotal
            food_price = self._round_money(order.order_value)

            delivery_fee = self._calculate_delivery_fee(order)
            subtotal = self._round_money(food_price + delivery_fee.total_delivery_fee)
            tax = self._round_money(subtotal * self.TAX_RATE)
            total = self._round_money(subtotal + tax)

            response = PriceBreakdownResponse(
                order_id=str(order.order_id),
                food_price=food_price,
                delivery_fee=delivery_fee,
                subtotal=subtotal,
                tax=tax,
                total=total,
            )

            return response

        # Then check Kaggle historical orders — treat as not found to avoid leaking data
        historical_order = self.kaggle_repo.get_order_by_id(order_id)
        if historical_order:
            raise HTTPException(status_code=404, detail="Order not found")

        raise HTTPException(status_code=404, detail="Order not found")