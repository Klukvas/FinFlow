#!/bin/sh
# =============================================================================
# FinFlow PostgreSQL Backup Script
# =============================================================================
# Runs daily via cron inside pg_backup container.
# Dumps all application databases, keeps 7 days of backups.
# =============================================================================

set -eu

BACKUP_DIR="/backups"
RETENTION_DAYS=7
DATE=$(date +%Y-%m-%d_%H%M%S)
BACKUP_SUBDIR="$BACKUP_DIR/$DATE"

# Application databases to back up
DATABASES="
  user_db
  workspace_db
  category_db
  account_db
  expense_db
  income_db
  recurring_db
  goals_db
  debt_db
  subscription_db
  currency_db
  payment_db
  scheduler_db
"

echo "=== FinFlow Backup Started: $(date) ==="

mkdir -p "$BACKUP_SUBDIR"

FAILED=0
for DB in $DATABASES; do
  echo "Backing up $DB..."
  if pg_dump -Fc --no-owner --no-privileges "$DB" > "$BACKUP_SUBDIR/${DB}.dump" 2>/dev/null; then
    SIZE=$(du -h "$BACKUP_SUBDIR/${DB}.dump" | cut -f1)
    echo "  OK ($SIZE)"
  else
    echo "  FAILED: $DB"
    FAILED=$((FAILED + 1))
    rm -f "$BACKUP_SUBDIR/${DB}.dump"
  fi
done

# Compress the backup directory
if [ "$(ls -A "$BACKUP_SUBDIR" 2>/dev/null)" ]; then
  cd "$BACKUP_DIR"
  tar czf "${DATE}.tar.gz" "$DATE" && rm -rf "$BACKUP_SUBDIR"
  SIZE=$(du -h "$BACKUP_DIR/${DATE}.tar.gz" | cut -f1)
  echo "Compressed backup: ${DATE}.tar.gz ($SIZE)"
else
  echo "No successful backups, removing empty directory"
  rm -rf "$BACKUP_SUBDIR"
fi

# Rotate old backups
echo "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true

# Report
REMAINING=$(find "$BACKUP_DIR" -name "*.tar.gz" | wc -l)
echo "Backups on disk: $REMAINING"

if [ "$FAILED" -gt 0 ]; then
  echo "WARNING: $FAILED database(s) failed to back up"
  exit 1
fi

echo "=== Backup Completed: $(date) ==="
