import pytest
from app.schemas.menu import MenuItemCreate, MenuItemOut, MenuItemUpdate
from pydantic import ValidationError


class TestMenuItemCreate:
    def test_valid(self):
        m = MenuItemCreate(food_item="Burger", price=12.50)
        assert m.food_item == "Burger"
        assert m.price == 12.50

    def test_food_item_stripped(self):
        m = MenuItemCreate(food_item="  Burger  ", price=12.50)
        assert m.food_item == "Burger"

    def test_missing_food_item(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(price=12.50)

    def test_missing_price(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(food_item="Burger")

    def test_empty_food_item_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(food_item="", price=12.50)

    def test_whitespace_food_item_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(food_item="   ", price=12.50)

    def test_zero_price_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(food_item="Burger", price=0)

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(food_item="Burger", price=-5.0)

    def test_small_positive_price_allowed(self):
        m = MenuItemCreate(food_item="Burger", price=0.01)
        assert m.price == 0.01

    def test_invalid_price_type(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(food_item="Burger", price="cheap")


class TestMenuItemUpdate:

    def test_valid_food_item_only(self):
        m = MenuItemUpdate(food_item="New Burger")
        assert m.food_item == "New Burger"
        assert m.price is None

    def test_valid_price_only(self):
        m = MenuItemUpdate(price=15.0)
        assert m.price == 15.0
        assert m.food_item is None

    def test_all_none_allowed(self):
        m = MenuItemUpdate()
        assert m.food_item is None
        assert m.price is None

    def test_both_fields_valid(self):
        m = MenuItemUpdate(food_item="Big Burger", price=18.0)
        assert m.food_item == "Big Burger"
        assert m.price == 18.0

    def test_empty_food_item_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemUpdate(food_item="")

    def test_whitespace_food_item_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemUpdate(food_item="   ")

    def test_zero_price_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemUpdate(price=0)

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError):
            MenuItemUpdate(price=-1.0)

    def test_food_item_stripped(self):
        m = MenuItemUpdate(food_item="  Pasta  ")
        assert m.food_item == "Pasta"


class TestMenuItemOut:

    def test_valid(self):
        m = MenuItemOut(restaurant_id="16", food_item="Burger", price=12.50)
        assert m.restaurant_id == "16"
        assert m.food_item == "Burger"
        assert m.price == 12.50

    def test_missing_price(self):
        with pytest.raises(ValidationError):
            MenuItemOut(restaurant_id="16", food_item="Burger")

    def test_missing_food_item(self):
        with pytest.raises(ValidationError):
            MenuItemOut(restaurant_id="16", price=12.50)

    def test_missing_restaurant_id(self):
        with pytest.raises(ValidationError):
            MenuItemOut(food_item="Burger", price=12.50)
