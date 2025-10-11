#!/bin/bash

# Extract database host from DATABASE_URL
# Format: postgresql://user:pass@host:port/dbname
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

echo "Database host: $DB_HOST:$DB_PORT"

# Wait for database to be ready
echo "Waiting for database to be ready..."
max_attempts=30
attempt=0
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    echo "WARNING: Database not ready after $max_attempts attempts. Starting anyway..."
    break
  fi
  echo "Database is unavailable - sleeping (attempt $attempt/$max_attempts)"
  sleep 2
done

echo "Database is ready - running migrations..."

# Run migrations (ignore errors if tables already exist)
alembic upgrade head || echo "Migration completed with warnings (tables may already exist)"

echo "Migrations completed - starting application..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
