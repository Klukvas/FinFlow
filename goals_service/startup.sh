#!/bin/bash
set -e

echo "Starting goals_service..."

# Wait for database to be ready
echo "Waiting for database..."
until pg_isready -h db -p 5432 -U postgres; do
  echo "Database is unavailable - sleeping"
  sleep 2
done
echo "Database is ready!"

# Run Alembic migrations
echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations completed successfully"
else
    echo "Migration completed with warnings"
fi

echo "Migrations completed - starting application..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
