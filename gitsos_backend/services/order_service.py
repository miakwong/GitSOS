# Order service for business logic
from fastapi import HTTPException, status

from schemas.order import Order, OrderCreate
from repositories.order_repository import OrderRepository, KaggleOrderRepository


# Service layer for order creation and validation
class OrderService:

    def __init__(
        self,
        order_repo: OrderRepository = None,
        kaggle_repo: KaggleOrderRepository = None,
    ):
        self.order_repo = order_repo or OrderRepository()
        self.kaggle_repo = kaggle_repo or KaggleOrderRepository()

    # Validate that customer_id exists in Kaggle data
    def _validate_customer_exists(self, customer_id: str) -> None:
        customers = self.kaggle_repo.get_customers()
        if customer_id not in customers:
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
