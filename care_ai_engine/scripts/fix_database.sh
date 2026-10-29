#!/bin/bash

# Quick fix script for the is_admin column issue
# This script will apply the migration to fix the missing column

set -e

echo "=========================================="
echo "Care AI - Database Migration Fix"
echo "=========================================="
echo ""
echo "This script will:"
echo "  1. Run the initial schema migration"
echo "  2. Add the missing is_admin column"
echo "  3. Verify the migration was successful"
echo ""

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "ERROR: Alembic is not installed"
    echo "Please install with: pip install alembic"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    echo "ERROR: alembic.ini not found"
    echo "Please run this script from the care_ai_engine directory"
    exit 1
fi

echo "Step 1: Checking current database revision..."
alembic current

echo ""
echo "Step 2: Running migrations..."
alembic upgrade head

echo ""
echo "Step 3: Verifying migration..."
alembic current

echo ""
echo "=========================================="
echo "✅ Migration complete!"
echo "=========================================="
echo ""
echo "The is_admin column has been added to the users table."
echo "You should now be able to register users successfully."
echo ""
echo "To verify, try registering a user:"
echo "  curl -X POST http://localhost:8000/api/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"password\":\"Test123!\",\"full_name\":\"Test User\"}'"
echo ""
