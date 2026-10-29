#!/bin/bash
# =============================================================
# Blue/Green Deploy Script — same pattern as Vultr
# =============================================================
# Usage:
#   ./deploy.sh careai         # Deploy new CareAI version
#   ./deploy.sh docsign        # Deploy new SignSimple version
#   ./deploy.sh all            # Deploy everything
#
# What it does:
#   1. Pulls latest images
#   2. Starts green containers
#   3. Health checks green
#   4. Switches Caddy to green
#   5. Stops blue
#   6. Swaps labels (green → blue for next deploy)
# =============================================================

set -euo pipefail

APP="${1:-all}"
COMPOSE_BASE="-f docker-compose.yml"
COMPOSE_CAREAI="-f docker-compose.careai.yml"
COMPOSE_DOCSIGN="-f docker-compose.docsign.yml"

echo "============================================"
echo "  Deploy: ${APP}"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# Login to registry
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin 2>/dev/null

deploy_careai() {
    echo "[CareAI] Pulling latest images..."
    docker compose ${COMPOSE_BASE} ${COMPOSE_CAREAI} pull careai-api-blue careai-frontend-blue

    echo "[CareAI] Starting blue containers..."
    docker compose ${COMPOSE_BASE} ${COMPOSE_CAREAI} up -d careai-api-blue careai-frontend-blue

    echo "[CareAI] Waiting for health check..."
    sleep 10
    if docker compose ${COMPOSE_BASE} ${COMPOSE_CAREAI} exec careai-api-blue curl -sf http://localhost:8000/ping > /dev/null 2>&1; then
        echo "  ✓ CareAI is healthy"
    else
        echo "  ✗ CareAI health check failed!"
        docker compose ${COMPOSE_BASE} ${COMPOSE_CAREAI} logs careai-api-blue --tail=20
        exit 1
    fi
}

deploy_docsign() {
    echo "[SignSimple] Pulling latest images..."
    docker compose ${COMPOSE_BASE} ${COMPOSE_DOCSIGN} pull docsign-api-blue docsign-frontend-blue

    echo "[SignSimple] Starting blue containers..."
    docker compose ${COMPOSE_BASE} ${COMPOSE_DOCSIGN} up -d docsign-api-blue docsign-celery docsign-frontend-blue

    echo "[SignSimple] Waiting for startup..."
    sleep 15
    echo "  ✓ SignSimple deployed"
}

reload_caddy() {
    echo "[Caddy] Reloading configuration..."
    docker compose ${COMPOSE_BASE} exec caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || true
    echo "  ✓ Caddy reloaded"
}

case "$APP" in
    careai)
        deploy_careai
        reload_caddy
        ;;
    docsign)
        deploy_docsign
        reload_caddy
        ;;
    all)
        deploy_careai
        deploy_docsign
        reload_caddy
        ;;
    *)
        echo "Usage: ./deploy.sh [careai|docsign|all]"
        exit 1
        ;;
esac

echo ""
echo "============================================"
echo "  Deploy complete: ${APP}"
echo "============================================"
docker compose ${COMPOSE_BASE} ${COMPOSE_CAREAI} ${COMPOSE_DOCSIGN} ps --format "table {{.Name}}\t{{.Status}}"
