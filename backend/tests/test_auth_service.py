from pathlib import Path
import tempfile

import pytest

from app.services.auth_service import AuthService, TOKEN_BLACKLIST
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin

SECRET_KEY = "dev-secret-key-for-gitsos-project-authentication-12345"
ALGORITHM = "HS256"


@pytest.fixture
def auth_service():
    with tempfile.TemporaryDirectory() as temp_dir:
        users_file = Path(temp_dir) / "users.json"
        user_repo = UserRepository(users_file)
        TOKEN_BLACKLIST.clear()
        yield AuthService(user_repo=user_repo, secret_key=SECRET_KEY, algorithm=ALGORITHM)
        TOKEN_BLACKLIST.clear()


def test_register_user_success(auth_service):
    user = auth_service.register_user(
        UserCreate(email="user@test.com", password="secret12", role="customer")
    )

    assert user.email == "user@test.com"
    assert user.role == "customer"
    # make sure password is hashed
    assert user.password_hash != "secret12"


def test_login_user_returns_token(auth_service):
    auth_service.register_user(
        UserCreate(email="user@test.com", password="secret12", role="customer")
    )

    token = auth_service.login_user(
        UserLogin(email="user@test.com", password="secret12")
    )

    assert isinstance(token, str)
    assert token is not None


def test_logout_invalidates_token(auth_service):
    user = auth_service.register_user(
        UserCreate(email="user@test.com", password="secret12", role="customer")
    )

    token = auth_service.create_access_token(user.id, user.role)
    auth_service.logout_token(token)

    assert auth_service.is_token_invalidated(token) is True
    assert auth_service.verify_token(token) is None


def test_verify_token_valid(auth_service):
    user = auth_service.register_user(
        UserCreate(email="user@test.com", password="secret12", role="customer")
    )

    token = auth_service.create_access_token(user.id, user.role)
    user_id = auth_service.verify_token(token)

    assert user_id == str(user.id)


def test_verify_token_invalid(auth_service):
    result = auth_service.verify_token("not-a-real-token")

    assert result is None


def test_verify_token_expired(auth_service):
    user = auth_service.register_user(
        UserCreate(email="user@test.com", password="secret12", role="customer")
    )

    # use -1 minutes so token is already expired
    expired = AuthService(
        user_repo=auth_service.user_repo,
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        access_token_minutes=-1,
    )

    expired_token = expired.create_access_token(user.id, user.role)

    assert auth_service.verify_token(expired_token) is None
