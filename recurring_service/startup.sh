#!/bin/bash

# Ждать пока база данных будет готова
echo "Waiting for database to be ready..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done

echo "Database is ready!"

# Выполнить миграции
echo "Running database migrations..."
alembic upgrade head

# Запустить приложение
echo "Starting Recurring Payments Service..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
