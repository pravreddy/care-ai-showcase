#!/bin/bash
# =============================================================
# Avyangah Technologies — Hetzner Server Setup
# =============================================================
# Run ONCE on a fresh Ubuntu 24.04 Hetzner CPX32.
#
# Usage:
#   ssh root@YOUR_HETZNER_IP
#   bash server-setup.sh
#
# What it does:
#   1. Creates deploy user
#   2. Installs Docker + Docker Compose
#   3. Hardens SSH + firewall
#   4. Prepares deployment directory
#   5. Logs into GitHub Container Registry
# =============================================================

set -euo pipefail

echo "============================================"
echo "  Avyangah Technologies — Hetzner Setup"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "============================================"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run as root"
    exit 1
fi

# --- Create deploy user ---
echo "[1/7] Creating deploy user..."
if ! id "deploy" &>/dev/null; then
    adduser --disabled-password --gecos "Avyangah Deploy" deploy
    usermod -aG sudo deploy
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
echo "[2/7] Updating system..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl git htop ufw fail2ban unzip

# --- Install Docker ---
echo "[3/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker deploy
    systemctl enable docker
    echo "  ✓ Docker installed"
else
    echo "  ✓ Docker already installed"
fi

# --- Firewall ---
echo "[4/7] Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (Caddy)
ufw allow 443/tcp   # HTTPS (Caddy)
# Port 25 — uncomment after Hetzner approves SMTP
# ufw allow 25/tcp
ufw --force enable
echo "  ✓ Firewall configured (ports 22, 80, 443)"

# --- Harden SSH ---
echo "[5/7] Hardening SSH..."
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
echo "  ✓ SSH hardened (root login disabled, password auth disabled)"

# --- Create deployment directory ---
echo "[6/7] Setting up deployment directory..."
DEPLOY_DIR="/home/deploy/avyangah"
mkdir -p $DEPLOY_DIR
chown -R deploy:deploy $DEPLOY_DIR
echo "  ✓ Deploy directory: $DEPLOY_DIR"

# --- Swap (important for 4GB servers) ---
echo "[7/7] Setting up swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    echo "  ✓ 2GB swap created"
else
    echo "  ✓ Swap already exists"
fi

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  Next steps:"
echo "  1. Log in as: ssh deploy@$(hostname -I | awk '{print $1}')"
echo "  2. Copy your compose files to $DEPLOY_DIR"
echo "  3. Copy .env.template to .env and fill values"
echo "  4. Log into GitHub registry:"
echo "     echo \$GITHUB_TOKEN | docker login ghcr.io -u \$GITHUB_USER --password-stdin"
echo "  5. Start services:"
echo "     docker compose -f docker-compose.yml \\"
echo "       -f docker-compose.careai.yml \\"
echo "       -f docker-compose.docsign.yml \\"
echo "       up -d"
echo ""
echo "  Server IP: $(hostname -I | awk '{print $1}')"
echo "============================================"
