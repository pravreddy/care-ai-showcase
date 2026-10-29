#!/bin/bash
# =============================================================
# Deploy Mailcow — Run from LOCAL machine
# =============================================================
# Copies all configs to server and sets up Mailcow.
# All source files live in deploy/hetzner/mailcow/ in the repo.
#
# Usage:
#   ./deploy-mailcow.sh              # Full setup (first time)
#   ./deploy-mailcow.sh update       # Update configs only
#
# Prerequisites:
#   - SSH alias 'hetzner-prod' in ~/.ssh/config
#   - Port 25 unblocked ✅
#   - DNS records for mail.guhya.co.in
#   - rDNS set in Hetzner Robot
# =============================================================

set -euo pipefail

SSH_HOST="hetzner-prod"
REMOTE_DIR="/home/deploy/careai"
MAILCOW_DIR="/opt/mailcow-dockerized"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAILCOW_SRC="${SCRIPT_DIR}/deploy/hetzner/mailcow"

MODE="${1:-full}"

echo "============================================="
echo "  Mailcow Deploy — Avyangah Technologies"
echo "  Mode: ${MODE}"
echo "  Source: ${MAILCOW_SRC}"
echo "  Target: ${SSH_HOST}:${REMOTE_DIR}"
echo "============================================="
echo ""

# --- Step 1: Copy configs to server ---
echo "[1/4] Copying configs to server..."

# nginx-mail.conf → ~/careai/ (mounted by docker-compose into nginx container)
scp "${MAILCOW_SRC}/nginx-mail.conf" "${SSH_HOST}:${REMOTE_DIR}/nginx-mail.conf"
echo "  ✓ nginx-mail.conf → ${REMOTE_DIR}/"

# docker-compose.yml (with mailcow nginx mount + extra_hosts)
scp "${SCRIPT_DIR}/docker-compose.yml" "${SSH_HOST}:${REMOTE_DIR}/docker-compose.yml"
echo "  ✓ docker-compose.yml → ${REMOTE_DIR}/"

# setup script
scp "${MAILCOW_SRC}/setup-mailcow.sh" "${SSH_HOST}:/tmp/setup-mailcow.sh"
echo "  ✓ setup-mailcow.sh → /tmp/"

echo ""

# --- Step 2: Restart nginx ---
echo "[2/4] Restarting nginx with mail config..."
ssh "${SSH_HOST}" "cd ${REMOTE_DIR} && docker compose up -d nginx"
echo "  ✓ nginx restarted"
echo ""

# --- Step 3: Setup Mailcow (first time only) ---
if [ "${MODE}" = "full" ]; then
    echo "[3/4] Running Mailcow setup..."
    ssh -t "${SSH_HOST}" "sudo bash /tmp/setup-mailcow.sh mail.guhya.co.in"
    echo ""

    echo "[4/4] Starting Mailcow (downloading ~15 images, 5-10 min)..."
    ssh -t "${SSH_HOST}" "cd ${MAILCOW_DIR} && sudo docker compose pull && sudo docker compose up -d"
    echo ""
else
    echo "[3/4] Skipped (update mode)"
    echo "[4/4] Restarting Mailcow..."
    ssh -t "${SSH_HOST}" "cd ${MAILCOW_DIR} && sudo docker compose up -d"
    echo ""
fi

echo "============================================="
echo "  DONE!"
echo "============================================="
echo ""
echo "  Admin:   https://mail.guhya.co.in"
echo "  Webmail: https://mail.guhya.co.in/SOGo"
echo "  Login:   admin / moohoo (CHANGE THIS!)"
echo "============================================="
