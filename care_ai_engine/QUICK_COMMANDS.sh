#!/bin/bash

# 🎯 ONE-LINER FIXES
# Copy and paste these commands based on what you need

echo "════════════════════════════════════════════════════════════════"
echo "   CARE AI - ONE-LINER COMMAND REFERENCE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Fix production
echo "🚨 FIX PRODUCTION (Do this first!):"
echo "   cd care_ai_engine && chmod +x scripts/*.sh && ./scripts/fix_database.sh"
echo ""

# Setup tests
echo "🧪 SETUP TESTS:"
echo "   cd care_ai_engine && pip install -r requirements-test.txt && ./scripts/manage_db.sh test-db"
echo ""

# Run tests
echo "✅ RUN TESTS:"
echo "   cd care_ai_engine && pytest"
echo ""

# With coverage
echo "📊 RUN TESTS WITH COVERAGE:"
echo "   cd care_ai_engine && pytest --cov=app --cov-report=html && open htmlcov/index.html"
echo ""

# Apply migrations
echo "🗄️  APPLY DATABASE MIGRATIONS:"
echo "   cd care_ai_engine && alembic upgrade head"
echo ""

# Check database version
echo "🔍 CHECK DATABASE VERSION:"
echo "   cd care_ai_engine && alembic current"
echo ""

# Create migration
echo "📝 CREATE NEW MIGRATION:"
echo "   cd care_ai_engine && alembic revision --autogenerate -m 'your description'"
echo ""

# Full setup (first time)
echo "⚙️  COMPLETE FIRST-TIME SETUP:"
echo "   cd care_ai_engine && chmod +x scripts/*.sh && pip install -r requirements-test.txt && ./scripts/setup_tests.sh"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "📚 READ DOCUMENTATION:"
echo "   Start with: cat care_ai_engine/README_START_HERE.md"
echo "   Or open:    care_ai_engine/INDEX.md (navigation guide)"
echo "════════════════════════════════════════════════════════════════"
