from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "food_delivery.csv"


class SearchRepository:
    """
    This is the data access layer, which reads from the CSV.
    """

    def __init__(self, csv_path: Optional[Path] = None) -> None:
        self.csv_path = csv_path or DATA_PATH

    def load_all_rows(self) -> List[Dict[str, Any]]:
        if not self.csv_path.exists():
            return []

        with self.csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows: List[Dict[str, Any]] = []
            for r in reader:
                rows.append(dict(r))
            return rows