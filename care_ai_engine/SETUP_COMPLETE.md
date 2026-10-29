# Care AI - Testing & Database Setup Guide

## 🚨 IMMEDIATE FIX FOR PRODUCTION

Your production is broken because the database is missing the `is_admin` column. **Fix it now:**

```bash
cd care_ai_engine
chmod +x scripts/fix_database.sh
./scripts/fix_database.sh
```

This runs the migration that adds the missing column.

---

## What I've Set Up For You

I've created a complete testing infrastructure to prevent these issues in the future:

### 📁 New Files Created

```
care_ai_engine/
├── alembic/
│   └── versions/
│       └── 001_initial_schema.py          # Migration that fixes is_admin
├── scripts/
│   ├── manage_db.sh                       # Database management tool
│   └── fix_database.sh                    # Quick fix for production
├── tests/
│   ├── conftest.py                        # Test configuration & fixtures
│   ├── unit/
│   │   └── test_auth_service.py          # Unit tests for auth
│   └── integration/
│       └── test_auth_endpoints.py        # Integration tests for API
├── pytest.ini                             # Pytest configuration
├── requirements-test.txt                  # Test dependencies
├── TESTING.md                            # Complete testing guide
└── DATABASE_MIGRATIONS.md                # Migration guide
```

---

## 🚀 Quick Start

### 1. Fix Production (Do this first!)

```bash
cd care_ai_engine
chmod +x scripts/*.sh
./scripts/fix_database.sh
```

### 2. Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### 3. Set Up Test Database

```bash
./scripts/manage_db.sh test-db
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

---

## 📊 What The Tests Cover

### Unit Tests (`tests/unit/test_auth_service.py`)
- ✅ User registration
- ✅ Password hashing and verification
- ✅ JWT token creation
- ✅ Duplicate email handling
- ✅ All required fields including `is_admin`

### Integration Tests (`tests/integration/test_auth_endpoints.py`)
- ✅ Registration endpoint
- ✅ Login endpoint
- ✅ Get current user endpoint
- ✅ Authentication flows
- ✅ Error handling
- ✅ Field validation
- ✅ `is_admin` field presence

---

## 🔧 Database Management

### Common Commands

```bash
# Run migrations
alembic upgrade head

# Check current version
alembic current

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# Reset database (dev only!)
./scripts/manage_db.sh reset
```

---

## 🎯 How This Prevents Future Issues

### Before (What caused your problem):
1. You changed the code (added `is_admin` to User model)
2. Database wasn't updated
3. Code tried to use column that doesn't exist
4. **💥 Production breaks**

### Now (With this setup):
1. Change code
2. Create migration: `alembic revision --autogenerate -m "add is_admin"`
3. Run tests locally: `pytest`
4. Tests fail if database doesn't match code
5. Fix migration, run tests again
6. Apply to production: `alembic upgrade head`
7. **✅ Everything works**

---

## 📝 Example: Adding a New Field

Let's say you want to add a `phone_number` field to users:

### 1. Update the model
```python
# app/models/database.py
class User(Base):
    # ... existing fields ...
    phone_number = Column(String(20), nullable=True)
```

### 2. Create migration
```bash
alembic revision --autogenerate -m "add phone_number to users"
```

### 3. Review the migration
```bash
cat alembic/versions/xxxx_add_phone_number_to_users.py
```

### 4. Write a test
```python
# tests/unit/test_user_model.py
def test_user_has_phone_number(db_session):
    user = User(
        email="test@example.com",
        phone_number="+1234567890"
    )
    assert user.phone_number == "+1234567890"
```

### 5. Run tests
```bash
pytest
```

### 6. Apply to production
```bash
alembic upgrade head
```

---

## 🔍 Debugging Failed Tests

### Test fails with "database does not exist"
```bash
./scripts/manage_db.sh test-db
```

### Test fails with "column does not exist"
```bash
DATABASE_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test" \
  alembic upgrade head
```

### Import errors
```bash
# Make sure you're in the right directory
cd care_ai_engine
pip install -e .
```

---

## 📋 Pre-Deployment Checklist

Before deploying to production, always:

- [ ] Run all tests: `pytest`
- [ ] Check test coverage: `pytest --cov=app`
- [ ] Review migrations: `alembic history`
- [ ] Backup database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Monitor logs after deployment

---

## 🆘 Emergency Production Fix

If production breaks:

### Quick Fix
```bash
# SSH to production
cd /path/to/care_ai_engine

# Run the fix script
./scripts/fix_database.sh

# Restart the service
docker-compose restart careai-api
```

### Manual Fix
```sql
-- Connect to database
psql -h localhost -U careai -d careai

-- Check what columns exist
\d users

-- Add missing column (if needed)
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;

-- Verify
\d users
```

---

## 📚 Documentation Files

- **`TESTING.md`** - Complete guide to writing and running tests
- **`DATABASE_MIGRATIONS.md`** - Everything about database migrations
- **`README.md`** - Main project documentation

---

## 🎓 Best Practices Moving Forward

1. **Write tests first** - When fixing bugs, write a test that reproduces it
2. **Test locally** - Always run tests before committing
3. **Use migrations** - Never manually change production database
4. **Review migrations** - Auto-generated migrations aren't always perfect
5. **Keep tests fast** - Fast tests = tests you'll actually run
6. **Test edge cases** - Empty inputs, null values, invalid data
7. **Monitor coverage** - Aim for 80%+ coverage

---

## 🚦 CI/CD Integration (Future)

Add to your GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: careai_secret
          POSTGRES_USER: careai
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd care_ai_engine
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests
        run: |
          cd care_ai_engine
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## ✅ What You Should Do Right Now

1. **Fix production**: `./scripts/fix_database.sh`
2. **Verify it works**: Try registering a user
3. **Set up tests locally**: 
   ```bash
   pip install -r requirements-test.txt
   ./scripts/manage_db.sh test-db
   pytest
   ```
4. **Read the docs**: Start with `TESTING.md`
5. **Make tests part of your workflow**: Run before every commit

---

## 💡 Questions?

If you run into issues:

1. Check the error message carefully
2. Look in `TESTING.md` or `DATABASE_MIGRATIONS.md`
3. Run `alembic current` to check database state
4. Check if migrations are applied: `alembic history`
5. Make sure test database exists: `./scripts/manage_db.sh test-db`

---

**Remember**: Tests are not extra work - they save you time by catching bugs before production! 🎯
