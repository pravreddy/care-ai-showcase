# 🔧 QUICK FIX - Migration Error

## The Problem

You got this error:
```
ModuleNotFoundError: No module named 'app'
```

This happens because alembic can't find the `app` module inside the Docker container.

## The Fix

I've already fixed the `alembic/env.py` file. Now you need to rebuild the container:

```bash
# Stop the API container
docker-compose -f docker-compose.local.yml stop api

# Rebuild the API container
docker-compose -f docker-compose.local.yml build api

# Start it again
docker-compose -f docker-compose.local.yml up -d api

# Wait for it to be healthy
sleep 10

# Now run migrations
docker exec careai-api-local alembic upgrade head
```

## Alternative: Run Migration a Different Way

If rebuild doesn't work, try running the migration with Python path set:

```bash
docker exec careai-api-local sh -c "cd /app && PYTHONPATH=/app alembic upgrade head"
```

## Or: Run Migration from Inside Container

```bash
# Enter the container
docker exec -it careai-api-local sh

# Inside container, set Python path
export PYTHONPATH=/app

# Run migration
alembic upgrade head

# Exit container
exit
```

## Verify It Worked

```bash
# Check current migration
docker exec careai-api-local sh -c "cd /app && PYTHONPATH=/app alembic current"

# You should see: 001_initial_schema (head)
```

## Complete Fix Steps

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai

# 1. Rebuild API
docker-compose -f docker-compose.local.yml build api

# 2. Restart API
docker-compose -f docker-compose.local.yml up -d api

# 3. Run migration with PYTHONPATH
docker exec careai-api-local sh -c "cd /app && PYTHONPATH=/app alembic upgrade head"

# 4. Verify
docker exec careai-api-local sh -c "cd /app && PYTHONPATH=/app alembic current"

# 5. Test health
curl http://localhost:8000/health
```

That should fix it! 🎉
