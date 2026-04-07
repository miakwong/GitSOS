from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "food_delivery.csv"
ORDERS_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.json"


class SearchRepository:
    """
    This is the data access layer, which reads from the CSV.
    """

    def __init__(
        self,
        csv_path: Optional[Path] = None,
        orders_path: Optional[Path] = None,
    ) -> None:
        self.csv_path = csv_path or DATA_PATH
        self.orders_path = orders_path or ORDERS_PATH

    def load_all_rows(self) -> List[Dict[str, Any]]:
        if not self.csv_path.exists():
            return []

        with self.csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows: List[Dict[str, Any]] = []
            for r in reader:
                rows.append(dict(r))
            return rows

    def load_system_orders(self) -> List[Dict[str, Any]]:
        if not self.orders_path.exists():
            return []
        with self.orders_path.open("r", encoding="utf-8") as f:
            return json.load(f)
