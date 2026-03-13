# routers/notifications.py
from uuid import UUID

from app.dependencies import get_current_user_full
from app.repositories import notification_repository
from app.schemas.constants import ROLE_ADMIN, VALID_NOTIFICATION_TYPES
from app.schemas.notification import NotificationOut
from app.schemas.user import UserInDB
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationOut])
def list_my_notifications(
    current_user: UserInDB = Depends(get_current_user_full),
) -> list[NotificationOut]:
    """Return all notifications for the authenticated user."""
    records = notification_repository.list_by_user(current_user.id)
    return [NotificationOut.from_record(r) for r in records]


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: UUID,
    current_user: UserInDB = Depends(get_current_user_full),
) -> NotificationOut:
    """Mark a notification as read. Only the owning user may do this."""
    record = notification_repository.get_by_id(notification_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if str(record.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    updated = notification_repository.update_read_status(notification_id, is_read=True)
    return NotificationOut.from_record(updated)


@router.patch("/{notification_id}/unread", response_model=NotificationOut)
def mark_as_unread(
    notification_id: UUID,
    current_user: UserInDB = Depends(get_current_user_full),
) -> NotificationOut:
    """Mark a notification as unread. Only the owning user may do this."""
    record = notification_repository.get_by_id(notification_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if str(record.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    updated = notification_repository.update_read_status(notification_id, is_read=False)
    return NotificationOut.from_record(updated)


@router.get("/admin", response_model=list[NotificationOut])
def admin_list_notifications(
    notif_type: str | None = Query(
        None,
        description=f"Filter by type. One of: {VALID_NOTIFICATION_TYPES}",
    ),
    since: str | None = Query(
        None,
        description="ISO 8601 datetime — return only notifications created at or after this timestamp",
    ),
    until: str | None = Query(
        None,
        description="ISO 8601 datetime — return only notifications created before or at this timestamp",
    ),
    current_user: UserInDB = Depends(get_current_user_full),
) -> list[NotificationOut]:
    """Admin-only: list all notifications with optional filters."""
    if current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    if notif_type is not None and notif_type not in VALID_NOTIFICATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type. Must be one of: {VALID_NOTIFICATION_TYPES}",
        )
    records = notification_repository.list_all()
    if notif_type:
        records = [r for r in records if r.type == notif_type]
    if since:
        records = [r for r in records if r.created_at >= since]
    if until:
        records = [r for r in records if r.created_at <= until]
    return [NotificationOut.from_record(r) for r in records]
