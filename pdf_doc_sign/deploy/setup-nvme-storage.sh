#!/bin/bash
# =============================================================
# NVMe Block Storage Setup — Vultr London
# =============================================================
# Run ONCE after attaching 10GB NVMe (pdf-ai-store) in Vultr.
#
# Usage: sudo bash setup-nvme-storage.sh
# =============================================================

set -euo pipefail

DEVICE="/dev/vdb"
MOUNT_POINT="/mnt/nvme_data"

echo "============================================"
echo "  NVMe Block Storage Setup"
echo "============================================"

if [ ! -b "$DEVICE" ]; then
    echo "ERROR: $DEVICE not found. Is the block storage attached in Vultr?"
    exit 1
fi

# 1. Partition + format (skip if already done)
echo "[1/6] Creating partition..."
if ! lsblk -n -o FSTYPE "${DEVICE}1" 2>/dev/null | grep -q ext4; then
    sudo parted -s $DEVICE mklabel gpt
    sudo parted -s $DEVICE unit mib mkpart primary 0% 100%
    sudo mkfs.ext4 "${DEVICE}1"
    echo "  ✓ Formatted as ext4"
else
    echo "  ✓ Already formatted"
fi

# 2. Mount point
echo "[2/6] Creating mount point..."
sudo mkdir -p $MOUNT_POINT

# 3. Add to fstab
echo "[3/6] Adding to /etc/fstab..."
UUID=$(sudo blkid -s UUID -o value "${DEVICE}1")
if ! grep -q "$UUID" /etc/fstab; then
    echo "UUID=$UUID $MOUNT_POINT ext4 defaults,noatime,nofail 0 2" | sudo tee -a /etc/fstab
    echo "  ✓ Added to fstab"
else
    echo "  ✓ Already in fstab"
fi

# 4. Mount
echo "[4/6] Mounting..."
sudo mount -a
echo "  ✓ Mounted at $MOUNT_POINT"

# 5. Create directories (matching docker-compose volume mounts)
echo "[5/6] Creating directories..."

# Shared infrastructure
sudo mkdir -p $MOUNT_POINT/postgres_data
sudo mkdir -p $MOUNT_POINT/redis_data
sudo mkdir -p $MOUNT_POINT/ssl

# Care AI
sudo mkdir -p $MOUNT_POINT/logs
sudo mkdir -p $MOUNT_POINT/careai/blue
sudo mkdir -p $MOUNT_POINT/careai/green

# DocSign / SignSimple
sudo mkdir -p $MOUNT_POINT/docsign/documents
sudo mkdir -p $MOUNT_POINT/docsign/invoices
sudo mkdir -p $MOUNT_POINT/docsign/media
sudo mkdir -p $MOUNT_POINT/docsign/static

# Backups
sudo mkdir -p $MOUNT_POINT/backups

echo "  ✓ Directories created"

# 6. Permissions
echo "[6/6] Setting permissions..."
sudo chown -R deploy:deploy $MOUNT_POINT
sudo chown -R 70:70 $MOUNT_POINT/postgres_data     # Postgres container UID
sudo chown -R 999:999 $MOUNT_POINT/redis_data       # Redis container UID
echo "  ✓ Permissions set"

echo ""
echo "============================================"
echo "  ✅ NVMe Ready!"
echo "============================================"
df -h $MOUNT_POINT
echo ""
echo "  Structure:"
ls -la $MOUNT_POINT/
echo ""
echo "  Next: sudo bash migrate-to-nvme.sh"
echo "============================================"
