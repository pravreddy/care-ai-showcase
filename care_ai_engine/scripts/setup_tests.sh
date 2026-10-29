#!/bin/bash

# Quick Setup Script - Run this to get started
# This script will:
# 1. Check dependencies
# 2. Set up test database
# 3. Run tests
# 4. Show you what to do next

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         Care AI Testing Setup                            ║"
echo "║         Quick Setup Script                               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this from the care_ai_engine directory${NC}"
    exit 1
fi

# Step 1: Check Python
print_section "Step 1: Checking Python installation"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

# Step 2: Check PostgreSQL
print_section "Step 2: Checking PostgreSQL"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL found${NC}"
else
    echo -e "${YELLOW}! PostgreSQL not found in PATH (might still be running)${NC}"
fi

# Step 3: Install test dependencies
print_section "Step 3: Installing test dependencies"
echo "Installing from requirements-test.txt..."
pip install -q -r requirements-test.txt
echo -e "${GREEN}✓ Test dependencies installed${NC}"

# Step 4: Make scripts executable
print_section "Step 4: Making scripts executable"
chmod +x scripts/*.sh
echo -e "${GREEN}✓ Scripts are now executable${NC}"

# Step 5: Setup test database
print_section "Step 5: Setting up test database"
echo "Creating test database and running migrations..."
./scripts/manage_db.sh test-db
echo -e "${GREEN}✓ Test database ready${NC}"

# Step 6: Run tests
print_section "Step 6: Running tests"
echo "Running pytest..."
pytest -v
TESTS_PASSED=$?

echo ""
if [ $TESTS_PASSED -eq 0 ]; then
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ✓ All tests passed! You're ready to go!                ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
else
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ✗ Some tests failed. Check the output above.           ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
fi

# Next steps
print_section "Next Steps"
echo ""
echo -e "${YELLOW}Production Fix:${NC}"
echo "  If your production database is broken, run:"
echo -e "  ${GREEN}./scripts/fix_database.sh${NC}"
echo ""
echo -e "${YELLOW}Development Workflow:${NC}"
echo "  1. Make changes to your code"
echo "  2. Run tests: ${GREEN}pytest${NC}"
echo "  3. If tests pass, commit and deploy"
echo ""
echo -e "${YELLOW}Common Commands:${NC}"
echo "  Run tests:           ${GREEN}pytest${NC}"
echo "  With coverage:       ${GREEN}pytest --cov=app${NC}"
echo "  Specific test:       ${GREEN}pytest tests/unit/test_auth_service.py${NC}"
echo "  Database migration:  ${GREEN}alembic upgrade head${NC}"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  Quick start:         ${GREEN}README_START_HERE.md${NC}"
echo "  Testing guide:       ${GREEN}TESTING.md${NC}"
echo "  Database guide:      ${GREEN}DATABASE_MIGRATIONS.md${NC}"
echo ""
echo -e "${BLUE}Happy testing! 🚀${NC}"
echo ""
