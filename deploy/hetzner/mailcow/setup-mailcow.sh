#!/bin/bash
# =============================================================
# Mailcow Setup Script — Hetzner Dedicated Server
# Avyangah Technologies Limited
#
# Works with existing NGINX reverse proxy setup.
# Port 25 already unblocked by Hetzner (2026-06-18).
#
# Handles EVERYTHING automatically:
#   - Clones Mailcow
#   - Generates config with secure passwords
#   - Creates self-signed SSL certs (so Mailcow starts immediately)
#   - ACME will replace with Let's Encrypt certs once DNS is ready
#   - Configures firewall
#
# Usage:
#   sudo bash setup-mailcow.sh mail.guhya.co.in
# =============================================================

set -euo pipefail

MAIL_HOSTNAME="${1:-mail.guhya.co.in}"
MAILCOW_DIR="/opt/mailcow-dockerized"
TIMEZONE="Europe/London"
SERVER_IP="88.99.167.49"
DEPLOY_DIR="/home/deploy/careai"

echo "============================================="
echo "  Mailcow Setup — Avyangah Technologies"
echo "  Hostname: ${MAIL_HOSTNAME}"
echo "  Server:   ${SERVER_IP}"
echo "============================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Run with sudo"
    exit 1
fi

# --- Prerequisites ---
echo "[1/9] Checking prerequisites..."
apt-get update -qq
apt-get install -y -qq curl git
if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker not installed"
    exit 1
fi
echo "  Docker: $(docker --version)"

# --- Clone Mailcow ---
echo "[2/9] Cloning Mailcow..."
if [ -d "${MAILCOW_DIR}" ]; then
    echo "  Directory exists. Pulling latest..."
    cd "${MAILCOW_DIR}"
    git pull --quiet
else
    git clone https://github.com/mailcow/mailcow-dockerized "${MAILCOW_DIR}"
    cd "${MAILCOW_DIR}"
fi

# --- Generate passwords ---
DBPASS=$(openssl rand -hex 16)
DBROOTPASS=$(openssl rand -hex 16)
API_KEY=$(openssl rand -hex 32)
REDISPASS=$(openssl rand -hex 16)

# --- Generate Config ---
echo "[3/9] Generating mailcow.conf..."
cat > mailcow.conf <<EOF
# =============================================================
# Mailcow Config — Avyangah Technologies Limited
# Generated: $(date -u +"%Y-%m-%d %H:%M UTC")
# Hostname: ${MAIL_HOSTNAME}
# =============================================================

MAILCOW_HOSTNAME=${MAIL_HOSTNAME}
MAILCOW_PASS_SCHEME=BLF-CRYPT
DBNAME=mailcow
DBUSER=mailcow
DBROOT=mailcowroot
DBPASS=${DBPASS}
DBROOTPASS=${DBROOTPASS}
TZ=${TIMEZONE}

# ===========================================
# WEB UI — behind nginx reverse proxy
# ===========================================
HTTP_PORT=8080
HTTP_BIND=0.0.0.0
HTTPS_PORT=8443
HTTPS_BIND=0.0.0.0
SKIP_LETS_ENCRYPT=n
ADDITIONAL_SAN=

# ===========================================
# Redis
# ===========================================
REDISPASS=${REDISPASS}

# ===========================================
# Mail ports (exposed directly to internet)
# ===========================================
SMTP_PORT=25
SMTPS_PORT=465
SUBMISSION_PORT=587

# IMAP: disable non-SSL (port 143), enable SSL only (port 993)
# This avoids port conflict between IMAP_PORT and IMAPS_PORT
IMAP_PORT=0
IMAPS_PORT=993

# Sieve (mail filters)
SIEVE_PORT=4190

# Disable POP3 entirely (use IMAP)
POP_PORT=0
POPS_PORT=0

