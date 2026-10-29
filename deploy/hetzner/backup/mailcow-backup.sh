#!/usr/bin/env bash
# =============================================================================
# mailcow-backup.sh — nightly Mailcow backup (mail store, Mailcow DB, DKIM
# keys, rspamd/redis, and mailcow.conf), via Mailcow's own helper so the
# backup is consistent. Keeps a few days locally, MIRRORS off-box to the
# Storage Box (deeper history comes from the box's snapshots), and pings
# healthchecks.io.
#
# MUST run as root — the helper reads Docker volumes.
#
# Install (on the server, as root):
#   chmod +x /home/deploy/careai/mailcow-backup.sh
#   echo '30 2 * * * root /home/deploy/careai/mailcow-backup.sh' > /etc/cron.d/mailcow-backup
#   # -> runs every night at 02:30, after the Postgres backup
#
# Restore (interactive):
#   cd /opt/mailcow-dockerized
#   MAILCOW_BACKUP_LOCATION=/mnt/nvme_data/backups/mailcow \
#     ./helper-scripts/backup_and_restore.sh restore
# =============================================================================
set -euo pipefail

MAILCOW_DIR="/opt/mailcow-dockerized"
BACKUP_ROOT="/mnt/nvme_data/backups/mailcow"
KEEP_DAYS=3                       # local retention; box snapshots hold longer
LOG="${BACKUP_ROOT}/backup-mailcow.log"

# off-box: same Storage Box as Postgres. Use the deploy user's key explicitly,
# with absolute paths, because this runs as root (root's HOME != deploy's).
STORAGEBOX="u618536@u618536.your-storagebox.de"
SSH_KEY="/home/deploy/.ssh/id_ed25519"
SSHOPTS="-p 23 -i $SSH_KEY -o StrictHostKeyChecking=accept-new"

# dead-man's-switch — its OWN check (HC_URL_MAIL) so a mail-backup failure is
# distinguishable from a Postgres one. URL lives in the server-only env file.
[ -f /home/deploy/careai/.backup-env ] && . /home/deploy/careai/.backup-env
HC_URL="${HC_URL_MAIL:-}"
hc() { [ -n "$HC_URL" ] && curl -fsS -m 10 --retry 3 "${HC_URL}${1:-}" >/dev/null 2>&1 || true; }

mkdir -p "$BACKUP_ROOT"
exec >> "$LOG" 2>&1
echo "=== $(date -u +'%Y-%m-%d %H:%M:%S UTC') starting mailcow backup ==="
hc /start

# --- run Mailcow's own backup (consistent across all its volumes) ---
cd "$MAILCOW_DIR"
# The helper bails with "Could not determine compose project name" if
# COMPOSE_PROJECT_NAME is empty (older mailcow.conf files don't set it).
# Derive it from the running Mailcow containers' compose label and export it.
export COMPOSE_PROJECT_NAME="$(docker ps --format '{{.Label "com.docker.compose.project"}}' | grep -im1 mailcow || true)"
echo "using COMPOSE_PROJECT_NAME='${COMPOSE_PROJECT_NAME}'"
if [ -z "$COMPOSE_PROJECT_NAME" ]; then
  echo "FAIL could not determine COMPOSE_PROJECT_NAME from running containers"
  hc /fail; exit 1
fi
if MAILCOW_BACKUP_LOCATION="$BACKUP_ROOT" \
     ./helper-scripts/backup_and_restore.sh backup all --delete-days "$KEEP_DAYS"; then
  LATEST="$(ls -1dt "$BACKUP_ROOT"/mailcow-* 2>/dev/null | head -1 || true)"
  echo "OK   mailcow backup -> ${LATEST:-?} ($(du -sh "${LATEST:-$BACKUP_ROOT}" 2>/dev/null | cut -f1))"
else
  echo "FAIL mailcow backup_and_restore.sh failed"
  hc /fail
  exit 1
fi

# --- off-box: MIRROR to the box (mail is large -> bound the live copy; the
#     box's automated snapshots provide point-in-time history). The log is
#     excluded so an actively-written file isn't shipped. ---
if rsync -a --delete --mkpath --exclude='backup-mailcow.log' \
     -e "ssh $SSHOPTS" "$BACKUP_ROOT/" "${STORAGEBOX}:backups/mailcow/"; then
  echo "off-box OK -> Storage Box (mirror)"
else
  echo "off-box FAIL -> Storage Box"
fi

# --- success ping; a missed ping makes healthchecks.io alert you ---
hc
echo "=== done ==="
