from typing import Any, Dict, List, Optional

from fastapi import HTTPException

# Valid sort fields for each resource type
VALID_RESTAURANT_SORT_KEYS = {"restaurant_id", "restaurant_name"}
VALID_MENU_ITEM_SORT_KEYS = {"item_name", "price"}
VALID_ORDER_SORT_KEYS = {"order_id", "order_value"}


def sort_results(
    rows: List[Dict[str, Any]],
    sort_by: Optional[str],
    sort_order: str,
    valid_sort_keys: set,
) -> List[Dict[str, Any]]:
    # If no sort requested, just return the list as is
    if sort_by is None:
        return rows

    # Reject unsupported sort fields
    if sort_by not in valid_sort_keys:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Invalid sort_by value '{sort_by}'.",
                "allowed_sort_keys": sorted(valid_sort_keys),
            },
        )

    reverse = sort_order == "desc"

    # Separate rows that have a value for the sort field from those that don't.
    # This ensures None rows always go to the end, regardless of sort direction.
    has_value = [row for row in rows if row.get(sort_by) is not None]
    missing_value = [row for row in rows if row.get(sort_by) is None]

    def sort_key(row: Dict[str, Any]) -> Any:
        val = row.get(sort_by)
        # Strings are sorted case-insensitively
        if isinstance(val, str):
            return val.lower()
        return val

    return sorted(has_value, key=sort_key, reverse=reverse) + missing_value
