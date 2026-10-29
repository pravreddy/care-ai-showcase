# Testing Guide for Care AI Engine

This guide will help you set up and run tests to catch errors before they reach production.

## Quick Start

### 1. Install Test Dependencies

```bash
cd care_ai_engine
pip install -r requirements-test.txt
```

### 2. Set Up Test Database

```bash
# Make the script executable
chmod +x scripts/manage_db.sh

# Create and setup test database
./scripts/manage_db.sh test-db
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit -m unit

# Run only integration tests
pytest tests/integration -m integration

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_auth_endpoints.py

# Run specific test
pytest tests/unit/test_auth_service.py::TestAuthService::test_register_user_success
```

## Fixing Your Current Database Issue

Your production database is missing the `is_admin` column. Here's how to fix it:

### Option 1: Run Migration (Recommended)

```bash
cd care_ai_engine

# Make sure your production database connection is correct in alembic.ini
# Then run:
alembic upgrade head
```

### Option 2: Manual SQL Fix (If migration doesn't work)

Connect to your production database and run:

```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (test individual functions)
│   ├── __init__.py
│   └── test_auth_service.py
└── integration/             # Integration tests (test API endpoints)
    ├── __init__.py
    └── test_auth_endpoints.py
```

## Writing New Tests

### Unit Test Example

```python
# tests/unit/test_my_service.py
import pytest
from app.services.my_service import my_function

class TestMyService:
    @pytest.mark.asyncio
    async def test_my_function(self):
        result = await my_function("input")
        assert result == "expected_output"
```

### Integration Test Example

```python
# tests/integration/test_my_endpoints.py
import pytest
from httpx import AsyncClient

class TestMyEndpoints:
    @pytest.mark.asyncio
    async def test_my_endpoint(self, client: AsyncClient):
        response = await client.get("/api/my-endpoint")
        assert response.status_code == 200
```

## Available Fixtures

- `client`: Unauthenticated test client
- `authenticated_client`: Test client with valid JWT token
- `db_session`: Fresh database session for each test
- `test_user_data`: Sample user data dictionary
- `test_user_data_2`: Another sample user data

## CI/CD Integration

Add this to your GitHub Actions workflow:

```yaml
- name: Run Tests
  run: |
    cd care_ai_engine
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    ./scripts/manage_db.sh test-db
    pytest --cov=app --cov-report=xml
  env:
    TEST_DATABASE_URL: postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test
```

## Common Issues

### Issue: Tests fail with "database does not exist"
**Solution**: Run `./scripts/manage_db.sh test-db` to create test database

### Issue: Tests fail with "column does not exist"
**Solution**: Run migrations on test database: `DATABASE_URL=$TEST_DATABASE_URL alembic upgrade head`

### Issue: Import errors
**Solution**: Make sure you're in the `care_ai_engine` directory when running tests

## Best Practices

1. **Write tests before fixing bugs** - Reproduce the bug in a test first
2. **Test edge cases** - Empty inputs, null values, invalid data
3. **Keep tests isolated** - Each test should be independent
4. **Use meaningful test names** - `test_user_cannot_register_with_invalid_email`
5. **Test both success and failure cases** - Don't just test happy paths
6. **Run tests before committing** - Catch issues early

## Coverage Goals

- **Minimum**: 70% code coverage
- **Target**: 85% code coverage
- **Critical paths**: 95%+ coverage (auth, payments, data handling)

View coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # On Mac
# or xdg-open htmlcov/index.html on Linux
```

## Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd care_ai_engine
echo "Running tests before commit..."
pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```
