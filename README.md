# GitSOS

Food delivery platform (COSC 310) — FastAPI backend + Next.js frontend, containerised with Docker.

- **GitHub**: https://github.com/miakwong/GitSOS
- **Team**: Mia Kuang, Kianan B, Mason Liu, Nikki Sidhu

---

## Quick Start

### Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker Desktop | 24.x |
| Docker Compose | v2.x (bundled with Docker Desktop) |
| Git | any recent version |

No other tools are required — Python, Node.js, and all dependencies run inside containers.

### 1. Clone the repository

```bash
git clone https://github.com/miakwong/GitSOS.git
cd GitSOS
```

### 2. Start the full stack

```bash
docker compose up --build
```

This command builds both images and starts two containers:

| Service | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend API (FastAPI) | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

The backend automatically seeds test data on first startup (via `backend/start.sh`).

### 3. Stop the stack

```bash
docker compose down
```

---

## Test Accounts

These accounts are created automatically by the seed script on first boot:

| Email | Password | Role |
|-------|----------|------|
| admin@test.com | Admin1234 | Admin |
| owner@test.com | Owner1234 | Restaurant Owner (Restaurant #0) |
| customer@test.com | Customer1234 | Customer |

You can also register a new customer account at http://localhost:3000/register.

---

## Project Structure

```
GitSOS/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── data/             # JSON + CSV data files
│   │   ├── repositories/     # Data access layer
│   │   ├── routers/          # API route handlers
│   │   ├── schemas/          # Pydantic models & constants
│   │   └── services/         # Business logic
│   ├── scripts/              # seed_data.py
│   ├── tests/                # pytest test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── start.sh              # Seeds data then starts uvicorn
├── frontend/                 # Next.js application
│   ├── app/                  # App Router pages
│   ├── components/           # Shared UI components
│   └── Dockerfile
└── docker-compose.yml
```

---

## Dependencies

### Backend (Python 3.11)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.135.1 | Web framework |
| uvicorn | 0.34.3 | ASGI server |
| pydantic | 2.12.5 | Data validation |
| PyJWT | 2.10.1 | JWT authentication |
| passlib / bcrypt | 1.7.4 / 4.2.1 | Password hashing |
| python-multipart | 0.0.20 | Form data parsing |
| pytest | 9.0.2 | Test runner |
| httpx | 0.28.1 | Test HTTP client |

Full list: `backend/requirements.txt`

### Frontend (Node.js 20)

| Package | Purpose |
|---------|---------|
| Next.js 15 | React framework (App Router) |
| Tailwind CSS | Styling |
| shadcn/ui | Component library |
| axios | HTTP client |

Full list: `frontend/package.json`

---

## Running Tests

```bash
cd backend && pytest
```

Or with coverage:

```bash
cd backend && pytest --cov=app tests/
```

---

## Data Management

All application data is stored as JSON files in `backend/app/data/`:

| File | Contents |
|------|----------|
| `orders.json` | System-created orders |
| `payments.json` | Payment records |
| `notifications.json` | User notifications |
| `reviews.json` | Customer reviews |
| `favourites.json` | Saved favourites |
| `users.json` | Registered user accounts |
| `menu_items.json` | Restaurant menu items |
| `food_delivery.csv` | Kaggle historical dataset |

The `backend/app/data/` directory is mounted as a Docker volume, so data persists across container restarts without rebuilding the image.

To reset to seed data, remove the container and rebuild:

```bash
docker compose down && docker compose up --build
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL used by the frontend |
| `ENVIRONMENT` | `development` | Backend environment flag |

These are set in `docker-compose.yml` and require a rebuild (`--build`) to take effect.

---

## TA Repository Access

GitHub usernames with admin access: **Anubhav2806**, **TWright-28**

---

## Team Members

| Name | GitHub Username |
|------|----------------|
| Mia Kuang | miakwong |
| Kianan B | Kiananb |
| Mason Liu | mason-liuuu |
| Nikki Sidhu | msidhu21 |
