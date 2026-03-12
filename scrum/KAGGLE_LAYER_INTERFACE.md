# Kaggle Data Layer — Interface Reference

## Overview

This document describes the public interface exposed by the `feat/kaggle-data-layer` branch.
All functions listed here are **read-only**. No write operations are permitted on Kaggle data (DR1, DR2).

---

## For pricing_service (Feat6)

The only function you need:

```python
from app.services.restaurant_service import get_median_price

price = get_median_price("Pasta")   # → 35.0 (float)
price = get_median_price("Pizza")   # → None  (unknown item)
```

Or call the repository directly:

```python
from app.repositories.kaggle_menu_repository import get_median_price

price = get_median_price("Pasta")   # → 35.0
```

**All 21 food items in the dataset:**
Taccos, Briyani rice, Pasta, Whole cake, Shawarma, Cup cake, PastrySmoothie,
Chicken pie, Burger, Sushi, Pizza, Sandwich, Noodles, Fried rice, Salad,
Steak, Soup, Tacos, Wrap, Spring rolls, Dumplings

---

## For order_service (Feat4)

Query historical Kaggle orders:

```python
from app.repositories import kaggle_order_repository

# Load all historical orders (10,000 rows)
orders = kaggle_order_repository.load_all()

# Get a specific order by ID (str, not UUID)
order = kaggle_order_repository.get_by_id("1d8e87M")

# Get all orders for a customer
orders = kaggle_order_repository.get_by_customer_id("9c6dbfcb-72c5-4cc4-9f76-29200f0efda7")

# Get all orders for a food item (used by pricing analytics)
orders = kaggle_order_repository.get_by_food_item("Pasta")
```

**KaggleOrder fields:**
```python
order_id:             str    # e.g. "1d8e87M"   — NOT UUID
restaurant_id:        str    # e.g. "16"         — NOT UUID
customer_id:          str    # UUID format string — NOT uuid.UUID object
food_item:            str
order_value:          float
order_time:           str
delivery_distance:    float
delivery_time_actual: float
delivery_delay:       float
```

---

## For delivery_service (Feat5)

```python
from app.repositories import kaggle_order_repository

# Get historical delivery data for analytics
orders = kaggle_order_repository.load_all()

# Fields relevant to delivery analytics:
# order.delivery_time_actual  → float (actual delivery time in minutes)
# order.delivery_delay        → float (delay in minutes, negative = early)
# order.delivery_distance     → float (distance in km)
```

---

## For restaurant_service / search_service (Feat2, Feat3)

```python
from app.services.restaurant_service import (
    list_restaurants,       # → list[KaggleRestaurant]
    get_restaurant,         # → KaggleRestaurant | None
    get_menu,               # → list[KaggleMenuItem]
)

# List all 100 restaurants
restaurants = list_restaurants()

# Get a specific restaurant
restaurant = get_restaurant("16")   # → KaggleRestaurant(restaurant_id="16", name="Restaurant_16")
restaurant = get_restaurant("999")  # → None

# Get menu for a restaurant (includes median_price per item)
menu = get_menu("16")
# → [KaggleMenuItem(restaurant_id="16", food_item="Pasta", median_price=35.0), ...]
```

**KaggleRestaurant fields:**
```python
restaurant_id: str    # e.g. "16"  — NOT UUID
name:          str    # "Restaurant_{restaurant_id}"
```

**KaggleMenuItem fields:**
```python
restaurant_id: str    # e.g. "16"  — NOT UUID
food_item:     str
median_price:  float  # precomputed from all order_value entries for this food_item
```

---

## ID Type Rules

| Data Source  | ID Type | Example            |
|--------------|---------|--------------------|
| Kaggle order | `str`   | `"1d8e87M"`        |
| Kaggle restaurant | `str` | `"16"`          |
| Kaggle customer | `str` | `"9c6dbfcb-..."`  |
| System order | `UUID`  | `uuid.uuid4()`     |
| System restaurant | `UUID` | `uuid.uuid4()` |
| System user  | `UUID`  | `uuid.uuid4()`     |

**Never pass a Kaggle str ID into a function expecting a UUID. The service layer enforces this boundary.**

---

## What This Branch Does NOT Include

- System restaurant / menu CRUD (Owner-managed) → `feat/restaurant-system`
- Authentication / RBAC → `feat/auth`
- Order creation → `feat/order-workflow`
- Pricing calculation logic → `feat/pricing` (uses `get_median_price` from this branch)
