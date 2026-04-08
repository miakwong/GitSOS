# GitSOS
Food delivery platform (COSC 310) — FastAPI REST API + Next.js frontend, Docker, auth/roles, pytest, CI

## Getting Started

### Run the full stack (backend + frontend)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Test accounts

Register a new account at http://localhost:3000/register, or use the seed script to create test accounts:

```bash
python backend/scripts/seed_users.py
```

| Email | Password | Role |
|-------|----------|------|
| admin@test.com | Admin1234 | admin |
| owner@test.com | Owner1234 | owner (restaurant 0) |
| customer@test.com | Customer1234 | customer |

### Run tests

```bash
cd backend && pytest
```
