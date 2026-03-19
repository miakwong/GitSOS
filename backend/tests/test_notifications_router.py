import uuid
from unittest.mock import patch

import pytest
from app.dependencies import get_current_user_full
from app.main import app
from app.schemas.constants import NOTIF_ORDER_CREATED, NOTIF_PAYMENT_STATUS_CHANGED
from app.schemas.notification import NotificationRecord
from app.schemas.user import UserInDB
from fastapi.testclient import TestClient

USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()
ORDER_ID = uuid.uuid4()
NOTIF_ID = uuid.uuid4()

MOCK_USER = UserInDB(
    id=USER_ID,
    email="user@example.com",
    role="customer",
    password_hash="hashed",
)

MOCK_RECORD = NotificationRecord(
    notification_id=NOTIF_ID,
    user_id=USER_ID,
    order_id=ORDER_ID,
    type=NOTIF_ORDER_CREATED,
    message="Your order has been placed.",
)

OTHER_RECORD = NotificationRecord(
    notification_id=uuid.uuid4(),
    user_id=OTHER_USER_ID,
    order_id=ORDER_ID,
    type=NOTIF_PAYMENT_STATUS_CHANGED,
    message="Another user's notification.",
)

MOCK_ADMIN = UserInDB(
    id=uuid.uuid4(),
    email="admin@example.com",
    role="admin",
    password_hash="hashed",
)


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user_full] = lambda: MOCK_USER
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# --- GET /notifications/ ---


def test_list_my_notifications_returns_own():
    with patch(
        "app.routers.notifications.notification_repository.list_by_user",
        return_value=[MOCK_RECORD],
    ):
        response = client.get("/notifications/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["notification_id"] == str(NOTIF_ID)
    assert data[0]["user_id"] == str(USER_ID)


def test_list_my_notifications_empty():
    with patch(
        "app.routers.notifications.notification_repository.list_by_user",
        return_value=[],
    ):
        response = client.get("/notifications/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_notifications_requires_auth():
    app.dependency_overrides.clear()
    response = client.get("/notifications/")
    assert response.status_code == 401


# --- PATCH /notifications/{id}/read ---


def test_mark_as_read_success():
    updated = MOCK_RECORD.model_copy(update={"is_read": True})
    with (
        patch(
            "app.routers.notifications.notification_repository.get_by_id",
            return_value=MOCK_RECORD,
        ),
        patch(
            "app.routers.notifications.notification_repository.update_read_status",
            return_value=updated,
        ),
    ):
        response = client.patch(f"/notifications/{NOTIF_ID}/read")
    assert response.status_code == 200
    assert response.json()["is_read"] is True


def test_mark_as_read_not_found():
    with patch(
        "app.routers.notifications.notification_repository.get_by_id",
        return_value=None,
    ):
        response = client.patch(f"/notifications/{NOTIF_ID}/read")
    assert response.status_code == 404


def test_mark_as_read_forbidden():
    """User cannot mark another user's notification as read."""
    with patch(
        "app.routers.notifications.notification_repository.get_by_id",
        return_value=OTHER_RECORD,
    ):
        response = client.patch(f"/notifications/{OTHER_RECORD.notification_id}/read")
    assert response.status_code == 403


# --- PATCH /notifications/{id}/unread ---


def test_mark_as_unread_success():
    read_record = MOCK_RECORD.model_copy(update={"is_read": True})
    updated = MOCK_RECORD.model_copy(update={"is_read": False})
    with (
        patch(
            "app.routers.notifications.notification_repository.get_by_id",
            return_value=read_record,
        ),
        patch(
            "app.routers.notifications.notification_repository.update_read_status",
            return_value=updated,
        ),
    ):
        response = client.patch(f"/notifications/{NOTIF_ID}/unread")
    assert response.status_code == 200
    assert response.json()["is_read"] is False


def test_mark_as_unread_forbidden():
    with patch(
        "app.routers.notifications.notification_repository.get_by_id",
        return_value=OTHER_RECORD,
    ):
        response = client.patch(f"/notifications/{OTHER_RECORD.notification_id}/unread")
    assert response.status_code == 403


# --- GET /notifications/admin ---


def test_admin_list_all():
    app.dependency_overrides[get_current_user_full] = lambda: MOCK_ADMIN
    with patch(
        "app.routers.notifications.notification_repository.list_all",
        return_value=[MOCK_RECORD, OTHER_RECORD],
    ):
        response = client.get("/notifications/admin")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_admin_filter_by_type():
    app.dependency_overrides[get_current_user_full] = lambda: MOCK_ADMIN
    with patch(
        "app.routers.notifications.notification_repository.list_all",
        return_value=[MOCK_RECORD, OTHER_RECORD],
    ):
        response = client.get(f"/notifications/admin?notif_type={NOTIF_ORDER_CREATED}")
    assert response.status_code == 200
    result = response.json()
    assert all(r["type"] == NOTIF_ORDER_CREATED for r in result)


def test_admin_filter_invalid_type():
    app.dependency_overrides[get_current_user_full] = lambda: MOCK_ADMIN
    response = client.get("/notifications/admin?notif_type=INVALID_TYPE")
    assert response.status_code == 400


def test_admin_endpoint_forbidden_for_non_admin():
    response = client.get("/notifications/admin")
    assert response.status_code == 403
