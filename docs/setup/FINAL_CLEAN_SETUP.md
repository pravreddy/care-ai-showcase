# 🎯 FINAL SETUP - Clean Start

**Simple instructions that work for local AND production**

---

## 🧹 STEP 1: Clean Everything

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai

# Stop and remove everything (containers, volumes, networks)
docker-compose -f docker-compose.local.yml down -v

# Remove old images (optional but recommended)
docker rmi care-ai-api care-ai-frontend 2>/dev/null || true

# Verify everything is gone
docker ps -a | grep careai
docker volume ls | grep care-ai
```

**Expected:** No containers or volumes should show

---

## 🚀 STEP 2: Start Fresh

```bash
# Pull Ollama model first (only needed once)
docker-compose -f docker-compose.local.yml up -d ollama
sleep 10
docker exec careai-ollama-local ollama pull llama3.2:3b

# Build everything
docker-compose -f docker-compose.local.yml build

# Start everything
docker-compose -f docker-compose.local.yml up -d

# Wait for services
sleep 20
```

---

## 🗄️ STEP 3: Setup Database

```bash
# Run migrations
docker exec careai-api-local alembic upgrade head

# Verify
docker exec careai-api-local alembic current
```

**Expected output:** `001_initial_schema (head)`

---

## ✅ STEP 4: Test Everything

```bash
# Check all services are up
docker-compose -f docker-compose.local.yml ps

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost

# Open in browser
open http://localhost
open http://localhost:8000/docs
```

---

## 🎉 DONE!

Your system is now running:
- **Frontend**: http://localhost
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📝 One-Line Complete Setup

Copy this entire command:

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai && \
docker-compose -f docker-compose.local.yml down -v && \
docker-compose -f docker-compose.local.yml up -d ollama && \
sleep 10 && \
docker exec careai-ollama-local ollama pull llama3.2:3b && \
docker-compose -f docker-compose.local.yml build && \
docker-compose -f docker-compose.local.yml up -d && \
sleep 20 && \
docker exec careai-api-local alembic upgrade head && \
echo "✅ Setup complete!" && \
curl http://localhost:8000/health
```

---

## 🚀 Production Setup (Same Process!)

On your production server:

```bash
cd /root/care-ai

# Clean
docker-compose down -v

# Start (pulls pre-built images from GitHub)
docker-compose up -d

# Wait
sleep 20

# Setup database
docker exec careai-api alembic upgrade head

# Test
curl http://localhost:8000/health
```

**That's it!** Same process, just different docker-compose file.

---

## 🔄 Daily Usage

```bash
# Start
docker-compose -f docker-compose.local.yml up -d

# Stop
docker-compose -f docker-compose.local.yml down

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Restart specific service
docker-compose -f docker-compose.local.yml restart api
```

---

## 🐛 If Something Goes Wrong

```bash
# Nuclear reset - start completely fresh
docker-compose -f docker-compose.local.yml down -v
docker system prune -af --volumes
# Then run the one-line setup again
```

---

**Simple and clean!** 🎉
