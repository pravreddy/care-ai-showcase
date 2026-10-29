#!/bin/bash
# ============================================================
# Care AI Engine - Server Deployment Script
# Run this on a fresh Ubuntu 22.04+ VPS (e.g., Fasthosts 16GB)
#
# Usage:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# --- Pre-flight checks ---
log "Starting Care AI Engine deployment..."

if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo ./scripts/deploy.sh"
fi

# --- Install Docker ---
log "Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    log "Docker installed"
else
    log "Docker already installed"
fi

# --- Install Docker Compose ---
if ! command -v docker compose &>/dev/null; then
    apt-get update && apt-get install -y docker-compose-plugin
    log "Docker Compose installed"
else
    log "Docker Compose already installed"
fi

# --- Create .env if missing ---
if [ ! -f .env ]; then
    log "Creating .env from template..."
    cp .env.example .env

    # Generate random secrets
    SECRET=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    PG_PASSWORD=$(openssl rand -hex 16)

    sed -i "s/change-me-to-a-random-64-char-string/$SECRET/" .env
    sed -i "s/change-me-to-another-random-64-char-string/$JWT_SECRET/" .env
    sed -i "s/careai_secret/$PG_PASSWORD/" .env

    warn "Generated random secrets in .env — review and update other settings!"
else
    log ".env already exists"
fi

# --- Build and start services ---
log "Building Docker images..."
docker compose build --no-cache

log "Starting services..."
docker compose up -d

# --- Wait for services ---
log "Waiting for services to be ready..."
sleep 15

# --- Pull the LLM model ---
log "Pulling Llama 3.2 3B model (this may take a few minutes)..."
docker compose exec -T ollama ollama pull llama3.2:3b

# --- Health check ---
log "Running health check..."
HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"

# --- Done ---
echo ""
echo "=============================================="
echo -e "${GREEN}Care AI Engine deployed successfully!${NC}"
echo "=============================================="
echo ""
echo "API:        http://$(hostname -I | awk '{print $1}'):8000"
echo "API Docs:   http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "Health:     http://$(hostname -I | awk '{print $1}'):8000/health"
echo ""
echo "Next steps:"
echo "  1. Update .env with your domain and Stripe keys"
echo "  2. Set up Nginx + SSL (see config/nginx.conf.example)"
echo "  3. Set up a cron job for NHS data updates:"
echo "     0 3 * * 0 cd /opt/careai && docker compose exec -T api python -m app.scrapers.nhs_scraper --all"
echo ""
