# 🚀 SIMPLE DOCKER COMMANDS - COPY & PASTE

**Just copy and paste these commands in order**

---

## 📍 Step 1: Navigate to Project

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai
```

---

## 🐳 Step 2: Download Ollama Model (IMPORTANT - Do This First!)

```bash
# Start only Ollama
docker-compose -f docker-compose.local.yml up -d ollama

# Wait 10 seconds
sleep 10

# Download model (takes 5-10 minutes)
docker exec careai-ollama-local ollama pull llama3.2:3b

# Verify it downloaded
docker exec careai-ollama-local ollama list
```

**You should see:** `llama3.2:3b`

---

## 🔨 Step 3: Build Everything (Takes 5-10 Minutes)

```bash
docker-compose -f docker-compose.local.yml build
```

**What happens:**
- Builds backend (installs Python packages)
- Builds frontend (runs npm install + npm build)
- Creates Docker images

---

## ▶️ Step 4: Start Everything

```bash
docker-compose -f docker-compose.local.yml up -d
```

---

## 🗄️ Step 5: Run Database Migrations

```bash
docker exec careai-api-local alembic upgrade head
```

---

## ✅ Step 6: Check Everything is Running

```bash
docker-compose -f docker-compose.local.yml ps
```

**You should see all services "Up (healthy)"**

---

## 🧪 Step 7: Test It Works

```bash
# Test backend
curl http://localhost:8000/health

# Test frontend (open in browser)
open http://localhost
```

---

## 📊 View Logs (If Something Goes Wrong)

```bash
# View all logs
docker-compose -f docker-compose.local.yml logs -f

# View only API logs
docker-compose -f docker-compose.local.yml logs -f api

# View only frontend logs
docker-compose -f docker-compose.local.yml logs -f frontend
```

Press `Ctrl+C` to stop viewing logs

---

## 🔄 Restart Everything

```bash
docker-compose -f docker-compose.local.yml restart
```

---

## 🛑 Stop Everything

```bash
docker-compose -f docker-compose.local.yml down
```

---

## 🧹 Fresh Start (If Things Break)

```bash
# Stop and remove everything
docker-compose -f docker-compose.local.yml down -v

# Rebuild from scratch
docker-compose -f docker-compose.local.yml build --no-cache

# Start again
docker-compose -f docker-compose.local.yml up -d

# Run migrations again
docker exec careai-api-local alembic upgrade head
```

---

## 🎯 Access Your App

- **Frontend**: http://localhost
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🚀 For Production Server

Once it works locally, use this on your server:

```bash
# Use the production docker-compose.yml
docker-compose pull
docker-compose up -d
```

---

## ❓ Common Errors

### "Port already in use"
```bash
# Find what's using the port
lsof -i :80
lsof -i :8000

# Kill it
kill -9 <PID>
```

### "Build failed"
```bash
# Clear Docker cache
docker builder prune

# Try again
docker-compose -f docker-compose.local.yml build --no-cache
```

### "Cannot connect to database"
```bash
# Restart postgres
docker-compose -f docker-compose.local.yml restart postgres

# Check logs
docker-compose -f docker-compose.local.yml logs postgres
```

---

## 📝 That's It!

**The complete workflow:**

1. Pull Ollama model
2. Build: `docker-compose -f docker-compose.local.yml build`
3. Start: `docker-compose -f docker-compose.local.yml up -d`
4. Migrate: `docker exec careai-api-local alembic upgrade head`
5. Test: Open http://localhost

**Need detailed help?** See [DOCKER_BUILD_GUIDE.md](DOCKER_BUILD_GUIDE.md)
