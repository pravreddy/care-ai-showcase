# 🚀 Quick Reference Card

**Keep this open while developing!**

---

## 🔥 Most Used Commands

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f careai-api

# Run tests
pytest

# Run migrations
alembic upgrade head

# Check health
curl http://localhost:8000/health
```

---

## 📂 File Locations

```
Configuration:     .env
Database Models:   app/models/database.py
API Routes:        app/api/
Services:          app/services/
Tests:             tests/
Migrations:        alembic/versions/
Scripts:           scripts/
```

---

## 🗄️ Database

```bash
# Connect to database
psql -U careai -d careai

# Run migrations
alembic upgrade head

# Check current version
alembic current

# Create migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_auth_service.py

# Verbose output
pytest -vv

# Setup test database
./scripts/manage_db.sh test-db
```

---

## 🐳 Docker

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f <service>

# Restart service
docker-compose restart <service>

# Rebuild
docker-compose up -d --build

# Services: careai-api, postgres, redis, ollama
```

---

## 🔐 Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"Test123!"}'

# Get current user
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

---

## 🤖 MCP & AI

```bash
# List MCP tools
curl http://localhost:8000/api/agent/mcp/tools \
  -H "Authorization: Bearer TOKEN"

# Ask question
curl -X POST http://localhost:8000/api/agent/ask \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is paracetamol?"}'

# Direct MCP call
curl -X POST http://localhost:8000/api/agent/mcp/call \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"search_nhs","arguments":{"query":"diabetes"}}'
```

---

## ⚡ Redis

```bash
# Ping
redis-cli ping

# Clear cache
redis-cli FLUSHDB

# Check keys
redis-cli KEYS "*"

# Get value
redis-cli GET key

# Monitor
redis-cli MONITOR
```

---

## 🧠 Ollama

```bash
# List models
ollama list

# Pull model
ollama pull llama3.2:3b

# Test model
ollama run llama3.2:3b "Say hello"

# Check service
curl http://localhost:11434/api/tags
```

---

## 🐛 Debugging

```bash
# View logs
docker-compose logs -f careai-api

# Check service status
docker-compose ps

# Exec into container
docker-compose exec careai-api bash

# Check environment
cat .env

# Test database connection
psql -U careai -d careai -c "SELECT 1;"

# Test Redis
redis-cli ping

# Full restart
docker-compose down && docker-compose up -d
```

---

## 📊 Health Checks

```bash
# Ping
curl http://localhost:8000/ping

# Full health check
curl http://localhost:8000/health | python3 -m json.tool

# Check specific service
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/ollama
```

---

## 🔄 Common Workflows

### Add New Feature
```bash
git checkout -b feature/name
# Write failing test
pytest tests/unit/test_feature.py  # Should fail
# Implement feature
pytest  # Should pass
git commit -m "Add feature"
```

### Fix Database Issue
```bash
alembic current  # Check version
./scripts/fix_database.sh  # Fix
psql -U careai -d careai -c "\d users"  # Verify
```

### Debug API Issue
```bash
docker-compose logs -f careai-api
curl http://localhost:8000/health
pytest tests/integration/  # Run integration tests
```

---

## 🎯 URLs

```
API:              http://localhost:8000
API Docs:         http://localhost:8000/docs
Redoc:            http://localhost:8000/redoc
Health:           http://localhost:8000/health
Ollama:           http://localhost:11434
```

---

## 🆘 Emergency Fixes

### Can't connect to database
```bash
docker-compose restart postgres
alembic upgrade head
```

### Can't connect to Redis
```bash
docker-compose restart redis
redis-cli ping
```

### Ollama not responding
```bash
docker-compose restart ollama
docker-compose exec ollama ollama list
```

### Port already in use
```bash
lsof -i :8000
kill -9 <PID>
```

### Tests failing
```bash
./scripts/manage_db.sh test-db
pytest -vv
```

### Import errors
```bash
source venv/bin/activate
export PYTHONPATH=$PWD
pip install -r requirements.txt
```

---

## 📚 Documentation

- **Setup**: [LOCAL_SETUP.md](LOCAL_SETUP.md)
- **Testing**: [TESTING.md](TESTING.md)
- **Migrations**: [DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md)
- **API**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 💡 Pro Tips

1. **Always activate venv**: `source venv/bin/activate`
2. **Run tests before commit**: `pytest`
3. **Check logs when stuck**: `docker-compose logs -f`
4. **Use API docs**: `http://localhost:8000/docs`
5. **Clear Redis cache**: `redis-cli FLUSHDB`
6. **Fresh start**: `docker-compose down -v && docker-compose up -d`

---

**Print this and keep it nearby!** 📋
