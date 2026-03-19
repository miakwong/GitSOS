from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).parent.parent / "data"
PRICING_RECORDS_PATH = DATA_DIR / "pricing_records.json"


class PricingRepository:
    def __init__(self, file_path: Path = PRICING_RECORDS_PATH) -> None:
        self.file_path = file_path

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []

        with open(self.file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data if data else []
            except json.JSONDecodeError:
                return []

    def _save_records(self, records: list[dict[str, Any]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def save_breakdown(self, breakdown: dict[str, Any]) -> None:
        records = self._load_records()
        records.append(breakdown)
        self._save_records(records)