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

    # Sort the rows — rows missing the field go to the end
    def sort_key(row: Dict[str, Any]) -> Any:
        val = row.get(sort_by)
        if val is None:
            # Put rows with missing field at the end
            return (1, "")
        # Strings are sorted case-insensitively
        if isinstance(val, str):
            return (0, val.lower())
        return (0, val)

    return sorted(rows, key=sort_key, reverse=reverse)
