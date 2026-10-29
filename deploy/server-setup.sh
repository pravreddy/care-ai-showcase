#!/bin/bash
# ============================================================
# Care AI - UK VPS Initial Setup
#
# Run this ONCE on a fresh Ubuntu 24.04 VPS.
# It installs Docker, hardens SSH, sets up the firewall,
# and prepares the deployment directory.
#
# Usage:
#   ssh root@YOUR_SERVER_IP
#   curl -sSL https://raw.githubusercontent.com/YOUR_REPO/deploy/server-setup.sh | bash
#   (or copy this file and run: chmod +x server-setup.sh && ./server-setup.sh)
#
# Tested on: Ubuntu 24.04 LTS, Hetzner UK / OVHcloud UK
# ============================================================

set -euo pipefail

echo "============================================"
echo "  Care AI - UK Server Setup"
echo "============================================"
echo ""

# --- Check we're root ---
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run this as root"
    exit 1
fi

# --- Create deploy user ---
echo "[1/8] Creating deploy user..."
if ! id "deploy" &>/dev/null; then
    adduser --disabled-password --gecos "Care AI Deploy" deploy
    usermod -aG sudo deploy
    # Copy root SSH keys to deploy user
    mkdir -p /home/deploy/.ssh
    cp /root/.ssh/authorized_keys /home/deploy/.ssh/ 2>/dev/null || true
    chown -R deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    chmod 600 /home/deploy/.ssh/authorized_keys 2>/dev/null || true
    echo "deploy ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/deploy
    echo "  ✓ User 'deploy' created"
else
    echo "  ✓ User 'deploy' already exists"
fi

# --- System updates ---
echo "[2/8] Updating system..."
apt-get update -qq
apt-get upgrade -y -qq
echo "  ✓ System updated"

# --- Install Docker ---
echo "[3/8] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker deploy
    systemctl enable docker
    echo "  ✓ Docker installed"
else
    echo "  ✓ Docker already installed"
fi

# --- Install Docker Compose plugin ---
echo "[4/8] Verifying Docker Compose..."
docker compose version &>/dev/null && echo "  ✓ Docker Compose ready" || echo "  ⚠ Docker Compose not found"

# --- Firewall ---
echo "[5/8] Configuring firewall..."
apt-get install -y -qq ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH (change port below if you want)
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo "  ✓ Firewall: only SSH, HTTP, HTTPS allowed"

# --- Harden SSH ---
echo "[6/8] Hardening SSH..."
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl restart sshd
echo "  ✓ SSH: password login disabled, key-only"

# --- Auto security updates ---
echo "[7/8] Enabling automatic security updates..."
apt-get install -y -qq unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
echo "  ✓ Unattended security upgrades enabled"

# --- Setup deployment directory ---
echo "[8/8] Setting up deployment directory..."
mkdir -p /home/deploy/careai/logs
mkdir -p /home/deploy/careai/ssl
chown -R deploy:deploy /home/deploy/careai

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Copy files to server:"
echo "     scp deploy/.env.template deploy@YOUR_IP:/home/deploy/careai/.env"
echo "     scp deploy/docker-compose.yml deploy@YOUR_IP:/home/deploy/careai/"
echo ""
echo "  2. SSH as deploy user:"
echo "     ssh deploy@YOUR_IP"
echo "     cd /home/deploy/careai"
echo "     nano .env  (fill in your secrets)"
echo ""
echo "  3. Login to GHCR:"
echo "     echo YOUR_GITHUB_PAT | docker login ghcr.io -u YOUR_USERNAME --password-stdin"
echo ""
echo "  4. Start everything:"
echo "     docker compose up -d"
echo ""
echo "  5. Pull the Ollama model:"
echo "     docker exec careai-ollama ollama pull llama3.2:3b"
echo ""
echo "  6. Add SSL (optional but recommended):"
echo "     See deploy/ssl-setup.sh"
echo ""
echo "Server hardened: SSH key-only, firewall (80/443/22), auto-updates."
echo "============================================"
