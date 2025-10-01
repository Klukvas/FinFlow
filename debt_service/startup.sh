#!/bin/bash

# Debt Service Startup Script
set -e

echo "Starting Debt Service..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
else
    echo "No virtual environment detected. Creating one..."
    python3.11 -m venv .venv
    source .venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip

# Try to install with poetry first, fallback to pip
if command -v poetry &> /dev/null; then
    echo "Using Poetry to install dependencies..."
    poetry install
else
    echo "Poetry not found, using pip..."
    pip install -r requirements.txt
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the service
echo "Starting Debt Service on port 8008..."
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
