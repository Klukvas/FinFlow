#!/usr/bin/env bash
# Generates TypeScript types from downloaded OpenAPI JSON schemas.
# Must be run from the repository root.
set -euo pipefail

SCHEMA_DIR="frontend/src/types/generated/schemas"
OUT_DIR="frontend/src/types/generated"
OPENAPI_TS="frontend/node_modules/.bin/openapi-typescript"

if [ ! -d "$SCHEMA_DIR" ] || [ -z "$(ls -A "$SCHEMA_DIR"/*.json 2>/dev/null)" ]; then
  echo "ERROR: No schemas found in ${SCHEMA_DIR}. Run collect-openapi-schemas.sh first."
  exit 1
fi

if [ ! -x "$OPENAPI_TS" ]; then
  echo "ERROR: openapi-typescript not found at ${OPENAPI_TS}."
  echo "Run 'cd frontend && yarn install' first."
  exit 1
fi

for SCHEMA in "$SCHEMA_DIR"/*.json; do
  NAME=$(basename "$SCHEMA" .json)
  echo "Generating types for ${NAME}..."
  "$OPENAPI_TS" "$SCHEMA" -o "${OUT_DIR}/${NAME}.ts"

  # Verify the output file is non-empty
  if [ ! -s "${OUT_DIR}/${NAME}.ts" ]; then
    echo "ERROR: Generated file for ${NAME} is empty. Schema may be invalid."
    exit 1
  fi
done

echo ""
echo "Generating manifest..."
node frontend/scripts/generate-manifest.mjs

echo "Done. Generated types are in ${OUT_DIR}/"
