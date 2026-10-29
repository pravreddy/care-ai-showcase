#!/bin/bash
# =============================================================
# SignSimple — AI Detector Migration Fix Script
# Run on Vultr server: bash fix-ai-detector-migrations.sh
# =============================================================
# What this does:
#   1. Checks current migration state
#   2. Applies the 0005_merge migration
#   3. Verifies everything is clean
#   4. Restarts the API containers
# =============================================================

set -e

BLUE="docsign-api-blue"
GREEN="docsign-api-green"
COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.docsign.yml"

# Find which API container is running
if docker inspect $BLUE --format='{{.State.Running}}' 2>/dev/null | grep -q true; then
  ACTIVE=$BLUE
elif docker inspect $GREEN --format='{{.State.Running}}' 2>/dev/null | grep -q true; then
  ACTIVE=$GREEN
else
  echo "❌ No active docsign API container found"
  exit 1
fi

echo "=== AI Detector Migration Fix ==="
echo "Active container: $ACTIVE"
echo ""

echo "[1/4] Current migration state:"
docker exec $ACTIVE python manage.py showmigrations ai_detector
echo ""

echo "[2/4] Applying merge migration..."
docker exec $ACTIVE python manage.py migrate ai_detector --noinput
echo "✅ Done"
echo ""

echo "[3/4] Verifying — Django system check:"
docker exec $ACTIVE python manage.py check
echo ""

echo "[4/4] Restarting containers to pick up changes..."
docker restart $ACTIVE docsign-celery
echo "✅ Restarted"
echo ""

echo "=== ✅ Fix complete! ==="
echo "Test at: https://signsimple.co.uk/ai-detector"
