# 🚀 Production Deployment Guide

**Deploy Care AI to your production server**

---

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose installed
- Domain name pointing to server (optional)
- GitHub account with Container Registry access

---

## 🔐 STEP 1: Push Images to GitHub Registry

**On your local machine** (after testing locally):

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai

# Login to GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Tag images
docker tag care-ai-api ghcr.io/YOUR_USERNAME/careai-api:latest
docker tag care-ai-frontend ghcr.io/YOUR_USERNAME/careai-frontend:latest

# Push images
docker push ghcr.io/YOUR_USERNAME/careai-api:latest
docker push ghcr.io/YOUR_USERNAME/careai-frontend:latest
```

---

## 🖥️ STEP 2: Setup Production Server

**SSH to your server:**

```bash
ssh root@your-server-ip
```

**Install Docker (if not installed):**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

---

## 📦 STEP 3: Copy Files to Server

**On your local machine:**

```bash
# Copy docker-compose and env files
scp docker-compose.yml root@your-server-ip:/root/
scp deploy/.env root@your-server-ip:/root/

# Or clone from git
ssh root@your-server-ip
git clone https://github.com/YOUR_USERNAME/care-ai.git
cd care-ai
```

---

## ⚙️ STEP 4: Configure Environment

**On server:**

```bash
cd /root/care-ai

# Edit environment variables
nano .env
```

**Important variables:**

```bash
# Update with your values
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-generate-random-string
GITHUB_USER=your-github-username
OLLAMA_MODEL=llama3.2:3b

# Keep these as is
DATABASE_URL=postgresql+asyncpg://careai:${POSTGRES_PASSWORD}@postgres:5432/careai
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://ollama:11434
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🚀 STEP 5: Deploy

```bash
cd /root/care-ai

# Login to GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull images
docker-compose pull

# Start services
docker-compose up -d

# Wait for services
sleep 30

# Check status
docker-compose ps
```

---

## 🗄️ STEP 6: Initialize Database

```bash
# Run migrations
docker exec careai-api alembic upgrade head

# Verify
docker exec careai-api alembic current
```

**Expected:** `001_initial_schema (head)`

---

## ✅ STEP 7: Test Deployment

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy",...}

# Test frontend
curl http://localhost

# Register a test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "password": "SecurePassword123!",
    "full_name": "Admin User"
  }'
```

---

## 🔒 STEP 8: Setup SSL (Optional but Recommended)

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be in: /etc/letsencrypt/live/yourdomain.com/

# Update docker-compose.yml to mount SSL certificates
# See deploy/nginx-ssl.conf for configuration
```

---

## 🔄 Update Deployment (Push New Version)

**On local machine:**

```bash
# After making changes and testing locally

# Build and push new images
docker-compose -f docker-compose.local.yml build
docker tag care-ai-api ghcr.io/YOUR_USERNAME/careai-api:latest
docker tag care-ai-frontend ghcr.io/YOUR_USERNAME/careai-frontend:latest
docker push ghcr.io/YOUR_USERNAME/careai-api:latest
docker push ghcr.io/YOUR_USERNAME/careai-frontend:latest
```

**On server:**

```bash
cd /root/care-ai

# Pull new images
docker-compose pull

# Restart services
docker-compose up -d

# Run any new migrations
docker exec careai-api alembic upgrade head

# Check health
curl http://localhost:8000/health
```

---

## 📊 Monitoring

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f frontend

# Check resource usage
docker stats

# Check disk space
df -h
docker system df
```

---

## 🧹 Maintenance

```bash
# Backup database
docker exec careai-postgres pg_dump -U careai careai > backup_$(date +%Y%m%d).sql

# Clean old images
docker image prune -a

# Clean old volumes
docker volume prune

# View all containers
docker ps -a
```

---

## 🐛 Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs service-name

# Restart service
docker-compose restart service-name

# Rebuild and restart
docker-compose up -d --build service-name
```

### Database connection error

```bash
# Check postgres is running
docker-compose ps postgres

# Check database exists
docker exec careai-postgres psql -U careai -l

# Restart postgres
docker-compose restart postgres
```

### Out of disk space

```bash
# Check space
df -h

# Clean Docker
docker system prune -af --volumes
```

---

## 📋 Production Checklist

Before going live:

- [ ] SSL certificates installed
- [ ] Environment variables set
- [ ] Database backed up
- [ ] Health check returns "healthy"
- [ ] Can register users
- [ ] Can login
- [ ] Can ask questions
- [ ] Frontend loads
- [ ] Monitoring setup
- [ ] Backup strategy in place

---

## 🎯 Quick Reference

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart api

# Update deployment
docker-compose pull && docker-compose up -d

# Backup database
docker exec careai-postgres pg_dump -U careai careai > backup.sql

# Restore database
docker exec -i careai-postgres psql -U careai careai < backup.sql
```

---

## 📞 Support

- Check logs: `docker-compose logs -f`
- Health check: `curl http://localhost:8000/health`
- Database status: `docker exec careai-api alembic current`

---

**Your production deployment is ready!** 🎉
