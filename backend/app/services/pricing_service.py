from __future__ import annotations

from typing import List, Optional

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

    def _get_food_price(self, order) -> float:
        """
        Returns the food price for an order.
        Both get_price_breakdown and inspect_pricing call this helper
        so they always use the same food price logic.
        """
        return order.order_value

    def _calculate_method_surcharge(self, delivery_method) -> float:
        method = delivery_method.value

        if method == "Walk":
            return 0.00
        if method == "Bike":
            return 0.50
        if method == "Car":
            return 1.50

        return 0.00

    def _calculate_traffic_surcharge(self, traffic_condition) -> float:
        traffic = traffic_condition.value

        if traffic == "Medium":
            return 0.50
        elif traffic == "High":
            return 1.00

        return 0.00

    def _calculate_weather_surcharge(self, weather_condition) -> float:
        weather = weather_condition.value

        if weather == "Rainy":
            return 0.75
        elif weather == "Snowy":
            return 1.25

        return 0.00

    def _calculate_delivery_fee(self, order) -> DeliveryFeeBreakdown:
        base_fee = self.BASE_DELIVERY_FEE
        distance_fee = order.delivery_distance * self.DISTANCE_RATE_PER_KM
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

    def get_price_breakdown(self, order_id: str, current_user) -> PriceBreakdownResponse:
        """
        Return a computed price breakdown for a system-created order.
        Kaggle historical orders should be rejected.
        """
        # First check system-created orders
        order = self.order_repo.get_order_by_id(order_id)

        if order:
            self._check_access(order, current_user)

            food_price = self._round_money(self._get_food_price(order))

            delivery_fee = self._calculate_delivery_fee(order)
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

        # Then check Kaggle historical orders — treat as not found to avoid leaking data
        historical_order = self.kaggle_repo.get_order_by_id(order_id)
        if historical_order:
            raise HTTPException(status_code=404, detail="Order not found")

        raise HTTPException(status_code=404, detail="Order not found")

    def inspect_pricing(
        self, current_user, restaurant_id: Optional[int] = None
    ) -> List[PriceBreakdownResponse]:
        """
        Return a list of price breakdowns for inspection.
        - Admin can see all orders, or filter by restaurant_id if provided
        - Owner can only see orders for their own restaurant (restaurant_id param not allowed)
        - Customer is always denied with 403
        """
        if current_user.role == "customer":
            raise HTTPException(
                status_code=403,
                detail="Customers cannot inspect pricing",
            )

        if current_user.role == "owner":
            # Owners cannot use restaurant_id filter so they always see their own restaurant only.
            # If they pass restaurant_id we return 403 so they know the param isn't available to them.
            if restaurant_id is not None:
                raise HTTPException(
                    status_code=403,
                    detail="Owners cannot filter by restaurant_id",
                )
            owner_rest_id = current_user.restaurant_id
            if owner_rest_id is None:
                raise HTTPException(
                    status_code=403,
                    detail="Owner has no restaurant assigned",
                )
            orders = self.order_repo.get_orders_by_restaurant_id(owner_rest_id)
        else:
            if restaurant_id is not None:
                orders = self.order_repo.get_orders_by_restaurant_id(restaurant_id)
            else:
                orders = self.order_repo.get_all_orders()

        result = []
        for order in orders:
            food_price = self._round_money(self._get_food_price(order))
            delivery_fee = self._calculate_delivery_fee(order)
            subtotal = self._round_money(food_price + delivery_fee.total_delivery_fee)
            tax = self._round_money(subtotal * self.TAX_RATE)
            total = self._round_money(subtotal + tax)

            result.append(
                PriceBreakdownResponse(
                    order_id=str(order.order_id),
                    food_price=food_price,
                    delivery_fee=delivery_fee,
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                )
            )

        return result