# ===========================================
# Security
# ===========================================
MAILCOW_FAIL2BAN=y
FAIL2BAN_BANTIME=3600
FAIL2BAN_MAXRETRY=5
SUBMISSION_TLS_ENFORCE=y
RATELIMIT_DEFAULT=50/h

# ===========================================
# Performance
# ===========================================
SKIP_SOLR=y
SKIP_CLAMD=n
SKIP_SOGO=n

# ===========================================
# API
# ===========================================
API_KEY=${API_KEY}
API_ALLOW_FROM=127.0.0.1,::1
EOF

echo "  Config saved."

# --- Generate self-signed SSL certs ---
echo "[4/9] Generating self-signed SSL certificates..."
SSL_DIR="${MAILCOW_DIR}/data/assets/ssl"
mkdir -p "${SSL_DIR}"

if [ ! -f "${SSL_DIR}/cert.pem" ] || [ ! -f "${SSL_DIR}/key.pem" ]; then
    openssl req -x509 -newkey rsa:4096 \
        -keyout "${SSL_DIR}/key.pem" \
        -out "${SSL_DIR}/cert.pem" \
        -days 365 -nodes \
        -subj "/CN=${MAIL_HOSTNAME}" \
        2>/dev/null
    echo "  Self-signed certs created."
else
    echo "  SSL certs already exist, skipping."
fi

# --- Create nginx config ---
echo "[5/9] Creating nginx config..."
NGINX_MAIL="${DEPLOY_DIR}/nginx-mail.conf"

if [ ! -f "${NGINX_MAIL}" ]; then
    cat > "${NGINX_MAIL}" <<'NGINX'
server {
    listen 80;
    server_name mail.guhya.co.in autoconfig.guhya.co.in autodiscover.guhya.co.in;

    location /.well-known/acme-challenge/ {
        proxy_pass http://host.docker.internal:8080;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name mail.guhya.co.in autoconfig.guhya.co.in autodiscover.guhya.co.in;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

    location / {
        proxy_pass http://host.docker.internal:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300;
        client_max_body_size 50m;
    }
}
NGINX
    echo "  Created ${NGINX_MAIL}"
else
    echo "  ${NGINX_MAIL} already exists."
fi

# --- Firewall ---
echo "[6/9] Configuring firewall..."
if command -v ufw &>/dev/null; then
    ufw allow 25/tcp comment 'SMTP' 2>/dev/null || true
    ufw allow 465/tcp comment 'SMTPS' 2>/dev/null || true
    ufw allow 587/tcp comment 'Submission' 2>/dev/null || true
    ufw allow 993/tcp comment 'IMAPS' 2>/dev/null || true
    ufw allow 4190/tcp comment 'Sieve' 2>/dev/null || true
    echo "  Firewall rules set."
else
    echo "  ufw not found."
fi

# --- Pull images ---
echo "[7/9] Pulling Mailcow Docker images..."
cd "${MAILCOW_DIR}"
docker compose pull --quiet 2>/dev/null || docker compose pull

# --- Start Mailcow ---
echo "[8/9] Starting Mailcow..."
docker compose up -d

# --- Save credentials ---
echo "[9/9] Saving credentials..."
CREDS_FILE="/root/.mailcow-credentials"
cat > "${CREDS_FILE}" <<EOF
# Mailcow Credentials — KEEP THIS SAFE
# Generated: $(date -u +"%Y-%m-%d %H:%M UTC")
# Admin: https://${MAIL_HOSTNAME}  admin / moohoo (CHANGE!)
# DB: ${DBPASS}  Root: ${DBROOTPASS}  Redis: ${REDISPASS}  API: ${API_KEY}
EOF
chmod 600 "${CREDS_FILE}"

echo ""
echo "============================================="
echo "  MAILCOW IS RUNNING!"
echo "============================================="
echo ""
echo "  Login: https://${MAIL_HOSTNAME}"
echo "    admin / moohoo → CHANGE PASSWORD → enable 2FA"
echo ""
echo "  Credentials: ${CREDS_FILE}"
echo "============================================="
