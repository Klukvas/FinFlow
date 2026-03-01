#!/bin/bash
set -e

echo "Starting goals_service..."

# Extract DB host from DATABASE_URL or use default
DB_HOST_PARSED=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_HOST_PARSED=${DB_HOST_PARSED:-db}

# Wait for database to be ready
echo "Waiting for database at ${DB_HOST_PARSED}:5432..."
until pg_isready -h "$DB_HOST_PARSED" -p 5432 -U postgres 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done
echo "Database is ready!"

# Run Alembic migrations
echo "Running database migrations..."
if alembic upgrade head 2>&1; then
    echo "Migrations completed successfully"
else
    echo "ERROR: Migration failed! Check logs above for details."
    echo "Starting application anyway — some features may not work."
fi

echo "Migrations completed - starting application..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
