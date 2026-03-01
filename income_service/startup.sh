#!/bin/bash
set -e

# Wait for database to be ready
echo "Database host: ${DATABASE_URL#*@}"
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

echo "Waiting for database to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready - running migrations..."

# Run migrations
if alembic upgrade head 2>&1; then
    echo "Migrations completed successfully"
else
    echo "ERROR: Migration failed! Check logs above for details."
    echo "Starting application anyway — some features may not work."
fi

echo "Migrations completed - starting application..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

