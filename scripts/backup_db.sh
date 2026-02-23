#!/bin/bash
# Daily SQLite backup with 7-day retention.
# Run via cron: 0 2 * * * /path/to/scripts/backup_db.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DB_PATH="$PROJECT_ROOT/Backend/app/db.sqlite3"
BACKUP_DIR="$PROJECT_ROOT/Backups"
RETENTION_DAYS=7

if [ ! -f "$DB_PATH" ]; then
    echo "DB not found: $DB_PATH"
    exit 1
fi

mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d)
BACKUP_FILE="$BACKUP_DIR/db_${DATE}.sqlite3"

sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
echo "Backed up to $BACKUP_FILE"

# Delete backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "db_*.sqlite3" -mtime +$RETENTION_DAYS -delete
echo "Retention: kept last $RETENTION_DAYS days"
