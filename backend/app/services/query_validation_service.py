from __future__ import annotations

from typing import Any, Dict, Set
from fastapi import HTTPException


class QueryValidationService:
    @staticmethod
    def reject_unsupported_filters(
        provided_params: Dict[str, Any],
        allowed_filters: Set[str],
    ) -> None:
        unsupported = [
            key
            for key, value in provided_params.items()
            if value not in (None, "") and key not in allowed_filters
        ]

        if unsupported:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Unsupported query parameter(s).",
                    "unsupported": unsupported,
                    "allowed": sorted(list(allowed_filters)),
                },
            )

    @staticmethod
    def validate_price_range(
        min_price: float | None,
        max_price: float | None,
    ) -> None:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Invalid price range.",
                    "reason": "min_price cannot be greater than max_price.",
                },
            )

    @staticmethod
    def validate_order_value_range(
        min_order_value: float | None,
        max_order_value: float | None,
    ) -> None:
        if (
            min_order_value is not None
            and max_order_value is not None
            and min_order_value > max_order_value
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Invalid order value range.",
                    "reason": "min_order_value cannot be greater than max_order_value.",
                },
            )