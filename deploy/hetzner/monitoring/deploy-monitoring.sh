#!/usr/bin/env bash
# Deploy the monitoring stack (Uptime Kuma + autoheal) FROM YOUR MAC.
#   Usage: ./deploy-monitoring.sh
set -euo pipefail

SSH_HOST="hetzner-prod"
REMOTE="/home/deploy/monitoring"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Creating ${REMOTE} on server"
ssh "$SSH_HOST" "mkdir -p ${REMOTE}"

echo "==> Copying compose file"
scp "${HERE}/docker-compose.yml" "${SSH_HOST}:${REMOTE}/docker-compose.yml"

echo "==> Starting monitoring stack"
ssh "$SSH_HOST" "cd ${REMOTE} && docker compose up -d"

cat <<EOF

==> Done.

Open the dashboard from your Mac with an SSH tunnel:
    ssh -L 3001:localhost:3001 ${SSH_HOST}
Then visit:  http://localhost:3001
(First visit: create your admin account.)

Next: add monitors + a notification channel — see README.md.
EOF
