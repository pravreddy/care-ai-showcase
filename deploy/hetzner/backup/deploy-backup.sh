#!/usr/bin/env bash
# Install the nightly Postgres backup on the server, FROM YOUR MAC.
#   Usage: ./deploy-backup.sh
set -euo pipefail

SSH_HOST="hetzner-prod"
REMOTE="/home/deploy/careai"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Copying pg-backup.sh to server"
scp "${HERE}/pg-backup.sh" "${SSH_HOST}:${REMOTE}/pg-backup.sh"

echo "==> Making it executable + installing the 02:00 cron (idempotent)"
ssh "$SSH_HOST" bash -s <<'REMOTE_CMDS'
set -e
chmod +x /home/deploy/careai/pg-backup.sh
# add the cron line only if it isn't already there.
# ( || true: on a server with no crontab yet, grep matches nothing and returns
#   non-zero, which under `set -e` would abort the subshell and pipe an EMPTY
#   crontab into `crontab -`. The guard prevents that. )
LINE="0 2 * * * /home/deploy/careai/pg-backup.sh"
( crontab -l 2>/dev/null | grep -vF "pg-backup.sh" || true; echo "$LINE" ) | crontab -
echo "cron installed:"
crontab -l | grep -F "pg-backup.sh" || echo "WARNING: cron line missing!"
REMOTE_CMDS

echo "==> Running one backup now to prove it works"
ssh "$SSH_HOST" "/home/deploy/careai/pg-backup.sh && tail -n 5 /mnt/nvme_data/backups/postgres/backup.log"

echo "==> Done. Nightly backups at 02:00; files in /mnt/nvme_data/backups/postgres/"
