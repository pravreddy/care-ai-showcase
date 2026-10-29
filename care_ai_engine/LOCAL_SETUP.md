# 🏠 Local Development Setup Guide

**Complete step-by-step guide to run Care AI locally before deploying to server**

---

## 📋 Table of Contents

1. [Prerequisites Check](#prerequisites-check)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Redis Setup](#redis-setup)
5. [Ollama Setup](#ollama-setup)
6. [Application Setup](#application-setup)
7. [Testing Everything](#testing-everything)
8. [Common Errors & Fixes](#common-errors--fixes)
9. [Development Workflow](#development-workflow)

---

## 1. Prerequisites Check

### Required Software

Run these commands to check what you have:

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version  # Should be 3.11+

# Check Git
git --version

# Check PostgreSQL (optional if using Docker)
psql --version

# Check Redis (optional if using Docker)
redis-cli --version
```

### Install Missing Software

#### macOS (using Homebrew)

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Install Python 3.11
brew install python@3.11

# Install PostgreSQL (optional)
brew install postgresql@15

# Install Redis (optional)
brew install redis

# Install Git
brew install git
```

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install Git
sudo apt install git
```

#### Windows

1. **Docker Desktop**: Download from https://www.docker.com/products/docker-desktop
2. **Python 3.11**: Download from https://www.python.org/downloads/
3. **Git**: Download from https://git-scm.com/download/win

---

## 2. Environment Setup

### Step 1: Clone the Repository

```bash
# Navigate to your projects folder
cd ~/Desktop

# Clone the repository
git clone https://github.com/your-org/care-ai.git
cd care-ai/care_ai_engine

# Verify you're in the right place
ls -la  # Should see app/, tests/, docker-compose.yml, etc.
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Verify activation (should show (venv) in prompt)
which python  # Should point to venv/bin/python
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt

# Verify installation
pip list | grep fastapi  # Should show fastapi
pip list | grep sqlalchemy  # Should show sqlalchemy
```

### Step 4: Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit the file
nano .env  # or use VS Code, vim, etc.
```

**Important: Update these values in `.env`:**

```bash
# === DATABASE ===
DATABASE_URL=postgresql+asyncpg://careai:careai_secret@localhost:5432/careai
TEST_DATABASE_URL=postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test

# === REDIS ===
REDIS_URL=redis://localhost:6379/0

# === JWT SECRET ===
# Generate a random secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
# Copy the output and paste it in .env

# === OLLAMA ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# === ENVIRONMENT ===
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# === CORS (for frontend development) ===
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8000

# === API ===
API_HOST=0.0.0.0
API_PORT=8000
```

**Generate a secure SECRET_KEY:**

```bash
# Run this command and copy the output
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Paste it into .env as SECRET_KEY=<output>
```

---

## 3. Database Setup

### Option A: Using Docker (Recommended)

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Wait a few seconds for startup
sleep 5

# Verify it's running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U careai -d careai -c "SELECT 1;"
```

### Option B: Using Local PostgreSQL

```bash
# Start PostgreSQL service
# macOS:
brew services start postgresql@15

# Linux:
sudo systemctl start postgresql

# Create database user
sudo -u postgres psql
postgres=# CREATE USER careai WITH PASSWORD 'careai_secret';
postgres=# ALTER USER careai CREATEDB;
postgres=# \q

# Create databases
createdb -U careai careai
createdb -U careai careai_test

# Test connection
psql -U careai -d careai -c "SELECT 1;"
```

### Run Database Migrations

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run migrations
./scripts/fix_database.sh

# Or manually:
alembic upgrade head

# Verify migration worked
alembic current
# Should show: 001_initial_schema (head)
```

**If migration fails:**

```bash
# Check current state
alembic current

# Check database exists
psql -U careai -l | grep careai

# Try manual migration
alembic upgrade head --sql > migration.sql  # Review SQL
psql -U careai -d careai -f migration.sql   # Apply manually
```

---

## 4. Redis Setup

### Option A: Using Docker (Recommended)

```bash
# Start Redis with Docker
docker-compose up -d redis

# Verify it's running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Option B: Using Local Redis

```bash
# Start Redis service
# macOS:
brew services start redis

# Linux:
sudo systemctl start redis

# Test connection
redis-cli ping
# Should return: PONG

# Test set/get
redis-cli set test "Hello"
redis-cli get test
# Should return: "Hello"
```

---

## 5. Ollama Setup

### Option A: Using Docker (Recommended)

```bash
# Start Ollama with Docker
docker-compose up -d ollama

# Wait for startup
sleep 10

# Pull the LLM model (this takes 5-10 minutes)
docker-compose exec ollama ollama pull llama3.2:3b

# Verify model is downloaded
docker-compose exec ollama ollama list
# Should show: llama3.2:3b

# Test Ollama
docker-compose exec ollama ollama run llama3.2:3b "Say hello"
# Should generate a response
```

### Option B: Using Local Ollama

```bash
# Install Ollama
# macOS:
brew install ollama

# Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# Windows:
# Download from https://ollama.ai/download

# Start Ollama service
ollama serve &

# Pull model
ollama pull llama3.2:3b

# Test
ollama run llama3.2:3b "Say hello"
```

**Model Options:**

```bash
# Small & Fast (good for testing)
ollama pull llama3.2:1b

# Balanced (recommended)
ollama pull llama3.2:3b

# Large & Accurate (requires more RAM)
ollama pull llama3.1:8b
```

---

## 6. Application Setup

### Start the Application

#### Option A: Using Docker Compose (Full Stack)

```bash
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f careai-api

# Stop viewing logs: Ctrl+C
```

#### Option B: Run Locally (Python)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Application should start and show:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

### Verify Application is Running

```bash
# Open another terminal and test

# Ping endpoint
curl http://localhost:8000/ping
# Should return: {"status":"ok"}

# Health check
curl http://localhost:8000/health
# Should return detailed health status
```

---

## 7. Testing Everything

### Step 1: Health Check

```bash
# Comprehensive health check
curl http://localhost:8000/health | python3 -m json.tool

# Expected output:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ollama": "running",
    "mcp_nhs": "available"
  },
  "timestamp": "2026-02-12T10:30:00Z"
}
```

### Step 2: Register a Test User

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User",
    "organisation": "Test Org",
    "role": "Developer"
  }'

# Expected: 201 Created
# Response will include user details
```

### Step 3: Login

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "Test123!"
  }'

# Copy the access_token from response
# Should look like: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 4: Test MCP Tools

```bash
# List available MCP tools
curl http://localhost:8000/api/agent/mcp/tools \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Expected: List of 4 NHS MCP tools
```

### Step 5: Ask a Medical Question

```bash
# Ask about a medicine
curl -X POST http://localhost:8000/api/agent/ask \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is paracetamol used for?"
  }'

# This will:
# 1. Fetch live data from NHS.uk (via MCP)
# 2. Send to Ollama LLM
# 3. Return answer with sources

# First request takes ~2-3 seconds (fetching + LLM)
# Subsequent requests are faster (cached)
```

### Step 6: Direct MCP Tool Call

```bash
# Call MCP tool directly (no LLM)
curl -X POST http://localhost:8000/api/agent/mcp/call \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "search_nhs",
    "arguments": {
      "query": "diabetes"
    }
  }'

# Returns raw NHS data (no LLM processing)
```

### Step 7: Run Automated Tests

```bash
# Setup test database (if not done)
./scripts/manage_db.sh test-db

# Run all tests
pytest

# Run with verbose output
pytest -vv

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

---

## 8. Common Errors & Fixes

### Error 1: "Cannot connect to database"

```bash
# Check database is running
docker-compose ps postgres
# or
pg_isready -U careai

# Check DATABASE_URL in .env is correct
cat .env | grep DATABASE_URL

# Test connection manually
psql -U careai -d careai -c "SELECT 1;"

# If using Docker, restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

**Fix:**
```bash
# Make sure database exists
createdb -U careai careai

# Run migrations again
alembic upgrade head
```

---

### Error 2: "Cannot connect to Redis"

```bash
# Check Redis is running
redis-cli ping
# or
docker-compose ps redis

# Check REDIS_URL in .env
cat .env | grep REDIS_URL

# If using Docker, restart Redis
docker-compose restart redis

# Check logs
docker-compose logs redis
```

**Fix:**
```bash
# Start Redis
brew services start redis
# or
docker-compose up -d redis
```

---

### Error 3: "Ollama not found" or "Model not available"

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If using Docker
docker-compose ps ollama
docker-compose logs ollama

# Check if model is downloaded
ollama list
# or
docker-compose exec ollama ollama list
```

**Fix:**
```bash
# Pull the model
ollama pull llama3.2:3b
# or
docker-compose exec ollama ollama pull llama3.2:3b

# Update .env if needed
OLLAMA_MODEL=llama3.2:3b
```

---

### Error 4: "Column users.is_admin does not exist"

```bash
# This means migrations haven't been run

# Check current migration status
alembic current

# Run migrations
./scripts/fix_database.sh

# Or manually
alembic upgrade head

# Verify
alembic current
# Should show: 001_initial_schema (head)
```

**If migration fails:**
```bash
# Check what tables exist
psql -U careai -d careai -c "\dt"

# Check users table structure
psql -U careai -d careai -c "\d users"

# If is_admin column is missing, add it manually
psql -U careai -d careai -c "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;"
```

---

### Error 5: "Port 8000 already in use"

```bash
# Find what's using the port
lsof -i :8000
# or
netstat -tuln | grep 8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001

# Update CORS_ORIGINS in .env to match
```

---

### Error 6: "Import errors" or "Module not found"

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Set Python path
export PYTHONPATH=$PWD

# If using VS Code, select the correct interpreter
# Cmd+Shift+P → "Python: Select Interpreter" → Choose venv

# Verify imports work
python3 -c "from app.main import app; print('OK')"
```

---

### Error 7: "NHS MCP tools not working"

```bash
# Check NHS website is accessible
curl -I https://www.nhs.uk
# Should return: HTTP/2 200

# Check MCP server is loaded
curl http://localhost:8000/api/agent/mcp/tools

# Test direct NHS access
curl https://www.nhs.uk/medicines/paracetamol/

# Check application logs
docker-compose logs careai-api | grep MCP
# or
tail -f logs/app.log | grep MCP
```

**Fix:**
```bash
# Restart application
docker-compose restart careai-api
# or
# Stop and start uvicorn

# Clear Redis cache
redis-cli FLUSHDB

# Test again
```

---

### Error 8: "Tests failing"

```bash
# Check test database exists
psql -U careai -l | grep careai_test

# Recreate test database
./scripts/manage_db.sh test-db

# Run specific failing test with verbose output
pytest tests/unit/test_auth_service.py::TestAuthService::test_register_user_success -vv

# Check test database connection
DATABASE_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test" \
  python3 -c "from app.core.database import engine; import asyncio; asyncio.run(engine.connect())"
```

---

### Error 9: "JWT token invalid"

```bash
# Check SECRET_KEY in .env is set
cat .env | grep SECRET_KEY

# Generate new SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
SECRET_KEY=<new_key>

# Restart application
docker-compose restart careai-api
```

---

### Error 10: "CORS errors" in browser

```bash
# Check CORS_ORIGINS in .env includes your frontend URL
cat .env | grep CORS_ORIGINS

# Update .env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8000

# Restart application
docker-compose restart careai-api
```

---

## 9. Development Workflow

### Daily Workflow

```bash
# 1. Start your day
cd care-ai/care_ai_engine
source venv/bin/activate

# 2. Pull latest changes
git pull origin main

# 3. Start services
docker-compose up -d

# 4. Run tests to make sure everything works
pytest

# 5. Start development
uvicorn app.main:app --reload

# 6. Make changes, tests auto-reload

# 7. Before committing
pytest
alembic current  # Make sure migrations are up to date

# 8. Commit and push
git add .
git commit -m "Your changes"
git push
```

### Making Database Changes

```bash
# 1. Update model
# Edit app/models/database.py

# 2. Create migration
alembic revision --autogenerate -m "description of change"

# 3. Review migration file
cat alembic/versions/<new_migration_file>.py

# 4. Test migration
alembic upgrade head

# 5. Test downgrade
alembic downgrade -1

# 6. Test upgrade again
alembic upgrade head

# 7. Run tests
pytest

# 8. Commit migration
git add alembic/versions/<new_migration_file>.py
git commit -m "Add migration: description"
```

### Adding New Features

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Write failing test first
# Edit tests/unit/test_my_feature.py

# 3. Run test (should fail)
pytest tests/unit/test_my_feature.py

# 4. Implement feature
# Edit app/services/my_service.py

# 5. Run test (should pass)
pytest tests/unit/test_my_feature.py

# 6. Run all tests
pytest

# 7. Check coverage
pytest --cov=app

# 8. Commit and push
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

---

## 🎯 Quick Verification Checklist

After setup, verify everything works:

- [ ] Database: `psql -U careai -d careai -c "SELECT 1;"`
- [ ] Redis: `redis-cli ping`
- [ ] Ollama: `ollama list`
- [ ] Migrations: `alembic current`
- [ ] API: `curl http://localhost:8000/health`
- [ ] Registration: Register a test user
- [ ] Login: Login with test user
- [ ] MCP Tools: `curl http://localhost:8000/api/agent/mcp/tools`
- [ ] Ask Question: Ask about a medicine
- [ ] Tests: `pytest`

**All green? You're ready to develop!** 🚀

---

## 📚 Next Steps

1. Read [TESTING.md](TESTING.md) for testing guide
2. Read [DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md) for migration guide
3. Read [README.md](README.md) for API documentation
4. Start building features!

---

## 🆘 Still Having Issues?

1. **Check logs:**
   ```bash
   docker-compose logs -f
   # or
   tail -f logs/app.log
   ```

2. **Verify environment:**
   ```bash
   cat .env | grep -v "^#" | grep -v "^$"
   ```

3. **Check service status:**
   ```bash
   docker-compose ps
   ```

4. **Full restart:**
   ```bash
   docker-compose down
   docker-compose up -d
   ./scripts/fix_database.sh
   ```

5. **Nuclear option (fresh start):**
   ```bash
   docker-compose down -v  # Removes volumes
   docker-compose up -d
   ./scripts/fix_database.sh
   pytest
   ```

Good luck! 🍀
