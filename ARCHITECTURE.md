# Avyangah Technologies — Server Architecture
#
# Hetzner Dedicated Server #2978507
# IP: 88.99.167.49 | Location: FSN1-DC1 (Falkenstein, Germany)
# Specs: Xeon E3-1275V6, 64GB RAM, 2x512GB NVMe
# Cost: €40.70/month
#
# ══════════════════════════════════════════════
# HOW EVERYTHING FITS TOGETHER
# ══════════════════════════════════════════════
#
# Internet
#     │
#     ├── Port 80/443 ──→ Nginx (Docker: careai-nginx)
#     │   ├── signsimple.co.uk     → nginx-docsign.conf → SignSimple (blue/green)
#     │   ├── careaisoftware.co.uk → nginx.conf          → CareAI (blue/green)
#     │   ├── guhya.co.in          → sites/*.conf        → Static site
#     │   └── mail.guhya.co.in     → nginx-mail.conf     → Mailcow (port 8080)
#     │
#     ├── Port 25/465/587 ──→ Mailcow (separate Docker Compose)
#     ├── Port 993 ──────────→ Mailcow IMAP
#     └── Port 4190 ─────────→ Mailcow Sieve
#
# ══════════════════════════════════════════════
# REPO STRUCTURE → SERVER MAPPING
# ══════════════════════════════════════════════
#
# REPO FILE                              → SERVER LOCATION
# ─────────────────────────────────────────────────────────
# docker-compose.yml                     → ~/careai/docker-compose.yml
# docker-compose.docsign.yml             → ~/careai/docker-compose.docsign.yml
# nginx.conf                             → ~/careai/nginx.conf
# nginx-docsign.conf                     → ~/careai/nginx-docsign.conf
# active_env.conf                        → ~/careai/active_env.conf
# active_docsign.conf                    → ~/careai/active_docsign.conf
# deploy/hetzner/mailcow/nginx-mail.conf → ~/careai/nginx-mail.conf  (via deploy-mailcow.sh)
# deploy/hetzner/mailcow/setup-mailcow.sh → /tmp/ then /opt/mailcow-dockerized/
#
# ══════════════════════════════════════════════
# DOCKER COMPOSE STACKS (independent)
# ══════════════════════════════════════════════
#
# Stack 1: Main Apps (~/careai/)
#   docker-compose.yml + docker-compose.docsign.yml
#   ├── careai-postgres (shared DB)
#   ├── careai-redis (shared cache)
#   ├── careai-nginx (shared reverse proxy, ports 80/443)
#   ├── careai-ollama
#   ├── careai-api-blue / green (CareAI backend)
#   ├── careai-frontend-blue / green (CareAI frontend)
#   ├── docsign-api-blue / green (SignSimple backend)
#   ├── docsign-frontend-blue / green (SignSimple frontend)
#   └── docsign-celery (SignSimple background jobs)
#
# Stack 2: Mailcow (/opt/mailcow-dockerized/)
#   Own docker-compose.yml (managed by Mailcow project)
#   ├── mailcow-nginx (port 8080, proxied by careai-nginx)
#   ├── mailcow-postfix (SMTP, port 25/465/587)
#   ├── mailcow-dovecot (IMAP, port 993)
#   ├── mailcow-rspamd (spam filter)
#   ├── mailcow-clamd (antivirus)
#   ├── mailcow-sogo (webmail)
#   ├── mailcow-mysql (MariaDB, separate from app PostgreSQL)
#   └── mailcow-redis (separate from app Redis)
#
# ══════════════════════════════════════════════
# ADDING A NEW APP / DOMAIN
# ══════════════════════════════════════════════
#
# 1. Create nginx config: nginx-<appname>.conf
#    - Add server blocks for HTTP (redirect) + HTTPS (proxy)
#    - Use existing SSL certs or add new ones
#
# 2. Update docker-compose.yml:
#    - Add volume mount under nginx service:
#      ./nginx-<appname>.conf:/etc/nginx/conf.d/<appname>.conf:ro
#    - Add app containers (api, frontend, etc.)
#
# 3. Add DNS:
#    - A record: newapp.co.uk → 88.99.167.49
#    - SSL: certbot or wildcard cert
#
# 4. Deploy:
#    - SCP configs to server
#    - docker compose up -d nginx  (reload nginx with new config)
#    - docker compose up -d <new-service>
#
# 5. IMPORTANT: Never edit files directly on server.
#    All configs live in this repo. Deploy via SCP or git pull.
#
# ══════════════════════════════════════════════
# ADDING EMAIL FOR A NEW DOMAIN
# ══════════════════════════════════════════════
#
# 1. Login: https://mail.guhya.co.in → Mailcow admin
# 2. Mail Setup → Domains → Add domain
# 3. Create mailboxes
# 4. Copy DKIM key from ARC/DKIM page
# 5. Add DNS records at registrar:
#    MX   @              → mail.guhya.co.in (priority 10)
#    TXT  @              → v=spf1 ip4:88.99.167.49 -all
#    TXT  _dmarc         → v=DMARC1; p=quarantine; rua=mailto:dmarc@domain.com
#    TXT  dkim._domainkey → (from Mailcow admin)
#
# No server changes needed. No nginx changes. Just DNS + Mailcow admin.
#
# ══════════════════════════════════════════════
# DEPLOY COMMANDS (from local machine)
# ══════════════════════════════════════════════
#
# SignSimple:  Automatic via GitHub Actions (push to main)
# CareAI:     Automatic via GitHub Actions (push to main)
# Mailcow:    ./deploy-mailcow.sh         (first time)
#             ./deploy-mailcow.sh update   (config changes only)
# New site:   scp nginx-<app>.conf hetzner-prod:~/careai/
#             ssh hetzner-prod "cd ~/careai && docker compose up -d nginx"
#
# ══════════════════════════════════════════════
# STORAGE
# ══════════════════════════════════════════════
#
# /mnt/nvme_data/              NVMe SSD (fast)
#   ├── postgres_data/         PostgreSQL databases
#   ├── redis_data/            Redis cache
#   ├── ssl/                   SSL certificates
#   └── docsign/
#       ├── media/             Uploaded PDFs, signed docs
#       └── static/            Django static files
#
# ~/careai/hdd_storage/        HDD (big, slow)
#   ├── ollama/                AI models (~5GB each)
#   ├── careai_logs/           Application logs
#   └── careai/                CareAI data
#
# /opt/mailcow-dockerized/     Mailcow (NVMe)
#   └── data/                  Mail storage, DB, certs
