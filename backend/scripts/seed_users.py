"""
Seed test users into users.json for local development.

Usage (from project root):
    python backend/scripts/seed_users.py

Creates three test accounts (skips any that already exist):
    admin@test.com    / Admin1234     role: admin
    owner@test.com    / Owner1234     role: owner  (restaurant_id: 16)
    customer@test.com / Customer1234  role: customer
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService

USERS = [
    UserCreate(email="admin@test.com", password="Admin1234", role="admin"),
    UserCreate(
        email="owner@test.com", password="Owner1234", role="owner", restaurant_id=16
    ),
    UserCreate(email="customer@test.com", password="Customer1234", role="customer"),
]

SECRET_KEY = "dev-secret-key-for-gitsos-project-authentication-12345"


def main():
    data_file = Path(__file__).parent.parent / "app" / "data" / "users.json"
    repo = UserRepository(data_file=data_file)
    auth = AuthService(user_repo=repo, secret_key=SECRET_KEY)

    for user in USERS:
        try:
            created = auth.register_user(user)
            print(f"  created : {created.email} ({created.role})")
        except ValueError:
            print(f"  skipped : {user.email} (already exists)")


if __name__ == "__main__":
    main()
