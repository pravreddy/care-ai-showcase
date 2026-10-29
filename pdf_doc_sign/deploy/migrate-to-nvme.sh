#!/bin/bash
# =============================================================
# Migrate Docker Volumes → NVMe Block Storage
# =============================================================
# Run ONCE after running setup-nvme-storage.sh.
# Moves Postgres, Redis data from Docker volumes to NVMe.
# Copies existing SSL certs to NVMe.
#
# WARNING: Requires stopping containers briefly (2-5 min).
#
# Usage: sudo bash migrate-to-nvme.sh
# =============================================================

set -euo pipefail

NVME="/mnt/nvme_data"
DEPLOY_DIR="/home/deploy/careai"

echo "============================================"
echo "  Migrate to NVMe Block Storage"
echo "============================================"

if ! mountpoint -q "$NVME"; then
    echo "ERROR: $NVME not mounted. Run setup-nvme-storage.sh first."
    exit 1
fi

echo "NVMe storage:"
df -h "$NVME"
echo ""

read -p "This will stop containers for 2-5 minutes. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 0; fi

cd "$DEPLOY_DIR"

# --- Step 1: Stop containers ---
echo "[1/5] Stopping containers..."
docker compose down 2>/dev/null || true
docker compose -f docker-compose.yml -f docker-compose.docsign.yml down 2>/dev/null || true
echo "  ✓ Stopped"

# --- Step 2: Copy Postgres data ---
echo "[2/5] Migrating Postgres..."
POSTGRES_VOL=$(docker volume inspect careai_postgres-data --format '{{.Mountpoint}}' 2>/dev/null || echo "")
if [ -n "$POSTGRES_VOL" ] && [ -d "$POSTGRES_VOL" ]; then
    if [ "$(ls -A $NVME/postgres_data 2>/dev/null)" ]; then
        echo "  ⚠ $NVME/postgres_data already has data — skipping"
    else
        sudo cp -a "$POSTGRES_VOL"/. "$NVME/postgres_data/"
        sudo chown -R 70:70 "$NVME/postgres_data"
        echo "  ✓ Postgres copied"
    fi
else
    echo "  ⚠ No existing Postgres volume found (will be created fresh)"
fi

# --- Step 3: Copy Redis data ---
echo "[3/5] Migrating Redis..."
REDIS_VOL=$(docker volume inspect careai_redis-data --format '{{.Mountpoint}}' 2>/dev/null || echo "")
if [ -n "$REDIS_VOL" ] && [ -d "$REDIS_VOL" ]; then
    if [ "$(ls -A $NVME/redis_data 2>/dev/null)" ]; then
        echo "  ⚠ Already has data — skipping"
    else
        sudo cp -a "$REDIS_VOL"/. "$NVME/redis_data/"
        sudo chown -R 999:999 "$NVME/redis_data"
        echo "  ✓ Redis copied"
    fi
else
    echo "  ⚠ No existing Redis volume"
fi

# --- Step 4: Copy Care AI logs/data ---
echo "[4/5] Migrating Care AI data..."
for VOL_NAME in careai_api-logs careai_api-data; do
    VOL_PATH=$(docker volume inspect "$VOL_NAME" --format '{{.Mountpoint}}' 2>/dev/null || echo "")
    if [ -n "$VOL_PATH" ] && [ -d "$VOL_PATH" ]; then
        if echo "$VOL_NAME" | grep -q "logs"; then
            TARGET="$NVME/logs"
        else
            TARGET="$NVME/careai/blue"
        fi
        mkdir -p "$TARGET"
        if [ "$(ls -A $TARGET 2>/dev/null)" ]; then
            echo "  ⚠ $TARGET already has data — skipping"
        else
            sudo cp -a "$VOL_PATH"/. "$TARGET/"
            sudo chown -R deploy:deploy "$TARGET"
            echo "  ✓ $VOL_NAME → $TARGET"
        fi
    fi
done

# --- Step 5: Copy SSL certs (keep original names) ---
echo "[5/5] Copying SSL certificates..."
if [ -f "$DEPLOY_DIR/ssl/fullchain.pem" ]; then
    sudo cp "$DEPLOY_DIR/ssl/fullchain.pem" "$NVME/ssl/fullchain.pem"
    sudo cp "$DEPLOY_DIR/ssl/privkey.pem" "$NVME/ssl/privkey.pem"
    # Also copy default.conf if present
    [ -f "$DEPLOY_DIR/ssl/default.conf" ] && sudo cp "$DEPLOY_DIR/ssl/default.conf" "$NVME/ssl/default.conf"
    sudo chown deploy:deploy "$NVME/ssl/"*
    sudo chmod 600 "$NVME/ssl/"*.pem
    echo "  ✓ SSL certs copied to $NVME/ssl/"
else
    echo "  ⚠ No existing SSL certs at $DEPLOY_DIR/ssl/"
fi

echo ""
echo "============================================"
echo "  ✅ Migration Complete!"
echo "============================================"
echo ""
echo "  NVMe usage:"
du -sh "$NVME"/* 2>/dev/null
echo ""
echo "  Next:"
echo "  1. Start services: docker compose up -d"
echo "  2. Verify: curl https://careaisoftware.co.uk/ping"
echo "  3. If OK, wait 48 hours then remove old Docker volumes:"
echo "     docker volume ls | grep careai"
echo "     docker volume rm careai_postgres-data careai_redis-data careai_api-logs careai_api-data"
echo "============================================"
