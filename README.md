# GitSOS
Food delivery platform (COSC 310) — FastAPI REST API + frontend (M4), Docker, auth/roles, Pytest, CI

## Getting Started

### 1. Start the backend

```bash
docker-compose up --build
```

API runs at http://localhost:8000. Docs at http://localhost:8000/docs.

### 2. Seed test users

User data is not tracked in git. Run this once after starting the container to create local test accounts:

```bash
python backend/scripts/seed_users.py
```

This creates three accounts (skips any that already exist):

| Email | Password | Role |
|-------|----------|------|
| admin@test.com | Admin1234 | admin |
| owner@test.com | Owner1234 | owner (restaurant 0) |
| customer@test.com | Customer1234 | customer |

### 3. Run tests

```bash
cd backend && pytest
```
