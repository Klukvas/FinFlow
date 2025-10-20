#!/bin/sh
set -euo pipefail

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8080


