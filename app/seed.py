from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from app.db import DB_PATH


def seed() -> None:
    random.seed(7)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS order_items;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS regions;
            CREATE TABLE regions (region_id TEXT PRIMARY KEY, region_name TEXT NOT NULL);
            CREATE TABLE products (
                product_id TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL
            );
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                order_date TEXT NOT NULL,
                region_id TEXT NOT NULL REFERENCES regions(region_id),
                returned INTEGER NOT NULL DEFAULT 0 CHECK (returned IN (0, 1))
            );
            CREATE TABLE order_items (
                order_id TEXT NOT NULL REFERENCES orders(order_id),
                product_id TEXT NOT NULL REFERENCES products(product_id),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price > 0),
                discount REAL NOT NULL CHECK (discount >= 0 AND discount <= 1)
            );
            """
        )
        regions = [("north", "North"), ("south", "South"), ("east", "East"), ("west", "West")]
        products = [
            ("p01", "Atlas Chair", "Furniture"),
            ("p02", "Breeze Desk", "Furniture"),
            ("p03", "Cobalt Lamp", "Office"),
            ("p04", "Dune Notebook", "Stationery"),
            ("p05", "Echo Monitor", "Electronics"),
            ("p06", "Fjord Keyboard", "Electronics"),
            ("p07", "Grove Backpack", "Accessories"),
            ("p08", "Harbor Headset", "Electronics"),
        ]
        connection.executemany("INSERT INTO regions VALUES (?, ?)", regions)
        connection.executemany("INSERT INTO products VALUES (?, ?, ?)", products)
        start = date(2024, 1, 1)
        order_rows: list[tuple[str, str, str, int]] = []
        item_rows: list[tuple[str, str, int, float, float]] = []
        prices = {product_id: random.uniform(18, 240) for product_id, _, _ in products}
        for index in range(1, 481):
            order_id = f"o{index:04d}"
            day = start + timedelta(days=random.randrange(366))
            region = regions[(index * 3 + random.randrange(4)) % len(regions)][0]
            returned = int(random.random() < (0.18 if day.month >= 7 else 0.1))
            order_rows.append((order_id, day.isoformat(), region, returned))
            product_id = products[(index * 5 + random.randrange(len(products))) % len(products)][0]
            quantity = 1 + random.randrange(5)
            discount = round(random.choice([0, 0.05, 0.1, 0.15]), 2)
            item_rows.append((order_id, product_id, quantity, round(prices[product_id], 2), discount))
        connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", order_rows)
        connection.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", item_rows)


if __name__ == "__main__":
    seed()
    print(f"Seeded {DB_PATH}")

