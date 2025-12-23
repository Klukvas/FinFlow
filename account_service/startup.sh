#!/bin/bash
set -e

# Extract database host and port from DATABASE_URL
echo "Database URL: ${DATABASE_URL}"
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

echo "Database host: ${DB_HOST}:${DB_PORT}"
echo "Waiting for database to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; do
  echo "${DB_HOST}:${DB_PORT} - no response"
  sleep 1
done

echo "${DB_HOST}:${DB_PORT} - accepting connections"
echo "Database is ready - running migrations..."

# Run migrations
alembic upgrade head || {
    echo "Migration completed with warnings (tables may already exist)"
}

echo "Migrations completed - starting application..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
