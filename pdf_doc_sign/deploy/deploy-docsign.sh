#!/bin/bash
# =============================================================
# SignSimple — Deploy Script
# Avyangah Technologies Limited
# =============================================================

set -e

DEPLOY_DIR="/home/deploy/careai"
COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.docsign.yml"

ACTION=${1:-help}
cd "$DEPLOY_DIR"

# Helper: get active colour
get_active() {
  if grep -q "blue" active_docsign.conf 2>/dev/null; then
    echo "blue"
  else
    echo "green"
  fi
}

case "$ACTION" in

  setup)
    echo "=== SignSimple — First Time Setup ==="

    echo "[1/6] Creating database..."
    docker exec careai-postgres psql -U careai -c "CREATE DATABASE docsign_uk;" 2>/dev/null \
      && echo "  ✓ Created" || echo "  ✓ Already exists"

    echo "[2/6] Pulling images..."
    $COMPOSE_CMD pull docsign-api-blue docsign-frontend-blue 2>/dev/null || echo "  ⚠ Pull failed (push to GHCR first)"

    echo "[3/6] Starting services..."
    $COMPOSE_CMD up -d docsign-api-blue docsign-frontend-blue docsign-celery

    echo "[4/6] Waiting (15s)..."
    sleep 15
    HEALTH=$(docker exec docsign-api-blue python manage.py check 2>&1)
    if echo "$HEALTH" | grep -q "System check identified no issues"; then
      echo "  ✓ Healthy!"
    else
      echo "  ⚠ $HEALTH"
    fi

    echo "[5/6] Running migrations..."
    docker exec docsign-api-blue python manage.py migrate --noinput
    echo "  ✓ Migrations complete"

    echo "[6/6] Reloading nginx..."
    docker exec careai-nginx nginx -s reload 2>/dev/null \
      && echo "  ✓ Nginx reloaded" || echo "  ⚠ Failed (need SSL certs first)"

    echo ""
    echo "=== Done! Next: DNS + SSL for signsimple.co.uk ==="
    ;;

  blue|green)
    COLOUR=$ACTION
    OTHER=$( [ "$COLOUR" = "blue" ] && echo "green" || echo "blue" )

    echo "=== SignSimple → $COLOUR ==="

    echo "[1/6] Pulling images..."
    $COMPOSE_CMD pull docsign-api-$COLOUR docsign-frontend-$COLOUR docsign-celery

    echo "[2/6] Starting $COLOUR..."
    if [ "$COLOUR" = "green" ]; then
      $COMPOSE_CMD --profile docsign-green up -d docsign-api-$COLOUR docsign-frontend-$COLOUR
    else
      $COMPOSE_CMD up -d docsign-api-$COLOUR docsign-frontend-$COLOUR
    fi
    $COMPOSE_CMD up -d docsign-celery

    echo "[3/6] Health check (12s)..."
    sleep 12
    HEALTH=$(docker exec docsign-api-$COLOUR python manage.py check 2>&1)
    if echo "$HEALTH" | grep -q "System check identified no issues"; then
      echo "  ✓ Passed"
    else
      echo "  ✗ FAILED — rolling back"
      $COMPOSE_CMD stop docsign-api-$COLOUR docsign-frontend-$COLOUR
      exit 1
    fi

    echo "[4/6] Migration dry-run..."
    docker exec docsign-api-$COLOUR python manage.py migrate --plan || {
      echo "  ✗ Migration plan FAILED — rolling back"
      $COMPOSE_CMD stop docsign-api-$COLOUR docsign-frontend-$COLOUR
      exit 1
    }

    echo "[5/6] Applying migrations..."
    docker exec docsign-api-$COLOUR python manage.py migrate --noinput
    echo "  ✓ Migrations complete"

    echo "[6/6] Switching traffic to $COLOUR..."
    cat > "$DEPLOY_DIR/active_docsign.conf" << EOF
