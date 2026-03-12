import csv
import os

os.makedirs("backend/app/data", exist_ok=True)

headers = [
    "order_id",
    "customer_id",
    "restaurant_id",
    "food_item",
    "quantity",
    "order_value",
    "order_date",
    "order_time",
    "delivery_time",
    "order_status",
    "payment_method",
    "payment_status",
    "customer_lat",
    "customer_lon",
    "restaurant_lat",
    "restaurant_lon",
    "delivery_distance_km",
    "delivery_fee",
    "discount_applied",
    "discount_amount",
    "is_historical",
]

foods = [
    "Pizza",
    "Burger",
    "Sushi",
    "Pasta",
    "Salad",
    "Tacos",
    "Ramen",
    "Steak",
    "Curry",
    "Sandwich",
]

rows = [
    [
        f"ORD{i:04d}",
        f"C{i%10}",
        f"R{i%5}",
        foods[i % 10],
        1,
        10.0 + i,
        "2024-01-01",
        "12:00",
        "13:00",
        "Delivered",
        "Credit Card",
        "Paid",
        0.0,
        0.0,
        0.0,
        0.0,
        2.0,
        1.5,
        False,
        0.0,
        False,
    ]
    for i in range(50)
]

with open("backend/app/data/food_delivery.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(headers)
    w.writerows(rows)

print("Mock CSV created: 50 rows")
