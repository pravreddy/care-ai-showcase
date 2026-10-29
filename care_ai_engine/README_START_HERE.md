# 🚀 QUICK START - Fix Production & Setup Tests

## ⚠️ YOUR PRODUCTION IS BROKEN - FIX IT NOW!

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai/care_ai_engine

# Make scripts executable
chmod +x scripts/*.sh

# Fix the database (adds missing is_admin column)
./scripts/fix_database.sh
```

**What this does**: Runs the migration that adds the `is_admin` column to the `users` table. This will fix the error:
```
column users.is_admin does not exist
```

---

## ✅ Verify The Fix

Try registering a user:

```bash
curl -X POST http://your-domain/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

If you get a 201 response, **you're fixed!** ✅

---

## 🧪 Set Up Testing (To Prevent This From Happening Again)

### 1. Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### 2. Create Test Database

```bash
./scripts/manage_db.sh test-db
```

### 3. Run Tests

```bash
pytest
```

You should see output like:
```
tests/unit/test_auth_service.py ......           [ 50%]
tests/integration/test_auth_endpoints.py ......  [100%]

============= 12 passed in 2.34s =============
```

### 4. Check Coverage

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 📁 What I Created For You

### Core Files
- ✅ **Migration file** (`alembic/versions/001_initial_schema.py`) - Fixes the database
- ✅ **12 tests** - Catches errors before production
- ✅ **Test configuration** (`pytest.ini`, `conftest.py`)
- ✅ **Management scripts** (`scripts/manage_db.sh`, `scripts/fix_database.sh`)

### Documentation
- ✅ **SETUP_COMPLETE.md** - Overview of everything
- ✅ **TESTING.md** - Complete testing guide
- ✅ **DATABASE_MIGRATIONS.md** - Migration management guide
- ✅ **requirements-test.txt** - Test dependencies

---

## 🎯 How To Use This Going Forward

### Before Making Any Code Changes:
1. Write a test that fails
2. Make the code change
3. Run tests: `pytest`
4. If tests pass, commit

### Before Deploying To Production:
1. Run all tests: `pytest`
2. Create migration (if needed): `alembic revision --autogenerate -m "description"`
3. Test migration locally: `alembic upgrade head`
4. Backup production database
5. Apply migration to production: `alembic upgrade head`
6. Deploy code
7. Verify everything works

---

## 🔧 Common Commands

### Database Management
```bash
# Check current database version
alembic current

# Run pending migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# Setup test database
./scripts/manage_db.sh test-db
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run specific test
pytest tests/unit/test_auth_service.py::TestAuthService::test_register_user_success

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

---

## 🐛 If Tests Fail

### "database does not exist"
```bash
./scripts/manage_db.sh test-db
```

### "column does not exist"
```bash
DATABASE_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test" \
  alembic upgrade head
```

### "import errors"
```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai/care_ai_engine
export PYTHONPATH=$PWD
pytest
```

---

## 📊 Test Coverage

Current test coverage:

- **Auth Service** ✅
  - User registration
  - Password verification
  - Token creation
  - Duplicate email handling
  - Field validation

- **Auth Endpoints** ✅
  - Registration endpoint
  - Login endpoint
  - Get current user
  - Error handling
  - Invalid data handling

**Next Steps**: Add tests for:
- Voice notes
- Partner accounts
- Coupon system
- Usage tracking

---

## 🚨 Emergency Production Fixes

### If production breaks:

1. **Check logs**:
   ```bash
   docker logs careai-api --tail 100
   ```

2. **Check database state**:
   ```bash
   alembic current
   ```

3. **Apply missing migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Restart service**:
   ```bash
   docker-compose restart careai-api
   ```

---

## 📝 Example: Adding a New Feature

Let's say you want to add a "user preferences" feature:

### 1. Write the test first
```python
# tests/unit/test_user_preferences.py
@pytest.mark.asyncio
async def test_user_can_set_preferences(db_session):
    user = await create_user(db_session, "test@example.com")
    prefs = await set_user_preferences(db_session, user.id, {"theme": "dark"})
    assert prefs["theme"] == "dark"
```

### 2. Run the test (it should fail)
```bash
pytest tests/unit/test_user_preferences.py
```

### 3. Implement the feature
```python
# app/services/preference_service.py
async def set_user_preferences(db, user_id, preferences):
    # Implementation here
    pass
```

### 4. Run tests again
```bash
pytest
```

### 5. If tests pass, commit and deploy!

---

## 🎓 Key Lessons

### What Went Wrong
- Code expected `is_admin` column
- Database didn't have it
- No tests caught it
- Production broke

### How We Fixed It
- Created migration to add column
- Wrote tests to prevent future issues
- Set up testing infrastructure
- Documented everything

### How To Prevent It
- Always write tests
- Run tests before deploying
- Use migrations for database changes
- Never manually edit production database

---

## 📚 Read More

- **SETUP_COMPLETE.md** - Comprehensive overview
- **TESTING.md** - Detailed testing guide
- **DATABASE_MIGRATIONS.md** - Migration best practices

---

## ✅ Checklist - Do These Now!

- [ ] Fix production: `./scripts/fix_database.sh`
- [ ] Verify fix works (try registering a user)
- [ ] Install test dependencies: `pip install -r requirements-test.txt`
- [ ] Setup test database: `./scripts/manage_db.sh test-db`
- [ ] Run tests: `pytest`
- [ ] Read TESTING.md
- [ ] Make testing part of your workflow

---

## 💡 Pro Tips

1. **Run tests before every commit**: `pytest`
2. **Check coverage regularly**: `pytest --cov=app`
3. **Write tests for bugs**: Reproduce the bug in a test first
4. **Keep tests fast**: Fast tests = tests you'll actually run
5. **Use fixtures**: Share setup code across tests (see `conftest.py`)

---

## 🆘 Need Help?

If you're stuck:

1. Read the error message carefully
2. Check `TESTING.md` for test issues
3. Check `DATABASE_MIGRATIONS.md` for migration issues
4. Run `alembic current` to see database state
5. Check if test database exists: `./scripts/manage_db.sh test-db`

---

**Remember: The time you spend on tests now saves you hours of debugging later!** 🎯

Good luck, and happy testing! 🚀
