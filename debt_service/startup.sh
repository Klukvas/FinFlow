#!/bin/bash

# Debt Service Startup Script
set -e

echo "Starting Debt Service..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the service
echo "Starting Debt Service on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