set \$ds_backend "docsign-api-$COLOUR:8000";
set \$ds_frontend "docsign-frontend-$COLOUR:80";
EOF
    docker exec careai-nginx nginx -s reload

    echo ""
    echo "=== ✅ Active: $COLOUR ==="
    echo "Stop old: $COMPOSE_CMD stop docsign-api-$OTHER docsign-frontend-$OTHER"
    ;;

  dry-run)
    ACTIVE=$(get_active)
    OTHER=$( [ "$ACTIVE" = "blue" ] && echo "green" || echo "blue" )

    echo "=== SignSimple — Dry Run (no changes will be made) ==="
    echo ""
    echo "📋 Current state:"
    echo "  Active colour: $ACTIVE"
    echo "  Next deploy would target: $OTHER"
    echo ""

    echo "📋 Container status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "docsign" || echo "  None running"
    echo ""

    echo "📋 Django system check on active ($ACTIVE):"
    docker exec docsign-api-$ACTIVE python manage.py check 2>&1 | head -5
    echo ""

    echo "📋 Migration check (are all model changes captured?):"
    docker exec docsign-api-$ACTIVE python manage.py migrate --check 2>&1 && \
      echo "  ✓ All migrations are up to date" || \
      echo "  ⚠ There are model changes not yet in migrations"
    echo ""

    echo "📋 Migration plan (what would run next):"
    PLAN=$(docker exec docsign-api-$ACTIVE python manage.py migrate --plan 2>&1)
    if echo "$PLAN" | grep -q "No planned migration operations"; then
      echo "  ✓ No pending migrations"
    else
      echo "$PLAN" | head -20
    fi
    echo ""

    echo "📋 Disk usage:"
    du -sh /mnt/nvme_data/* 2>/dev/null || echo "  NVMe not mounted"
    echo ""

    echo "=== Dry run complete — no changes were made ==="
    ;;

  migrate)
    ACTIVE=$(get_active)
    echo "=== Running migrations on active container ($ACTIVE) ==="

    echo "📋 Migration plan:"
    docker exec docsign-api-$ACTIVE python manage.py migrate --plan || {
      echo "❌ Migration plan failed"
      exit 1
    }

    echo ""
    read -p "Apply these migrations? (y/N) " CONFIRM
    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
      docker exec docsign-api-$ACTIVE python manage.py migrate --noinput
      echo "✅ Migrations complete"
    else
      echo "⏭️  Skipped"
    fi
    ;;

  check)
    ACTIVE=$(get_active)
    echo "=== SignSimple — Health Checks ($ACTIVE) ==="
    echo ""

    echo "🏥 Django system check:"
    docker exec docsign-api-$ACTIVE python manage.py check 2>&1
    echo ""

    echo "📋 Migration status:"
    docker exec docsign-api-$ACTIVE python manage.py migrate --check 2>&1 && \
      echo "  ✓ All migrations applied" || \
      echo "  ⚠ Unapplied migrations detected"
    echo ""

    echo "📋 Pending migrations:"
    docker exec docsign-api-$ACTIVE python manage.py showmigrations --plan 2>&1 | grep "\[ \]" || echo "  ✓ None"
    echo ""

    echo "🔌 Database connection:"
    docker exec docsign-api-$ACTIVE python -c "
import django; django.setup()
from django.db import connection
connection.ensure_connection()
print('  ✓ Connected to', connection.settings_dict['NAME'])
" 2>&1 || echo "  ❌ Failed"
    ;;

  status)
    echo "=== Containers ==="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "(careai|docsign)" || echo "None"
    echo ""
    echo "=== Active Colour ==="
    cat "$DEPLOY_DIR/active_docsign.conf" 2>/dev/null || echo "Not set"
    echo ""
    echo "=== NVMe Disk ==="
    du -sh /mnt/nvme_data/* 2>/dev/null || echo "Not mounted"
    ;;

  logs)
    CONTAINER=${2:-docsign-api-$(get_active)}
    echo "=== Tailing logs for $CONTAINER ==="
    docker logs $CONTAINER --tail 50 -f
    ;;

  stop)
    echo "=== Stopping SignSimple ==="
    $COMPOSE_CMD stop docsign-api-blue docsign-api-green docsign-frontend-blue docsign-frontend-green docsign-celery 2>/dev/null || true
    echo "✓ Stopped. Care AI unaffected."
    ;;

  backup)
    bash "$DEPLOY_DIR/backup.sh"
    ;;

  *)
    echo "SignSimple — Deploy Script"
    echo "Avyangah Technologies Limited"
    echo ""
    echo "  Deployment:"
    echo "    ./deploy-docsign.sh setup      First-time setup"
    echo "    ./deploy-docsign.sh blue       Deploy to blue"
    echo "    ./deploy-docsign.sh green      Deploy to green"
    echo ""
    echo "  Safety checks:"
    echo "    ./deploy-docsign.sh dry-run    Preview what would happen (no changes)"
    echo "    ./deploy-docsign.sh check      Run all health checks on active"
    echo "    ./deploy-docsign.sh migrate    Show plan + apply migrations (with confirm)"
    echo ""
    echo "  Operations:"
    echo "    ./deploy-docsign.sh status     Show container status"
    echo "    ./deploy-docsign.sh logs       Tail logs (active container)"
    echo "    ./deploy-docsign.sh logs <name> Tail specific container"
    echo "    ./deploy-docsign.sh stop       Stop all SignSimple containers"
    echo "    ./deploy-docsign.sh backup     Backup databases"
    ;;
esac
