#!/bin/bash
set -e

echo "Starting Scheduler Service..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the service
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8090
