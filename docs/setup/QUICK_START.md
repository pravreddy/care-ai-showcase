# 🚀 Care AI - Quick Start Guide

**Get frontend and backend running in 5 minutes!**

---

## ⚡ One-Line Start

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai && \
cp care_ai_engine/.env.example care_ai_engine/.env && \
docker-compose -f docker-compose.dev.yml up -d && \
echo "✅ Starting... Wait 2 minutes for Ollama to download model" && \
echo "📱 Frontend: http://localhost:3000" && \
echo "🔧 Backend:  http://localhost:8000" && \
echo "📚 API Docs: http://localhost:8000/docs"
```

---

## 📋 Step-by-Step (Recommended)

### 1. Navigate to Project (10 seconds)

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai
```

### 2. Setup Environment (30 seconds)

```bash
# Copy environment file
cp care_ai_engine/.env.example care_ai_engine/.env

# Generate secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Copy the output and add it to care_ai_engine/.env
nano care_ai_engine/.env
# or
code care_ai_engine/.env  # if you use VS Code
```

**Minimal .env content:**

```bash
SECRET_KEY=paste-your-generated-key-here
DATABASE_URL=postgresql+asyncpg://careai:careai_secret@postgres:5432/careai
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. Start Everything (2 minutes)

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps
```

You should see:
```
NAME                    STATUS
careai-frontend-dev     Up
careai-api-dev          Up (healthy)
careai-postgres-dev     Up (healthy)
careai-redis-dev        Up (healthy)
careai-ollama-dev       Up
careai-ollama-init      Exited (0)  ← This downloads the model
```

### 4. Wait for Model Download (5-10 minutes first time)

```bash
# Watch Ollama download progress
docker-compose -f docker-compose.dev.yml logs -f ollama-init

# You'll see: "Pulling llama3.2:3b model..."
# When done: "Model ready!"
# Press Ctrl+C to stop watching
```

### 5. Run Database Migrations (10 seconds)

```bash
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
```

### 6. Test Everything (30 seconds)

```bash
# Backend health check
curl http://localhost:8000/health

# Should return JSON with "status": "healthy"
```

### 7. Open in Browser

```bash
# Frontend
open http://localhost:3000

# Or manually:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## ✅ Verification Checklist

Run these to make sure everything works:

```bash
# 1. Check all services are running
docker-compose -f docker-compose.dev.yml ps
# All should show "Up" or "Up (healthy)"

# 2. Test backend
curl http://localhost:8000/ping
# Should return: {"status":"ok"}

# 3. Test database
docker-compose -f docker-compose.dev.yml exec postgres \
  psql -U careai -d careai -c "SELECT 1;"
# Should return: 1

# 4. Test Redis
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
# Should return: PONG

# 5. Test Ollama
docker-compose -f docker-compose.dev.yml exec ollama ollama list
# Should show: llama3.2:3b

# 6. Test frontend (open in browser)
open http://localhost:3000
```

---

## 🎯 First Steps After Setup

### 1. Register a User

**Via Frontend:**
- Go to http://localhost:3000
- Click "Register" or "Try Free Trial"
- Fill in details
- Click "Register"

**Via API:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User",
    "organisation": "Test Org",
    "role": "Developer"
  }'
```

### 2. Login

**Via Frontend:**
- Go to http://localhost:3000/login
- Enter email and password
- Click "Login"

**Via API:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "Test123!"
  }'

# Save the access_token from response
```

### 3. Ask a Question

**Via Frontend:**
- After login, go to "Ask Agent" page
- Type: "What is paracetamol used for?"
- Click "Ask"
- Wait for AI response with NHS sources

**Via API:**
```bash
# Use the token from login
curl -X POST http://localhost:8000/api/agent/ask \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is paracetamol used for?"
  }'
```

---

## 🔧 Common Commands

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f api
docker-compose -f docker-compose.dev.yml logs -f frontend
docker-compose -f docker-compose.dev.yml logs -f postgres
```

### Restarting Services

```bash
# Restart all
docker-compose -f docker-compose.dev.yml restart

# Restart specific service
docker-compose -f docker-compose.dev.yml restart api
docker-compose -f docker-compose.dev.yml restart frontend
```

### Stopping Services

```bash
# Stop all (keeps data)
docker-compose -f docker-compose.dev.yml down

# Stop and remove data (fresh start)
docker-compose -f docker-compose.dev.yml down -v
```

### Running Tests

```bash
# Backend tests
docker-compose -f docker-compose.dev.yml exec api pytest

# With coverage
docker-compose -f docker-compose.dev.yml exec api \
  pytest --cov=app --cov-report=html
```

---

## 🐛 Troubleshooting

### "Port already in use"

```bash
# Find what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Kill the process
kill -9 <PID>
```

### "Cannot connect to database"

```bash
# Restart postgres
docker-compose -f docker-compose.dev.yml restart postgres

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres
```

### "Ollama not working"

```bash
# Check Ollama logs
docker-compose -f docker-compose.dev.yml logs ollama

# Pull model manually
docker-compose -f docker-compose.dev.yml exec ollama \
  ollama pull llama3.2:3b
```

### "Frontend not loading"

```bash
# Check frontend logs
docker-compose -f docker-compose.dev.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.dev.yml up -d --build frontend
```

### Fresh Start (Nuclear Option)

```bash
# Stop everything
docker-compose -f docker-compose.dev.yml down -v

# Remove images
docker rmi careai-frontend-dev careai-api-dev

# Start again
docker-compose -f docker-compose.dev.yml up -d

# Run migrations
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
```

---

## 📚 Next Steps

1. **Read the docs:**
   - Main: [README.md](README.md)
   - Backend: [care_ai_engine/README.md](care_ai_engine/README.md)
   - Frontend: [care_ai_frontend/README.md](care_ai_frontend/README.md)

2. **Explore features:**
   - Register and login
   - Ask medical questions
   - Try voice notes
   - Check API docs at http://localhost:8000/docs

3. **Start developing:**
   - Edit `care_ai_frontend/src/` for frontend changes
   - Edit `care_ai_engine/app/` for backend changes
   - Changes auto-reload!

---

## 🎓 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Your Browser                           │
│          http://localhost:3000                      │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│         Frontend Container                          │
│         (React + Vite)                              │
│         Port: 3000                                  │
└───────────────┬─────────────────────────────────────┘
                │ /api requests
                ▼
┌─────────────────────────────────────────────────────┐
│         Backend Container                           │
│         (FastAPI)                                   │
│         Port: 8000                                  │
└───┬─────┬─────┬──────────────────────────────────┬──┘
    │     │     │                                  │
    ▼     ▼     ▼                                  ▼
┌──────┐ ┌────┐ ┌─────────┐              ┌──────────────┐
│ DB   │ │Redis│ │ Ollama  │              │ NHS.uk       │
│Port  │ │6379 │ │ 11434   │              │ (Internet)   │
│5432  │ └────┘ └─────────┘              └──────────────┘
└──────┘   Cache   LLM Model               MCP Data Source
```

---

## 💡 Pro Tips

1. **Keep services running**: Once started, leave them running during development
2. **Watch logs**: Use `docker-compose logs -f api` to see what's happening
3. **Use API docs**: http://localhost:8000/docs is interactive
4. **Hot reload works**: Edit code and see changes instantly
5. **Test often**: Run `pytest` to catch issues early

---

**You're all set!** 🎉

**Access your app:**
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

**Need help?** Check [README.md](README.md) for detailed documentation.
