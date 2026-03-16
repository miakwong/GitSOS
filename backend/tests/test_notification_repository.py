import json
import uuid
from unittest.mock import patch

import pytest
from app.repositories import notification_repository
from app.schemas.notification import NotificationRecord

NOTIF_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()
ORDER_ID = uuid.uuid4()


def _make_record(user_id=None, is_read=False) -> NotificationRecord:
    return NotificationRecord(
        notification_id=NOTIF_ID,
        user_id=user_id or USER_ID,
        order_id=ORDER_ID,
        type="ORDER_CREATED",
        message="Test notification",
        is_read=is_read,
    )


@pytest.fixture(autouse=True)
def mock_data_file(tmp_path):
    data_file = tmp_path / "notifications.json"
    data_file.write_text("[]", encoding="utf-8")
    with patch.object(notification_repository, "DATA_PATH", str(data_file)):
        yield data_file


def test_create_saves_record(mock_data_file):
    notification_repository.create(_make_record())
    data = json.loads(mock_data_file.read_text())
    assert len(data) == 1
    assert data[0]["notification_id"] == str(NOTIF_ID)


def test_create_returns_record(mock_data_file):
    result = notification_repository.create(_make_record())
    assert isinstance(result, NotificationRecord)
    assert result.notification_id == NOTIF_ID


def test_get_by_id_found(mock_data_file):
    notification_repository.create(_make_record())
    result = notification_repository.get_by_id(NOTIF_ID)
    assert result is not None
    assert result.notification_id == NOTIF_ID


def test_get_by_id_not_found(mock_data_file):
    result = notification_repository.get_by_id(uuid.uuid4())
    assert result is None


def test_list_by_user_returns_own_only(mock_data_file):
    notification_repository.create(_make_record(user_id=USER_ID))
    notification_repository.create(_make_record(user_id=OTHER_USER_ID))
    results = notification_repository.list_by_user(USER_ID)
    assert len(results) == 1
    assert results[0].user_id == USER_ID


def test_list_all_returns_all(mock_data_file):
    notification_repository.create(_make_record(user_id=USER_ID))
    notification_repository.create(_make_record(user_id=OTHER_USER_ID))
    results = notification_repository.list_all()
    assert len(results) == 2


def test_update_read_status_marks_read(mock_data_file):
    notification_repository.create(_make_record(is_read=False))
    result = notification_repository.update_read_status(NOTIF_ID, True)
    assert result is not None
    assert result.is_read is True


def test_update_read_status_marks_unread(mock_data_file):
    notification_repository.create(_make_record(is_read=True))
    result = notification_repository.update_read_status(NOTIF_ID, False)
    assert result.is_read is False


def test_update_read_status_not_found(mock_data_file):
    result = notification_repository.update_read_status(uuid.uuid4(), True)
    assert result is None
