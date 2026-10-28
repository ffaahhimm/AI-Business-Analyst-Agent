from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", ROOT / "data" / "retail.db"))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def query(sql: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as connection:
        return [dict(row) for row in connection.execute(sql, parameters).fetchall()]


def schema() -> dict[str, dict[str, str]]:
    return {
        "orders": {
            "order_id": "TEXT",
            "order_date": "TEXT",
            "region_id": "TEXT",
            "returned": "INTEGER",
        },
        "order_items": {
            "order_id": "TEXT",
            "product_id": "TEXT",
            "quantity": "INTEGER",
            "unit_price": "REAL",
            "discount": "REAL",
        },
        "products": {
            "product_id": "TEXT",
            "product_name": "TEXT",
            "category": "TEXT",
        },
        "regions": {"region_id": "TEXT", "region_name": "TEXT"},
    }

