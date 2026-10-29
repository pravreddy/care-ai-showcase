#!/bin/bash
# =============================================================
# SignSimple — NVMe Media Storage Fix
# =============================================================
# Run ONCE on VPS to fix media volume mapping.
#
# Problem: Docker was mapping 3 separate subdirectories into /app/media/
#          but signature images and signed PDFs were written to unmapped
#          paths inside the container (lost on redeploy).
#
# Fix: docker-compose.docsign.yml now maps entire /app/media → NVMe.
#      This script creates the unified directory structure and moves
#      any existing data.
#
# Usage: bash fix-nvme-media.sh
# =============================================================

set -e

NVME="/mnt/nvme_data/docsign"
DEPLOY_DIR="/home/deploy/careai"
COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.docsign.yml"

echo "=== SignSimple — Fix NVMe Media Storage ==="
echo ""

# Check NVMe is mounted
if ! mountpoint -q /mnt/nvme_data; then
    echo "❌ /mnt/nvme_data not mounted"
    exit 1
fi

echo "📋 Current NVMe layout:"
ls -la "$NVME/" 2>/dev/null || echo "  Directory not found"
echo ""

# Step 1: Create unified media directory structure
echo "[1/4] Creating unified media directory..."
mkdir -p "$NVME/media/documents"
mkdir -p "$NVME/media/signed"
mkdir -p "$NVME/media/invoices"
mkdir -p "$NVME/media/uploads"
echo "  ✓ Created: media/{documents,signed,invoices,uploads}"

# Step 2: Move existing data from old separate directories
echo "[2/4] Moving existing data from old layout..."

if [ -d "$NVME/documents" ] && [ "$(ls -A $NVME/documents 2>/dev/null)" ]; then
    cp -rn "$NVME/documents/"* "$NVME/media/documents/" 2>/dev/null || true
    echo "  ✓ Copied documents/ → media/documents/"
else
    echo "  ⏭️  No existing documents/ data"
fi

if [ -d "$NVME/invoices" ] && [ "$(ls -A $NVME/invoices 2>/dev/null)" ]; then
    cp -rn "$NVME/invoices/"* "$NVME/media/invoices/" 2>/dev/null || true
    echo "  ✓ Copied invoices/ → media/invoices/"
else
    echo "  ⏭️  No existing invoices/ data"
fi

echo "  ✓ Data migration complete"

# Step 3: Set permissions
echo "[3/4] Setting permissions..."
chown -R deploy:deploy "$NVME/media"
chmod -R 755 "$NVME/media"
echo "  ✓ Permissions set"

# Step 4: Restart containers to pick up new volume mapping
echo "[4/4] Restarting SignSimple containers..."
cd "$DEPLOY_DIR"

# Get active colour
if grep -q "blue" active_docsign.conf 2>/dev/null; then
    ACTIVE="blue"
else
    ACTIVE="green"
fi

echo "  Active: $ACTIVE"
$COMPOSE_CMD stop docsign-api-$ACTIVE docsign-frontend-$ACTIVE docsign-celery 2>/dev/null || true

if [ "$ACTIVE" = "green" ]; then
    $COMPOSE_CMD --profile docsign-green up -d docsign-api-$ACTIVE docsign-frontend-$ACTIVE
else
    $COMPOSE_CMD up -d docsign-api-$ACTIVE docsign-frontend-$ACTIVE
fi
$COMPOSE_CMD up -d docsign-celery

echo "  ✓ Containers restarted"

# Wait and verify
sleep 8
echo ""
echo "📋 Verification:"
echo ""

echo "  MEDIA_ROOT inside container:"
docker exec docsign-api-$ACTIVE python -c "
from django.conf import settings
print('  ', settings.MEDIA_ROOT)
" 2>/dev/null || echo "  ❌ Could not check"

echo ""
echo "  Volume mount check:"
docker exec docsign-api-$ACTIVE ls -la /app/media/ 2>/dev/null || echo "  ❌ Could not list"

echo ""
echo "  NVMe media directory:"
ls -la "$NVME/media/"

echo ""
echo "=== ✅ Fix complete! ==="
echo ""
echo "  Test by:"
echo "  1. Upload a new document on signsimple.co.uk"
echo "  2. Send for signing, sign it"
echo "  3. Download — should include signatures"
echo "  4. Check: ls -la $NVME/media/documents/"
echo "  5. Check: ls -la $NVME/media/signed/"
echo ""
echo "  Old directories (safe to keep for now):"
echo "  - $NVME/documents/"
echo "  - $NVME/invoices/"
echo "  Delete after confirming new layout works."
