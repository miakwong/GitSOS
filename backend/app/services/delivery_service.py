# Service layer for delivery info retrieval and outcome recording
from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.schemas.delivery import DeliveryAnalytics, DeliveryInfo, DeliveryOutcomeCreate
from app.schemas.order import Order, OrderStatus, TrafficCondition, WeatherCondition
from typing import Optional
from app.schemas.user import UserInDB
from fastapi import HTTPException, status


class DeliveryService:

    def __init__(self, order_repo=None, kaggle_repo=None):
        self.order_repo = order_repo or OrderRepository()
        self.kaggle_repo = kaggle_repo or KaggleOrderRepository()

    def get_delivery_info(self, order_id: str, user: UserInDB) -> DeliveryInfo:
        # check system orders first
        system_order = self.order_repo.get_order_by_id(order_id)
        if system_order:
            return self._delivery_from_system_order(system_order, user)

        # check Kaggle historical orders next
        kaggle_row = self.kaggle_repo.get_order_by_id(order_id)
        if kaggle_row:
            return self._delivery_from_kaggle_order(kaggle_row, user)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found",
        )

    def _delivery_from_system_order(self, order, user: UserInDB) -> DeliveryInfo:
        # customers can only see their own orders
        if user.role == "customer":
            if order.customer_id != str(user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: you can only view delivery info for your own orders",
                )
        # owners can only see orders from their restaurant
        elif user.role == "owner":
            if order.restaurant_id != user.restaurant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: this order does not belong to your restaurant",
                )
        # admins can see any order 

        return DeliveryInfo(
            order_id=str(order.order_id),
            delivery_distance=order.delivery_distance,
            delivery_method=order.delivery_method.value,
            traffic_condition=order.traffic_condition.value,
            weather_condition=order.weather_condition.value,
            is_historical=False,
        )

    def _delivery_from_kaggle_order(self, row: dict, user: UserInDB) -> DeliveryInfo:
        # Kaggle orders have no user UUID mapping so customers cannot claim ownership
        if user.role == "customer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: historical delivery records are not accessible to customers",
            )

        # owners can only see orders for their restaurant
        if user.role == "owner":
            if int(row["restaurant_id"]) != user.restaurant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: this order does not belong to your restaurant",
                )

        # Kaggle data is read-only so we only expose it, never modify it
        return DeliveryInfo(
            order_id=row["order_id"],
            delivery_distance=float(row["delivery_distance"]),
            delivery_time=float(row["delivery_time_actual"]),
            delivery_delay=float(row["delivery_delay"]),
            is_historical=True,
        )
# combined listing of delivery records for both system orders and Kaggle historical orders
    def list_delivery_records(self, user: UserInDB) -> list[DeliveryInfo]:
        results = []

        if user.role == "customer":
            orders = self.order_repo.get_orders_by_customer_id(str(user.id))
            for order in orders:
                results.append(DeliveryInfo(
                    order_id=str(order.order_id),
                    delivery_distance=order.delivery_distance,
                    delivery_method=order.delivery_method.value,
                    traffic_condition=order.traffic_condition.value,
                    weather_condition=order.weather_condition.value,
                    is_historical=False,
                ))

        elif user.role == "owner":
            orders = self.order_repo.get_orders_by_restaurant_id(user.restaurant_id)
            for order in orders:
                results.append(DeliveryInfo(
                    order_id=str(order.order_id),
                    delivery_distance=order.delivery_distance,
                    delivery_method=order.delivery_method.value,
                    traffic_condition=order.traffic_condition.value,
                    weather_condition=order.weather_condition.value,
                    is_historical=False,
                ))
            kaggle_rows = self.kaggle_repo.get_orders_by_restaurant(user.restaurant_id)
            for row in kaggle_rows:
                results.append(DeliveryInfo(
                    order_id=row["order_id"],
                    delivery_distance=float(row["delivery_distance"]),
                    delivery_time=float(row["delivery_time_actual"]),
                    delivery_delay=float(row["delivery_delay"]),
                    is_historical=True,
                ))

        else:
            orders = self.order_repo.get_all_orders()
            for order in orders:
                results.append(DeliveryInfo(
                    order_id=str(order.order_id),
                    delivery_distance=order.delivery_distance,
                    delivery_method=order.delivery_method.value,
                    traffic_condition=order.traffic_condition.value,
                    weather_condition=order.weather_condition.value,
                    is_historical=False,
                ))
            kaggle_rows = self.kaggle_repo.get_all_orders()
            for row in kaggle_rows:
                results.append(DeliveryInfo(
                    order_id=row["order_id"],
                    delivery_distance=float(row["delivery_distance"]),
                    delivery_time=float(row["delivery_time_actual"]),
                    delivery_delay=float(row["delivery_delay"]),
                    is_historical=True,
                ))

        return results

    def get_delivery_analytics(
        self,
        user: UserInDB,
        traffic_condition: Optional[str] = None,
        weather_condition: Optional[str] = None,
    ) -> DeliveryAnalytics:
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: only admins can view delivery analytics",
            )

        valid_traffic = {t.value for t in TrafficCondition}
        valid_weather = {w.value for w in WeatherCondition}

        if traffic_condition:
            traffic_condition = traffic_condition.capitalize()
            if traffic_condition not in valid_traffic:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid traffic_condition. Valid values: {', '.join(sorted(valid_traffic))}",
                )
        if weather_condition:
            weather_condition = weather_condition.capitalize()
            if weather_condition not in valid_weather:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid weather_condition. Valid values: {', '.join(sorted(valid_weather))}",
                )

        orders = self.order_repo.get_orders_by_conditions(
            traffic_condition=traffic_condition,
            weather_condition=weather_condition,
        )

        times = []
        delays = []
        for order in orders:
            if order.actual_delivery_time is not None:
                times.append(order.actual_delivery_time)
            if order.delivery_delay is not None:
                delays.append(order.delivery_delay)

        avg_time = round(sum(times) / len(times), 2) if times else None
        avg_delay = round(sum(delays) / len(delays), 2) if delays else None

        return DeliveryAnalytics(
            traffic_condition=traffic_condition,
            weather_condition=weather_condition,
            total_orders=len(orders),
            avg_delivery_time=avg_time,
            avg_delivery_delay=avg_delay,
        )

    def record_delivery_outcome(
        self, order_id: str, outcome: DeliveryOutcomeCreate, user: UserInDB
    ) -> Order:
        # Kaggle orders are read-only, outcomes cannot be recorded for them
        if self.kaggle_repo.get_order_by_id(order_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kaggle historical orders cannot have delivery outcomes recorded",
            )

        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found",
            )

        # customers cannot record outcomes
        if user.role == "customer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers cannot record delivery outcomes",
            )

        # owners can only record outcomes for their own restaurant's orders
        if user.role == "owner" and order.restaurant_id != user.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: this order does not belong to your restaurant",
            )

        # outcome can only be recorded after the order is delivered
        if order.order_status != OrderStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery outcome can only be recorded after order status is Delivered",
            )

        # once recorded, outcome fields are immutable
        if order.actual_delivery_time is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery outcome has already been recorded and cannot be changed",
            )

        updated = self.order_repo.record_delivery_outcome(
            order_id, outcome.actual_delivery_time, outcome.delivery_delay
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record delivery outcome",
            )
        return updated
