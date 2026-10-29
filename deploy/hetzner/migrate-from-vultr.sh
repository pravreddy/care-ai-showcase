#!/bin/bash
# =============================================================
# Migrate from Vultr to Hetzner
# =============================================================
# Run this on your LOCAL machine (not on either server).
# It copies data from Vultr → local → Hetzner.
#
# Prerequisites:
#   - SSH access to both servers as 'deploy' or 'root'
#   - Hetzner server already set up (server-setup.sh done)
#   - Docker running on Hetzner
# =============================================================

set -euo pipefail

VULTR_IP="${VULTR_IP:-45.32.177.231}"
HETZNER_IP="${HETZNER_IP:-YOUR_HETZNER_IP}"
VULTR_USER="${VULTR_USER:-root}"
HETZNER_USER="${HETZNER_USER:-deploy}"
BACKUP_DIR="./migration-backup-$(date +%Y%m%d)"

echo "============================================"
echo "  Vultr → Hetzner Migration"
echo "============================================"
echo "  Vultr:   ${VULTR_USER}@${VULTR_IP}"
echo "  Hetzner: ${HETZNER_USER}@${HETZNER_IP}"
echo "  Backup:  ${BACKUP_DIR}"
echo "============================================"
echo ""

mkdir -p "$BACKUP_DIR"

# ===========================================
# Step 1: Backup PostgreSQL from Vultr
# ===========================================
echo "[1/5] Backing up PostgreSQL databases from Vultr..."

# CareAI database
echo "  Dumping careai..."
ssh ${VULTR_USER}@${VULTR_IP} \
  "docker exec careai-postgres pg_dump -U careai careai" \
  > "${BACKUP_DIR}/careai.sql"
echo "  ✓ careai.sql ($(du -h ${BACKUP_DIR}/careai.sql | cut -f1))"

# SignSimple database
echo "  Dumping docsign_uk..."
ssh ${VULTR_USER}@${VULTR_IP} \
  "docker exec careai-postgres pg_dump -U careai docsign_uk" \
  > "${BACKUP_DIR}/docsign_uk.sql"
echo "  ✓ docsign_uk.sql ($(du -h ${BACKUP_DIR}/docsign_uk.sql | cut -f1))"

# ===========================================
# Step 2: Copy media files from Vultr
# ===========================================
echo "[2/5] Copying media files from Vultr..."

# SignSimple media (PDFs, signatures, logos)
rsync -avz --progress \
  ${VULTR_USER}@${VULTR_IP}:/mnt/nvme_data/docsign/media/ \
  "${BACKUP_DIR}/docsign-media/"
echo "  ✓ SignSimple media copied"

# CareAI data
rsync -avz --progress \
  ${VULTR_USER}@${VULTR_IP}:/home/deploy/careai/hdd_storage/ \
  "${BACKUP_DIR}/careai-data/" \
  --exclude='ollama' 2>/dev/null || echo "  (no careai data to copy)"
echo "  ✓ CareAI data copied"

# SSL certs (for reference, Caddy will auto-provision new ones)
rsync -avz --progress \
  ${VULTR_USER}@${VULTR_IP}:/mnt/nvme_data/ssl/ \
  "${BACKUP_DIR}/ssl-backup/" 2>/dev/null || echo "  (no SSL certs to copy)"

# ===========================================
# Step 3: Copy config files
# ===========================================
echo "[3/5] Copying config files..."

# .env files
scp ${VULTR_USER}@${VULTR_IP}:/home/deploy/careai/.env \
  "${BACKUP_DIR}/vultr-env-main" 2>/dev/null || true
scp ${VULTR_USER}@${VULTR_IP}:/home/deploy/careai/.env.docsign \
  "${BACKUP_DIR}/vultr-env-docsign" 2>/dev/null || true

echo "  ✓ Config files backed up"

# ===========================================
# Step 4: Upload to Hetzner
# ===========================================
echo "[4/5] Uploading to Hetzner..."

REMOTE_DIR="/home/${HETZNER_USER}/avyangah"

# Upload compose files
scp -r ../hetzner/* ${HETZNER_USER}@${HETZNER_IP}:${REMOTE_DIR}/
echo "  ✓ Compose files uploaded"

# Upload database backups
scp "${BACKUP_DIR}/careai.sql" ${HETZNER_USER}@${HETZNER_IP}:${REMOTE_DIR}/
scp "${BACKUP_DIR}/docsign_uk.sql" ${HETZNER_USER}@${HETZNER_IP}:${REMOTE_DIR}/
echo "  ✓ Database backups uploaded"

# Upload media
rsync -avz --progress \
  "${BACKUP_DIR}/docsign-media/" \
  ${HETZNER_USER}@${HETZNER_IP}:${REMOTE_DIR}/docsign-media/
echo "  ✓ Media files uploaded"

# ===========================================
# Step 5: Restore on Hetzner
# ===========================================
echo "[5/5] Restoring databases on Hetzner..."

ssh ${HETZNER_USER}@${HETZNER_IP} bash << 'REMOTE_SCRIPT'
cd ~/avyangah

# Start only PostgreSQL first
docker compose up -d postgres
echo "Waiting for PostgreSQL..."
sleep 10

# Create databases
docker compose exec -T postgres psql -U avyangah -d avyangah -c "CREATE DATABASE careai;" 2>/dev/null || true
docker compose exec -T postgres psql -U avyangah -d avyangah -c "CREATE DATABASE docsign_uk;" 2>/dev/null || true

# Restore CareAI
echo "Restoring careai database..."
docker compose exec -T postgres psql -U avyangah -d careai < careai.sql
echo "  ✓ careai restored"

# Restore SignSimple
echo "Restoring docsign_uk database..."
docker compose exec -T postgres psql -U avyangah -d docsign_uk < docsign_uk.sql
echo "  ✓ docsign_uk restored"

# Copy media into Docker volume
docker compose up -d docsign-api-blue 2>/dev/null || true
sleep 5
# The media will be available via the volume mount

# Clean up SQL files
rm -f careai.sql docsign_uk.sql

echo "  ✓ All databases restored"
REMOTE_SCRIPT

echo ""
echo "============================================"
echo "  Migration Data Transfer Complete!"
echo "============================================"
echo ""
echo "  Next steps on Hetzner:"
echo "  1. SSH in: ssh ${HETZNER_USER}@${HETZNER_IP}"
echo "  2. cd ~/avyangah"
echo "  3. Copy .env.template to .env and fill values"
echo "  4. Login to GitHub registry"
echo "  5. Start all services:"
echo "     docker compose -f docker-compose.yml \\"
echo "       -f docker-compose.careai.yml \\"
echo "       -f docker-compose.docsign.yml \\"
echo "       up -d"
echo "  6. Test both apps via server IP"
echo "  7. When ready: update DNS A records"
echo ""
echo "  Local backup saved in: ${BACKUP_DIR}"
echo "============================================"
