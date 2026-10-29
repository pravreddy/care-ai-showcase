#!/bin/bash
# =============================================================
# Daily Backup — Care AI + SignSimple databases
# =============================================================
# Add to crontab: 0 2 * * * /home/deploy/careai/backup.sh
# Keeps last 7 days. NO downtime — pg_dump runs live.
# =============================================================

set -e

BACKUP_DIR="/mnt/nvme_data/backups"
DATE=$(date +%Y-%m-%d)
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Care AI
docker exec careai-postgres pg_dump -U careai careai | gzip > "$BACKUP_DIR/careai-$DATE.sql.gz"
echo "  ✓ careai DB backed up"

# SignSimple (DocSign)
docker exec careai-postgres pg_dump -U careai docsign_uk 2>/dev/null | gzip > "$BACKUP_DIR/docsign-$DATE.sql.gz" \
  && echo "  ✓ docsign_uk DB backed up" \
  || echo "  ⚠ docsign_uk not yet created"

# Cleanup old
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete
echo "  ✓ Cleaned backups older than $KEEP_DAYS days"

echo "[$(date)] Backup complete"
ls -lh "$BACKUP_DIR"/*.gz 2>/dev/null
