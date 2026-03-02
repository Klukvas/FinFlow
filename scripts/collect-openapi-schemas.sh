#!/usr/bin/env bash
# Downloads OpenAPI JSON schemas from all running microservices.
# Usage: ./scripts/collect-openapi-schemas.sh [base_url]
# Must be run from the repository root.
set -euo pipefail

BASE_URL="${1:-http://localhost}"
OUT_DIR="frontend/src/types/generated/schemas"
mkdir -p "$OUT_DIR"

# service_name:port pairs
SERVICES="
user_service:8001
category_service:8002
expense_service:8003
income_service:8004
recurring_service:8005
goals_service:8006
pdf_parser_service:8007
debt_service:8008
account_service:8009
currency_service:8010
subscription_service:8011
workspace_service:8012
payment_service:8013
scheduler_service:8014
ai_assistant_service:8015
bank_sync_service:8016
"

FAILED=0
FETCHED=0
TOTAL=0

for entry in ${SERVICES}; do
  NAME="${entry%%:*}"
  PORT="${entry##*:}"
  TOTAL=$((TOTAL + 1))

  TMPFILE=$(mktemp)
  if curl -sf --max-time 30 "${BASE_URL}:${PORT}/openapi.json" -o "$TMPFILE" \
    && python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$TMPFILE" 2>/dev/null; then
    mv "$TMPFILE" "${OUT_DIR}/${NAME}.json"
    echo "OK: ${NAME} (port ${PORT})"
    FETCHED=$((FETCHED + 1))
  else
    rm -f "$TMPFILE"
    echo "WARN: ${NAME} (port ${PORT}) — schema fetch failed or invalid JSON"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "Fetched ${FETCHED}/${TOTAL} schemas (${FAILED} failed)"

# Allow up to 2 failures for services that may be temporarily unavailable
if [ "$FAILED" -gt 2 ]; then
  echo "ERROR: Too many services failed (${FAILED}). Aborting."
  exit 1
fi
