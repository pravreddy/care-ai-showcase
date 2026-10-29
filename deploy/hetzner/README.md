# Hetzner Deployment — Avyangah Technologies

All services on one Hetzner CPX32 (~€15/mo).
Each service can be split to its own server later by changing env vars.

## Architecture

```
Hetzner CPX32 (3 vCPU, 8GB RAM, 160GB NVMe)
├── Caddy (auto HTTPS, reverse proxy)
│   ├── signsimple.co.uk    → docsign-api + docsign-frontend
│   └── careaisoftware.co.uk → careai-api + careai-frontend
├── PostgreSQL (shared: careai DB + docsign_uk DB)
├── Redis (shared: cache + celery broker)
├── CareAI Engine (FastAPI + Groq LLM)
├── SignSimple (Django + Celery + React)
└── Postal (optional, when port 25 approved)
```

## Quick Start

```bash
# 1. Run server setup (once, as root)
ssh root@YOUR_IP
bash server-setup.sh

# 2. Copy files and configure (as deploy user)
ssh deploy@YOUR_IP
cd ~/avyangah
cp .env.template .env
nano .env  # fill in passwords, API keys, domains

# 3. Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin

# 4. Start everything
docker compose -f docker-compose.yml \
  -f docker-compose.careai.yml \
  -f docker-compose.docsign.yml \
  up -d
```

## Splitting Later

When traffic grows, split services to separate servers:

```bash
# Server 1 (apps): change DB_HOST and REDIS_HOST in .env to Server 2's IP
docker compose -f docker-compose.careai.yml -f docker-compose.docsign.yml up -d

# Server 2 (infra): just PostgreSQL + Redis
docker compose -f docker-compose.yml up -d

# Server 3 (postal): its own compose with its own MariaDB + RabbitMQ
docker compose -f docker-compose.postal.yml up -d

# Server 4 (India .in): same compose files, different .env
docker compose -f docker-compose.yml -f docker-compose.guhya.yml up -d
```

## Files

| File | Purpose |
|---|---|
| docker-compose.yml | Base: PostgreSQL + Redis + Caddy |
| docker-compose.careai.yml | Care AI: API (blue/green) + Frontend |
| docker-compose.docsign.yml | SignSimple: API (blue/green) + Celery + Frontend |
| docker-compose.postal.yml | Postal: MariaDB + RabbitMQ + Web + SMTP + Worker |
| Caddyfile | Reverse proxy + auto HTTPS (replaces nginx) |
| .env.template | All environment variables |
| init-db.sql | Creates app databases on first startup |
| server-setup.sh | Hetzner initial server setup |
| migrate-from-vultr.sh | Copy data from Vultr to Hetzner |
| deploy.sh | Blue/green deploy script |

## Migration Timeline

| Date | Action |
|---|---|
| 3-8 April | Prepare: test locally, build compose files |
| 9 April | Purchase Hetzner server, run server-setup.sh |
| 9-14 April | Test everything on Hetzner (access via IP) |
| 15 April 06:27 | Switch DNS, go live on Hetzner |
| 20 April | Close Vultr account (Akshaya Tritiya) |
