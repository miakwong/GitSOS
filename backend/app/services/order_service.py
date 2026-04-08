# Order service for business logic
from pathlib import Path

from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.order import (
    CANCELLABLE_STATUSES,
    MODIFIABLE_STATUSES,
    VALID_TRANSITIONS,
    Order,
    OrderCreate,
    OrderStatus,
    OrderUpdate,
)
from fastapi import HTTPException, status


# Service layer for order creation and validation
class OrderService:

    def __init__(
        self,
        order_repo: OrderRepository = None,
        kaggle_repo: KaggleOrderRepository = None,
        user_repo: UserRepository = None,
    ):
        self.order_repo = order_repo or OrderRepository()
        self.kaggle_repo = kaggle_repo or KaggleOrderRepository()
        _users_file = Path(__file__).resolve().parent.parent / "data" / "users.json"
        self.user_repo = user_repo or UserRepository(_users_file)

    # Validate that customer_id exists in Kaggle data or is a registered system user
    def _validate_customer_exists(self, customer_id: str) -> None:
        kaggle_customers = self.kaggle_repo.get_customers()
        if customer_id in kaggle_customers:
            return
        self.user_repo._load_users()
        system_user = self.user_repo.get_user_by_id_str(customer_id)
        if system_user is not None:
            return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with ID '{customer_id}' does not exist",
        )

    # Validate that restaurant_id exists in Kaggle data
    def _validate_restaurant_exists(self, restaurant_id: int) -> None:
        restaurants = self.kaggle_repo.get_restaurants()
        if restaurant_id not in restaurants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Restaurant with ID '{restaurant_id}' does not exist",
            )

    # Validate that food_item is offered by the restaurant
    def _validate_food_item(self, food_item: str, restaurant_id: int) -> None:
        food_items = self.kaggle_repo.get_food_items_by_restaurant(restaurant_id)
        if food_item not in food_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Food item '{food_item}' is not offered by restaurant {restaurant_id}",
            )

    # Create a new system order with full validation
    def create_order(self, order_data: OrderCreate) -> Order:
        # Validate referenced entities exist
        self._validate_customer_exists(order_data.customer_id)
        self._validate_restaurant_exists(order_data.restaurant_id)
        self._validate_food_item(order_data.food_item, order_data.restaurant_id)

        # Create and persist the order
        return self.order_repo.create_order(order_data)

    # Retrieve a system order by ID
    def get_order(self, order_id: str) -> Order:
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found",
            )
        return order

    # Retrieve all system-created orders
    def get_all_orders(self) -> list[Order]:
        return self.order_repo.get_all_orders()

    # Retrieve orders by customer ID
    def get_orders_by_customer(self, customer_id: str) -> list[Order]:
        all_orders = self.order_repo.get_all_orders()
        return [o for o in all_orders if o.customer_id == customer_id]

    def get_orders_for_owner(self, rest_id: int) -> list[Order]:
        return self.order_repo.get_orders_by_restaurant_id(rest_id)

    def get_order_for_owner(self, order_id: str, rest_id: int) -> Order:
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found",
            )
        # make sure order belongs to this owner's restaurant
        if order.restaurant_id != rest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: this order does not belong to your restaurant",
            )
        return order

    # Validate ownership - customer can only modify their own orders
    def _validate_ownership(self, order: Order, customer_id: str) -> None:
        if order.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only modify your own orders",
            )

    # Validate order is in a modifiable state
    def _validate_modifiable_status(self, order: Order) -> None:
        if order.order_status not in MODIFIABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be modified in '{order.order_status.value}' status. Only orders in {[s.value for s in MODIFIABLE_STATUSES]} status can be modified.",
            )

    # Validate order is in a cancellable state
    def _validate_cancellable_status(self, order: Order) -> None:
        if order.order_status not in CANCELLABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be cancelled in '{order.order_status.value}' status. Only orders in {[s.value for s in CANCELLABLE_STATUSES]} status can be cancelled.",
            )

    # Check if order is a Kaggle historical order (cannot be modified)
    def _is_kaggle_order(self, order_id: str) -> bool:
        return self.kaggle_repo.get_order_by_id(order_id) is not None

    # Update a system order with ownership and workflow validation
    def update_order(
        self, order_id: str, customer_id: str, update_data: OrderUpdate
    ) -> Order:
        # Check if this is a Kaggle order (read-only)
        if self._is_kaggle_order(order_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kaggle historical orders cannot be modified",
            )

        # Get the order
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found",
            )

        # Validate ownership
        self._validate_ownership(order, customer_id)

        # Validate order is modifiable
        self._validate_modifiable_status(order)

        # Validate food item if being updated
        if update_data.food_item is not None:
            self._validate_food_item(update_data.food_item, order.restaurant_id)

        # Perform the update
        updated_order = self.order_repo.update_order(order_id, update_data)
        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order",
            )
        return updated_order

    # Advance an order through valid workflow transitions (owner only)
    def advance_order_status(
        self, order_id: str, new_status: OrderStatus, rest_id: int
    ) -> Order:
        if self._is_kaggle_order(order_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kaggle historical orders cannot be modified",
            )

        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found",
            )

        if order.restaurant_id != rest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: this order does not belong to your restaurant",
            )

        allowed = VALID_TRANSITIONS[order.order_status]
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition order from '{order.order_status.value}' to '{new_status.value}'. "
                f"Valid transitions: {[s.value for s in allowed] if allowed else 'none (terminal state)'}",
            )

        updated = self.order_repo.update_order_status(order_id, new_status)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order status",
            )
        return updated

    # Override order status as admin (bypasses workflow transition rules)
    def admin_override_status(self, order_id: str, new_status: OrderStatus) -> Order:
        if self._is_kaggle_order(order_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kaggle historical orders cannot be modified",
            )

        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found",
            )

        updated = self.order_repo.update_order_status(order_id, new_status)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order status",
            )
        return updated

    # Cancel a system order with ownership and workflow validation
    def cancel_order(self, order_id: str, customer_id: str) -> Order:
        # Check if this is a Kaggle order (read-only)
        if self._is_kaggle_order(order_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kaggle historical orders cannot be cancelled",
            )

        # Get the order
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found",
            )

        # Validate ownership
        self._validate_ownership(order, customer_id)

        # Validate order is cancellable
        self._validate_cancellable_status(order)

        # Update status to Cancelled
        cancelled_order = self.order_repo.update_order_status(
            order_id, OrderStatus.CANCELLED
        )
        if not cancelled_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel order",
            )
        return cancelled_order
