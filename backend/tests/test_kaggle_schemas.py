import pytest
from app.schemas.kaggle import KaggleMenuItem, KaggleOrder, KaggleRestaurant
from pydantic import ValidationError

# KaggleOrder


class TestKaggleOrder:
    def _valid(self, **overrides) -> dict:
        base = {
            "order_id": "1d8e87M",
            "restaurant_id": "16",
            "customer_id": "9c6dbfcb-72c5-4cc4-9f76-29200f0efda7",
            "food_item": "Taccos",
            "order_value": 42.21,
            "order_time": "2024-01-31",
            "delivery_distance": 2.17,
            "delivery_time_actual": 0.0,
            "delivery_delay": 17.15,
        }
        base.update(overrides)
        return base

    def test_valid(self):
        o = KaggleOrder(**self._valid())
        assert o.order_id == "1d8e87M"
        assert o.restaurant_id == "16"
        assert o.order_value == 42.21

    def test_ids_are_str(self):
        o = KaggleOrder(**self._valid())
        assert isinstance(o.order_id, str)
        assert isinstance(o.restaurant_id, str)
        assert isinstance(o.customer_id, str)

    def test_missing_required_field(self):
        data = self._valid()
        del data["order_id"]
        with pytest.raises(ValidationError):
            KaggleOrder(**data)

    def test_invalid_order_value_type(self):
        with pytest.raises(ValidationError):
            KaggleOrder(**self._valid(order_value="not-a-float"))


# KaggleRestaurant
class TestKaggleRestaurant:

    def test_valid(self):
        r = KaggleRestaurant(restaurant_id="16", name="Restaurant_16")
        assert r.restaurant_id == "16"
        assert r.name == "Restaurant_16"

    def test_id_is_str(self):
        r = KaggleRestaurant(restaurant_id="42", name="Restaurant_42")
        assert isinstance(r.restaurant_id, str)

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            KaggleRestaurant(restaurant_id="16")

    def test_empty_restaurant_id_rejected(self):
        with pytest.raises(ValidationError):
            KaggleRestaurant(restaurant_id="", name="Restaurant_16")

    def test_whitespace_restaurant_id_rejected(self):
        with pytest.raises(ValidationError):
            KaggleRestaurant(restaurant_id="   ", name="Restaurant_16")

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            KaggleRestaurant(restaurant_id="16", name="")


# KaggleMenuItem
class TestKaggleMenuItem:

    def test_valid(self):
        m = KaggleMenuItem(restaurant_id="16", food_item="Taccos", median_price=38.5)
        assert m.food_item == "Taccos"
        assert m.median_price == 38.5

    def test_id_is_str(self):
        m = KaggleMenuItem(restaurant_id="16", food_item="Pasta", median_price=25.0)
        assert isinstance(m.restaurant_id, str)

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            KaggleMenuItem(restaurant_id="16", food_item="Pasta")

    def test_invalid_median_price_type(self):
        with pytest.raises(ValidationError):
            KaggleMenuItem(restaurant_id="16", food_item="Pasta", median_price="cheap")

    def test_empty_restaurant_id_rejected(self):
        with pytest.raises(ValidationError):
            KaggleMenuItem(restaurant_id="", food_item="Pasta", median_price=25.0)

    def test_whitespace_restaurant_id_rejected(self):
        with pytest.raises(ValidationError):
            KaggleMenuItem(restaurant_id="  ", food_item="Pasta", median_price=25.0)

    def test_empty_food_item_rejected(self):
        with pytest.raises(ValidationError):
            KaggleMenuItem(restaurant_id="16", food_item="", median_price=25.0)

    def test_whitespace_food_item_rejected(self):
        with pytest.raises(ValidationError):
            KaggleMenuItem(restaurant_id="16", food_item="  ", median_price=25.0)

    def test_negative_median_price_rejected(self):
        with pytest.raises(ValidationError):
            KaggleMenuItem(restaurant_id="16", food_item="Pasta", median_price=-1.0)

    def test_zero_median_price_allowed(self):
        m = KaggleMenuItem(restaurant_id="16", food_item="Pasta", median_price=0.0)
        assert m.median_price == 0.0
