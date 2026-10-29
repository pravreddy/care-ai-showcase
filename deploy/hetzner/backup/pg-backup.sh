#!/usr/bin/env bash
# =============================================================================
# pg-backup.sh — nightly Postgres backup for the careai instance.
#
# Dumps EVERY database in the careai-postgres instance (careai + docsign if it
# shares the instance) plus roles, gzips it, keeps the last N days, and logs.
# An off-box copy section is included — enable ONE target once you pick it.
#
# Install (on the server):
#   chmod +x /home/deploy/careai/pg-backup.sh
#   ( crontab -l 2>/dev/null; echo "0 2 * * * /home/deploy/careai/pg-backup.sh" ) | crontab -
#   # -> runs every night at 02:00 server time
#
# Restore a dump:
#   gunzip -c /mnt/nvme_data/backups/postgres/pg_all_YYYY-MM-DD_HHMMSS.sql.gz \
#     | docker exec -i careai-postgres psql -U careai
# =============================================================================
set -euo pipefail

CONTAINER="careai-postgres"
PGUSER="careai"
BACKUP_ROOT="/mnt/nvme_data/backups/postgres"
RETENTION_DAYS=14
TS="$(date +%Y-%m-%d_%H%M%S)"
FILE="${BACKUP_ROOT}/pg_all_${TS}.sql.gz"
LOG="${BACKUP_ROOT}/backup.log"

# --- dead-man's-switch (healthchecks.io) ---
# The ping URL lives in a server-only file (~/careai/.backup-env), never in git.
# If it's unset, pings are simply skipped, so the script still works without it.
[ -f "$HOME/careai/.backup-env" ] && . "$HOME/careai/.backup-env"
HC_URL="${HC_URL:-}"
hc() { [ -n "$HC_URL" ] && curl -fsS -m 10 --retry 3 "${HC_URL}${1:-}" >/dev/null 2>&1 || true; }

mkdir -p "$BACKUP_ROOT"
exec >> "$LOG" 2>&1
echo "=== $(date -u +'%Y-%m-%d %H:%M:%S UTC') starting backup ==="
hc /start

# --- dump everything ---
if docker exec "$CONTAINER" pg_dumpall -U "$PGUSER" | gzip > "$FILE"; then
  echo "OK   wrote $FILE ($(du -h "$FILE" | cut -f1))"
else
  echo "FAIL pg_dumpall failed"
  rm -f "$FILE"
  hc /fail
  exit 1
fi

# --- sanity check: file is non-trivial in size ---
SIZE=$(stat -c%s "$FILE")
if [ "$SIZE" -lt 1000 ]; then
  echo "FAIL backup suspiciously small (${SIZE} bytes) — not trusting it"
  hc /fail
  exit 1
fi

# --- prune old local backups ---
find "$BACKUP_ROOT" -name 'pg_all_*.sql.gz' -mtime +"$RETENTION_DAYS" -delete
echo "pruned local backups older than ${RETENTION_DAYS} days"

# ============================================================================
# OFF-BOX COPY — uncomment exactly ONE block once you've set up a target.
# This is what protects you if the disk or the whole server is lost.
# ============================================================================

# --- Option A: Hetzner Storage Box (rsync over SSH) — avyangah-backup ---
STORAGEBOX="u618536@u618536.your-storagebox.de"
SSHOPTS="-p 23 -i $HOME/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new"
# --mkpath creates backups/postgres/ on the box (receiver rsync is 3.2.7, which supports it)
if rsync -a --mkpath -e "ssh $SSHOPTS" "$FILE" "${STORAGEBOX}:backups/postgres/"; then
  echo "off-box OK -> Storage Box ($(basename "$FILE"))"
else
  echo "off-box FAIL -> Storage Box"
fi

# --- Option B: Backblaze B2 / Cloudflare R2 / S3 (rclone) ---
# rclone copy "$FILE" b2:careai-backups/postgres/ \
#   && echo "off-box OK -> rclone remote" || echo "off-box FAIL -> rclone remote"

# --- dead-man's-switch: success ping. A MISSED ping (cron died, dump failed,
#     server down) makes healthchecks.io alert you after the grace period. ---
hc

echo "=== done ==="
