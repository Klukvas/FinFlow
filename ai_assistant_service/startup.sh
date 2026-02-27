#!/bin/bash
set -euo pipefail

echo "Starting AI Assistant Service..."

# No database, no migrations needed — stateless service with Redis cache

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    --workers 2 \
    --timeout-keep-alive 30 \
    --limit-concurrency 50
