# 🔧 DATABASE CONNECTION FIX

## The Problem

The error shows:
```
OSError: Multiple exceptions: [Errno 111] Connect call failed ('::1', 5432, 0, 0), [Errno 111] Connect call failed ('127.0.0.1', 5432)
```

This means alembic is trying to connect to `localhost:5432` but inside Docker, the database is at `postgres:5432`.

## The Fix

I've updated `alembic/env.py` to read `DATABASE_URL` from environment variable (which is set in docker-compose to `postgres:5432`).

## Run These Commands

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai

# 1. Rebuild API container (picks up the fix)
docker-compose -f docker-compose.local.yml build api

# 2. Restart API
docker-compose -f docker-compose.local.yml up -d api

# 3. Wait for it to start
sleep 15

# 4. Run migration (DATABASE_URL is already set in docker-compose)
docker exec careai-api-local alembic upgrade head

# 5. Verify it worked
docker exec careai-api-local alembic current
```

**Expected output:** `001_initial_schema (head)`

---

## Test It Works

```bash
# Backend health
curl http://localhost:8000/health

# Should return:
# {
#   "status": "healthy",
#   "services": {
#     "database": "connected",
#     ...
#   }
# }
```

---

## What I Fixed

**File:** `care_ai_engine/alembic/env.py`

**Change:** Added code to read `DATABASE_URL` from environment variable:

```python
# Override sqlalchemy.url from environment variable if set
if os.getenv('DATABASE_URL'):
    config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))
```

This way, when running in Docker, it uses `postgres:5432` (from the environment variable set in docker-compose.yml).

---

## If You Still Get Errors

Check that the DATABASE_URL is set correctly:

```bash
# Check environment variable in container
docker exec careai-api-local printenv DATABASE_URL

# Should show:
# postgresql+asyncpg://careai:careai_secret@postgres:5432/careai
```

---

**Now it should work!** 🚀
