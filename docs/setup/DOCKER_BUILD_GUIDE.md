# 🚀 Docker Build & Run Guide

**Complete step-by-step guide to build and run Care AI with Docker**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development (Build from Source)](#local-development-build-from-source)
3. [Production Server (Pull from Registry)](#production-server-pull-from-registry)
4. [Common Issues](#common-issues)

---

## Prerequisites

### Required Software

- **Docker** (version 20+)
- **Docker Compose** (version 2+)

### Check Your Installation

```bash
docker --version
# Should show: Docker version 20.x.x or higher

docker-compose --version
# Should show: Docker Compose version 2.x.x or higher
```

### Install Docker (if needed)

**macOS:**
```bash
brew install --cask docker
# Or download Docker Desktop from https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and log back in
```

---

## Local Development (Build from Source)

This builds everything from your local code - perfect for development and testing.

### Step 1: Navigate to Project

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai
```

### Step 2: Verify Files Exist

```bash
ls -la
# You should see:
# care_ai_frontend/
# care_ai_engine/
# docker-compose.local.yml
```

### Step 3: Check Dockerfiles Exist

```bash
# Check backend Dockerfile
ls -la care_ai_engine/Dockerfile
# Should exist

# Check frontend Dockerfile
ls -la care_ai_frontend/Dockerfile
# Should exist

# Check nginx config
ls -la care_ai_frontend/nginx/default.conf
# Should exist
```

### Step 4: Set Environment Variable (Optional)

```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output

# Export it (or just use default for testing)
export SECRET_KEY="your-generated-key-here"
```

### Step 5: Pull LLM Model FIRST (Important!)

```bash
# Start only Ollama first to download the model
docker-compose -f docker-compose.local.yml up -d ollama

# Wait for Ollama to be ready
sleep 10

# Pull the model (this takes 5-10 minutes)
docker exec careai-ollama-local ollama pull llama3.2:3b

# Check it downloaded
docker exec careai-ollama-local ollama list
# Should show: llama3.2:3b
```

### Step 6: Build Everything

```bash
# Build all services (this takes 5-10 minutes)
docker-compose -f docker-compose.local.yml build

# You'll see:
# Building api...
# Building frontend...
```

**What this does:**
- ✅ Builds backend Docker image (installs Python packages)
- ✅ Builds frontend Docker image (npm install + npm build)
- ✅ Creates optimized production images

### Step 7: Start All Services

```bash
# Start everything
docker-compose -f docker-compose.local.yml up -d

# Check status
docker-compose -f docker-compose.local.yml ps
```

**Expected output:**
```
NAME                      STATUS
careai-postgres-local     Up (healthy)
careai-redis-local        Up (healthy)
careai-ollama-local       Up
careai-api-local          Up (healthy)
careai-frontend-local     Up (healthy)
```

### Step 8: Run Database Migrations

```bash
# Run migrations
docker exec careai-api-local alembic upgrade head

# Verify migration worked
docker exec careai-api-local alembic current
# Should show: 001_initial_schema (head)
```

### Step 9: Test Everything

```bash
# Test backend
curl http://localhost:8000/health
# Should return JSON

# Test frontend (open in browser)
open http://localhost
# or
curl http://localhost
# Should return HTML
```

### Step 10: View Logs

```bash
# View all logs
docker-compose -f docker-compose.local.yml logs -f

# View specific service
docker-compose -f docker-compose.local.yml logs -f api
docker-compose -f docker-compose.local.yml logs -f frontend
```

---

## Production Server (Pull from Registry)

This pulls pre-built images from GitHub Container Registry - used for production.

### Step 1: Login to GitHub Container Registry

```bash
# Create a Personal Access Token (PAT) on GitHub
# Go to: Settings → Developer settings → Personal access tokens
# Generate token with 'read:packages' permission

# Login
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### Step 2: Copy Files to Server

```bash
# On your local machine, copy to server
scp docker-compose.yml deploy/.env root@your-server-ip:/root/care-ai/
```

### Step 3: On Server, Start Services

```bash
# SSH to server
ssh root@your-server-ip

# Navigate to directory
cd /root/care-ai

# Edit .env with your settings
nano .env

# Pull images
docker-compose pull

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

---

## Complete Command Reference

### Building

```bash
# Build all services
docker-compose -f docker-compose.local.yml build

# Build specific service
docker-compose -f docker-compose.local.yml build api
docker-compose -f docker-compose.local.yml build frontend

# Build with no cache (fresh build)
docker-compose -f docker-compose.local.yml build --no-cache

# Build and start
docker-compose -f docker-compose.local.yml up -d --build
```

### Starting/Stopping

```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Stop all services
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (fresh start)
docker-compose -f docker-compose.local.yml down -v

# Restart all services
docker-compose -f docker-compose.local.yml restart

# Restart specific service
docker-compose -f docker-compose.local.yml restart api
```

### Viewing Logs

```bash
# All logs
docker-compose -f docker-compose.local.yml logs

# Follow logs (live)
docker-compose -f docker-compose.local.yml logs -f

# Specific service logs
docker-compose -f docker-compose.local.yml logs -f api
docker-compose -f docker-compose.local.yml logs -f frontend
docker-compose -f docker-compose.local.yml logs -f postgres

# Last 100 lines
docker-compose -f docker-compose.local.yml logs --tail=100 api
```

### Executing Commands

```bash
# Run command in container
docker exec careai-api-local <command>

# Examples:
docker exec careai-api-local alembic upgrade head
docker exec careai-api-local alembic current
docker exec careai-api-local pytest
docker exec careai-postgres-local psql -U careai -d careai -c "SELECT 1;"
docker exec careai-redis-local redis-cli ping
docker exec careai-ollama-local ollama list
```

### Database Management

```bash
# Connect to database
docker exec -it careai-postgres-local psql -U careai -d careai

# Run migrations
docker exec careai-api-local alembic upgrade head

# Check migration status
docker exec careai-api-local alembic current

# Create migration
docker exec careai-api-local alembic revision --autogenerate -m "description"

# Rollback migration
docker exec careai-api-local alembic downgrade -1
```

### Cleanup

```bash
# Stop and remove containers
docker-compose -f docker-compose.local.yml down

# Stop and remove containers + volumes
docker-compose -f docker-compose.local.yml down -v

# Remove images
docker rmi careai-api-local careai-frontend-local

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune
```

---

## Common Issues

### Issue 1: Build Fails - "npm install" Error

**Error:**
```
npm ERR! network
```

**Fix:**
```bash
# Check your internet connection
ping google.com

# Try building with more memory
docker-compose -f docker-compose.local.yml build --memory 4g

# Or clear Docker cache
docker builder prune
docker-compose -f docker-compose.local.yml build --no-cache
```

### Issue 2: Build Fails - "pip install" Error

**Error:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Fix:**
```bash
# Check requirements.txt exists
cat care_ai_engine/requirements.txt

# Try building with more memory
docker-compose -f docker-compose.local.yml build --memory 4g

# Or build manually
cd care_ai_engine
docker build -t careai-api-local .
```

### Issue 3: Port Already in Use

**Error:**
```
Error: port is already allocated
```

**Fix:**
```bash
# Find what's using the port
lsof -i :80
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.local.yml
```

### Issue 4: Database Connection Error

**Error:**
```
could not connect to database
```

**Fix:**
```bash
# Check postgres is running
docker-compose -f docker-compose.local.yml ps postgres

# Check postgres logs
docker-compose -f docker-compose.local.yml logs postgres

# Restart postgres
docker-compose -f docker-compose.local.yml restart postgres

# Or start fresh
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d
```

### Issue 5: Ollama Model Not Downloaded

**Error:**
```
model not found
```

**Fix:**
```bash
# Pull model manually
docker exec careai-ollama-local ollama pull llama3.2:3b

# Check model exists
docker exec careai-ollama-local ollama list

# Test model
docker exec careai-ollama-local ollama run llama3.2:3b "Say hello"
```

### Issue 6: Frontend Shows "Cannot connect to backend"

**Error:**
Browser console shows network errors

**Fix:**
```bash
# Check API is running
curl http://localhost:8000/health

# Check nginx config
docker exec careai-frontend-local cat /etc/nginx/conf.d/default.conf

# Check API logs
docker-compose -f docker-compose.local.yml logs api

# Restart frontend
docker-compose -f docker-compose.local.yml restart frontend
```

### Issue 7: "Out of disk space"

**Error:**
```
no space left on device
```

**Fix:**
```bash
# Check disk space
df -h

# Remove unused Docker resources
docker system prune -a
docker volume prune

# If still not enough, remove specific volumes
docker-compose -f docker-compose.local.yml down -v
```

---

## Testing After Build

### Step 1: Health Check

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

**Expected:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ollama": "running",
    "mcp_nhs": "available"
  }
}
```

### Step 2: Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

### Step 3: Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "Test123!"
  }'
```

### Step 4: Ask Question

```bash
# Use token from login response
curl -X POST http://localhost:8000/api/agent/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is paracetamol used for?"
  }'
```

---

## Production Deployment Checklist

Before deploying to production server:

- [ ] Built and tested locally with `docker-compose.local.yml`
- [ ] All services start successfully
- [ ] Database migrations run without errors
- [ ] Health check returns "healthy"
- [ ] Can register and login users
- [ ] Can ask questions and get responses
- [ ] Frontend loads correctly
- [ ] No errors in logs
- [ ] Ollama model downloaded

---

## Quick Reference

```bash
# BUILD everything
docker-compose -f docker-compose.local.yml build

# START everything
docker-compose -f docker-compose.local.yml up -d

# CHECK status
docker-compose -f docker-compose.local.yml ps

# VIEW logs
docker-compose -f docker-compose.local.yml logs -f

# RUN migrations
docker exec careai-api-local alembic upgrade head

# STOP everything
docker-compose -f docker-compose.local.yml down

# FRESH START
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml build --no-cache
docker-compose -f docker-compose.local.yml up -d
```

---

## Next Steps

1. ✅ Build locally: `docker-compose -f docker-compose.local.yml build`
2. ✅ Test locally: `docker-compose -f docker-compose.local.yml up -d`
3. ✅ Fix any errors
4. ✅ Push images to registry (optional)
5. ✅ Deploy to production server

---

**Need help?** Check the error messages in logs:
```bash
docker-compose -f docker-compose.local.yml logs -f
```
