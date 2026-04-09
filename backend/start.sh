#!/bin/sh
set -e

echo "=== GitSOS: running seed script ==="
python /app/scripts/seed_data.py

echo "=== GitSOS: starting server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
