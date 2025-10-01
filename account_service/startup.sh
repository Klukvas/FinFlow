#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready - continuing"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting Account Service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
