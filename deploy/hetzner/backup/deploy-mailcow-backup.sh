#!/usr/bin/env bash
# deploy-mailcow-backup.sh — ship mailcow-backup.sh, install the root cron at
# 02:30, and run one backup now to prove it works.
#
# Needs root on the server (Mailcow backup reads Docker volumes), so it uses
# sudo over an interactive SSH (-t). You may be asked for your sudo password.
set -euo pipefail
SSH_HOST="${SSH_HOST:-hetzner-prod}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> Copying mailcow-backup.sh to server"
scp "$HERE/mailcow-backup.sh" "$SSH_HOST:/home/deploy/careai/mailcow-backup.sh"

echo "==> Installing root cron (02:30) + running one backup now (sudo may prompt)"
ssh -t "$SSH_HOST" "
  sudo chmod +x /home/deploy/careai/mailcow-backup.sh &&
  echo '30 2 * * * root /home/deploy/careai/mailcow-backup.sh' | sudo tee /etc/cron.d/mailcow-backup &&
  sudo chmod 644 /etc/cron.d/mailcow-backup &&
  echo '--- running one mailcow backup now (can take a minute) ---' &&
  sudo /home/deploy/careai/mailcow-backup.sh ;
  echo '--- last 10 log lines ---' ;
  tail -n 10 /mnt/nvme_data/backups/mailcow/backup-mailcow.log
"
echo "==> Done. Nightly mailcow backup at 02:30."
