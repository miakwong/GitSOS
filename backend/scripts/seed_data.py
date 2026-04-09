"""
Comprehensive seed script for GitSOS development.
Runs automatically on Docker startup. Safe to run multiple times (idempotent).

Seed accounts:
  admin@test.com    / Admin1234
  owner@test.com    / Owner1234   (restaurant R0)
  customer@test.com / Customer1234

Seed data for customer@test.com:
  - 6 orders in various statuses (Delivered x2, Preparing, Paid, Placed, Cancelled)
  - 4 payments (for the non-Placed/Cancelled orders)
  - 2 reviews (for delivered orders)
  - 2 favourites
  - 14 notifications

Seed data for owner (restaurant R0):
  - Restaurant profile
  - 5 custom menu items

Idempotency: detected by a sentinel order ID prefix (all valid hex UUIDs).
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"

# All seed order IDs start with this — all valid hex, correct UUID shape
SEED_PREFIX = "aaaaaaaa-0000-4000-8000-"


def load(name: str) -> list:
    p = DATA_DIR / f"{name}.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save(name: str, data: list) -> None:
    p = DATA_DIR / f"{name}.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ts(offset_minutes: int = 0) -> str:
    base = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(minutes=offset_minutes)).isoformat()


def oid(n: int) -> str:
    """Seed order UUID — valid hex, identifiable by SEED_PREFIX."""
    return f"{SEED_PREFIX}{n:012d}"


def pid(n: int) -> str:
    return f"bbbbbbbb-0000-4000-8000-{n:012d}"


def rid(n: int) -> str:
    return f"cccccccc-0000-4000-8000-{n:012d}"


def fid(n: int) -> str:
    return f"dddddddd-0000-4000-8000-{n:012d}"


def nid(n: int) -> str:
    return f"eeeeeeee-0000-4000-8000-{n:012d}"


def main() -> None:
    # ── 1. Ensure seed users exist ────────────────────────────────────────────
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserCreate
    from app.services.auth_service import AuthService

    SECRET_KEY = "dev-secret-key-for-gitsos-project-authentication-12345"
    repo = UserRepository(data_file=DATA_DIR / "users.json")
    auth = AuthService(user_repo=repo, secret_key=SECRET_KEY)

    for u in [
        UserCreate(email="admin@test.com",    password="Admin1234",    role="admin"),
        UserCreate(email="owner@test.com",    password="Owner1234",    role="owner", restaurant_id=0),
        UserCreate(email="customer@test.com", password="Customer1234", role="customer"),
    ]:
        try:
            created = auth.register_user(u)
            print(f"  [users] created  {created.email} ({created.role})")
        except ValueError:
            print(f"  [users] exists   {u.email}")

    # ── 2. Resolve user IDs ───────────────────────────────────────────────────
    by_email = {u["email"]: u["id"] for u in load("users")}
    customer_id = by_email.get("customer@test.com")
    if not customer_id:
        print("  [seed] ERROR: customer@test.com not found — aborting")
        return

    # ── 3. Idempotency check ──────────────────────────────────────────────────
    existing_orders = load("orders")
    if any(o.get("order_id", "").startswith(SEED_PREFIX) for o in existing_orders):
        print("  [seed] seed data already present — skipping")
        return

    # ── 3b. Clean any legacy bad seed entries ────────────────────────────────
    BAD_PREFIX = "a1seed0-"
    for name, key in [("orders","order_id"),("payments","order_id"),("favourites","order_id"),("notifications","order_id"),("reviews","order_id")]:
        data = load(name)
        cleaned = [r for r in data if not r.get(key, "").startswith(BAD_PREFIX)]
        if len(cleaned) != len(data):
            save(name, cleaned)
            print(f"  [seed] cleaned {len(data)-len(cleaned)} legacy bad entries from {name}.json")

    print("  [seed] inserting seed data …")

    # ── 4. Restaurant profile for R0 ──────────────────────────────────────────
    profiles = load("restaurant_profiles")
    if not any(p.get("restaurant_id") == "R0" for p in profiles):
        profiles.append({
            "restaurant_id": "R0",
            "name": "The Test Kitchen",
            "city": "Vancouver",
            "cuisine": "International",
            "description": "Owner's demo restaurant for GitSOS development.",
            "image_url": None,
        })
        save("restaurant_profiles", profiles)
        print("  [seed] restaurant profile R0 created")

    # ── 5. Menu items for R0 ─────────────────────────────────────────────────
    menu_items = load("menu_items")
    seed_menu = [
        {"food_item": "Margherita Pizza",   "restaurant_id": "R0", "price": 12.99},
        {"food_item": "BBQ Chicken Burger", "restaurant_id": "R0", "price": 14.50},
        {"food_item": "Caesar Salad",       "restaurant_id": "R0", "price":  9.99},
        {"food_item": "Garlic Bread",       "restaurant_id": "R0", "price":  5.50},
        {"food_item": "Chocolate Lava Cake","restaurant_id": "R0", "price":  7.99},
    ]
    existing_keys = {(m["food_item"], m.get("restaurant_id")) for m in menu_items}
    new_items = [i for i in seed_menu if (i["food_item"], i["restaurant_id"]) not in existing_keys]
    if new_items:
        menu_items.extend(new_items)
        save("menu_items", menu_items)
        print(f"  [seed] {len(new_items)} menu items added for R0")

    # ── 6. Orders ─────────────────────────────────────────────────────────────
    seed_orders = [
        # 1 — Delivered at R0
        {"order_id": oid(1), "customer_id": customer_id, "restaurant_id": 0, "food_item": "Margherita Pizza",   "order_time": ts(0),   "order_value": 12.99, "delivery_distance": 3.5, "delivery_method": "Bike", "traffic_condition": "Low",    "weather_condition": "Sunny", "order_status": "Delivered", "actual_delivery_time": 28.0, "delivery_delay": -2.0},
        # 2 — Delivered at R0
        {"order_id": oid(2), "customer_id": customer_id, "restaurant_id": 0, "food_item": "BBQ Chicken Burger", "order_time": ts(60),  "order_value": 14.50, "delivery_distance": 4.0, "delivery_method": "Car",  "traffic_condition": "Medium", "weather_condition": "Rainy", "order_status": "Delivered", "actual_delivery_time": 40.0, "delivery_delay":  5.0},
        # 3 — Preparing at R0
        {"order_id": oid(3), "customer_id": customer_id, "restaurant_id": 0, "food_item": "Caesar Salad",       "order_time": ts(120), "order_value":  9.99, "delivery_distance": 2.5, "delivery_method": "Walk", "traffic_condition": "Low",    "weather_condition": "Sunny", "order_status": "Preparing", "actual_delivery_time": None, "delivery_delay": None},
        # 4 — Paid at R0
        {"order_id": oid(4), "customer_id": customer_id, "restaurant_id": 0, "food_item": "Garlic Bread",       "order_time": ts(180), "order_value":  5.50, "delivery_distance": 3.0, "delivery_method": "Bike", "traffic_condition": "High",   "weather_condition": "Snowy", "order_status": "Paid",      "actual_delivery_time": None, "delivery_delay": None},
        # 5 — Placed at R0
        {"order_id": oid(5), "customer_id": customer_id, "restaurant_id": 0, "food_item": "Chocolate Lava Cake","order_time": ts(240), "order_value":  7.99, "delivery_distance": 3.0, "delivery_method": "Bike", "traffic_condition": "Low",    "weather_condition": "Sunny", "order_status": "Placed",    "actual_delivery_time": None, "delivery_delay": None},
        # 6 — Cancelled at R16
        {"order_id": oid(6), "customer_id": customer_id, "restaurant_id": 16, "food_item": "Tacos",             "order_time": ts(300), "order_value": 11.99, "delivery_distance": 5.0, "delivery_method": "Bike", "traffic_condition": "Low",    "weather_condition": "Rainy", "order_status": "Cancelled", "actual_delivery_time": None, "delivery_delay": None},
    ]
    existing_orders.extend(seed_orders)
    save("orders", existing_orders)
    print(f"  [seed] {len(seed_orders)} orders added")

    # ── 7. Payments ───────────────────────────────────────────────────────────
    payments = load("payments")
    existing_pay_oids = {p["order_id"] for p in payments}
    seed_payments = [
        {"payment_id": pid(1), "order_id": oid(1), "customer_id": customer_id, "status": "Success", "amount": 12.99, "created_at": ts(1),   "updated_at": None},
        {"payment_id": pid(2), "order_id": oid(2), "customer_id": customer_id, "status": "Success", "amount": 14.50, "created_at": ts(61),  "updated_at": None},
        {"payment_id": pid(3), "order_id": oid(3), "customer_id": customer_id, "status": "Success", "amount":  9.99, "created_at": ts(121), "updated_at": None},
        {"payment_id": pid(4), "order_id": oid(4), "customer_id": customer_id, "status": "Success", "amount":  5.50, "created_at": ts(181), "updated_at": None},
    ]
    new_payments = [p for p in seed_payments if p["order_id"] not in existing_pay_oids]
    if new_payments:
        payments.extend(new_payments)
        save("payments", payments)
        print(f"  [seed] {len(new_payments)} payments added")

    # ── 8. Reviews ────────────────────────────────────────────────────────────
    reviews = load("reviews")
    existing_rids = {r["review_id"] for r in reviews}
    seed_reviews = [
        {"review_id": rid(1), "order_id": oid(1), "customer_id": customer_id, "restaurant_id": 0, "rating": 5, "tags": ["Delicious", "Fast delivery"], "created_at": ts(30)},
        {"review_id": rid(2), "order_id": oid(2), "customer_id": customer_id, "restaurant_id": 0, "rating": 4, "tags": ["Just okay", "On time"],        "created_at": ts(90)},
    ]
    new_reviews = [r for r in seed_reviews if r["review_id"] not in existing_rids]
    if new_reviews:
        reviews.extend(new_reviews)
        save("reviews", reviews)
        print(f"  [seed] {len(new_reviews)} reviews added")

    # ── 9. Favourites ─────────────────────────────────────────────────────────
    favourites = load("favourites")
    existing_fids = {f["favourite_id"] for f in favourites}
    seed_favs = [
        {"favourite_id": fid(1), "order_id": oid(1), "customer_id": customer_id, "created_at": ts(35)},
        {"favourite_id": fid(2), "order_id": oid(2), "customer_id": customer_id, "created_at": ts(95)},
    ]
    new_favs = [f for f in seed_favs if f["favourite_id"] not in existing_fids]
    if new_favs:
        favourites.extend(new_favs)
        save("favourites", favourites)
        print(f"  [seed] {len(new_favs)} favourites added")

    # ── 10. Notifications ─────────────────────────────────────────────────────
    notifications = load("notifications")
    existing_nids = {n["notification_id"] for n in notifications}
    seed_notifs = [
        {"notification_id": nid(1),  "user_id": customer_id, "order_id": oid(1), "type": "ORDER_CREATED",          "message": "Your order for Margherita Pizza has been placed.",    "is_read": True,  "created_at": ts(0)},
        {"notification_id": nid(2),  "user_id": customer_id, "order_id": oid(1), "type": "PAYMENT_STATUS_CHANGED", "message": "Your payment of $12.99 is Success.",                  "is_read": True,  "created_at": ts(1)},
        {"notification_id": nid(3),  "user_id": customer_id, "order_id": oid(1), "type": "ORDER_STATUS_CHANGED",   "message": "Your Margherita Pizza order is now Delivered.",      "is_read": True,  "created_at": ts(28)},
        {"notification_id": nid(4),  "user_id": customer_id, "order_id": oid(2), "type": "ORDER_CREATED",          "message": "Your order for BBQ Chicken Burger has been placed.", "is_read": True,  "created_at": ts(60)},
        {"notification_id": nid(5),  "user_id": customer_id, "order_id": oid(2), "type": "PAYMENT_STATUS_CHANGED", "message": "Your payment of $14.50 is Success.",                  "is_read": True,  "created_at": ts(61)},
        {"notification_id": nid(6),  "user_id": customer_id, "order_id": oid(2), "type": "ORDER_STATUS_CHANGED",   "message": "Your BBQ Chicken Burger order is now Delivered.",    "is_read": True,  "created_at": ts(100)},
        {"notification_id": nid(7),  "user_id": customer_id, "order_id": oid(3), "type": "ORDER_CREATED",          "message": "Your order for Caesar Salad has been placed.",       "is_read": False, "created_at": ts(120)},
        {"notification_id": nid(8),  "user_id": customer_id, "order_id": oid(3), "type": "PAYMENT_STATUS_CHANGED", "message": "Your payment of $9.99 is Success.",                   "is_read": False, "created_at": ts(121)},
        {"notification_id": nid(9),  "user_id": customer_id, "order_id": oid(3), "type": "ORDER_STATUS_CHANGED",   "message": "Your Caesar Salad order is now Preparing.",          "is_read": False, "created_at": ts(125)},
        {"notification_id": nid(10), "user_id": customer_id, "order_id": oid(4), "type": "ORDER_CREATED",          "message": "Your order for Garlic Bread has been placed.",       "is_read": False, "created_at": ts(180)},
        {"notification_id": nid(11), "user_id": customer_id, "order_id": oid(4), "type": "PAYMENT_STATUS_CHANGED", "message": "Your payment of $5.50 is Success.",                   "is_read": False, "created_at": ts(181)},
        {"notification_id": nid(12), "user_id": customer_id, "order_id": oid(5), "type": "ORDER_CREATED",          "message": "Your order for Chocolate Lava Cake has been placed.","is_read": False, "created_at": ts(240)},
        {"notification_id": nid(13), "user_id": customer_id, "order_id": oid(6), "type": "ORDER_CREATED",          "message": "Your order for Tacos has been placed.",              "is_read": True,  "created_at": ts(300)},
        {"notification_id": nid(14), "user_id": customer_id, "order_id": oid(6), "type": "ORDER_STATUS_CHANGED",   "message": "Your Tacos order is now Cancelled.",                 "is_read": True,  "created_at": ts(301)},
    ]
    new_notifs = [n for n in seed_notifs if n["notification_id"] not in existing_nids]
    if new_notifs:
        notifications.extend(new_notifs)
        save("notifications", notifications)
        print(f"  [seed] {len(new_notifs)} notifications added")

    print("  [seed] done ✓")


if __name__ == "__main__":
    main()
