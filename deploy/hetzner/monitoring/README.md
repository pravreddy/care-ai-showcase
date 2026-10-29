# Monitoring & recovery — Hetzner box

Two layers, both deployed by `./deploy-monitoring.sh`:

1. **Uptime Kuma** — tells you *the moment* something is down (site, cert, container, mail port).
2. **autoheal** — automatically restarts any container that goes `unhealthy`.

Plus the resilience fixes already made in `docker-compose.yml`:
- `postgres` and `redis` now have `restart: always` (the exact gap that kept them down).

## 1. Deploy
From your Mac:
```bash
chmod +x deploy-monitoring.sh
./deploy-monitoring.sh
```
Open the dashboard over an SSH tunnel (it's bound to localhost, never public):
```bash
ssh -L 3001:localhost:3001 hetzner-prod
# then open http://localhost:3001  and create your admin account
```

## 2. Add these monitors in Uptime Kuma
Click **+ Add New Monitor** for each. These are chosen to catch *exactly* the failures we just hit.

**Websites (HTTP-s, every 60s)** — catches "site down" and **certificate problems** (Kuma flags an invalid cert and warns before expiry):
- `https://guhya.co.in`        (Type: HTTP(s), accepted codes 200-299, "Ignore TLS" OFF)
- `https://careaisoftware.co.uk`
- `https://signsimple.co.uk`

For each website monitor, scroll to **"Certificate Expiry"** and enable the notification — this alone would have warned you about the guhya cert mismatch.

**Keyword check (catches "serving the wrong site")** — add an HTTP monitor with **Keyword** type:
- `https://guhya.co.in` contains `GUHYA`  → if guhya ever falls through to SignSimple again, this fires.

**Containers (Docker, every 30s)** — under monitor Type choose **Docker Container** (add your Docker host = `unix:///var/run/docker.sock`):
- `careai-postgres`, `careai-redis`  ← the two that went down
- `careai-nginx`
- `careai-api-blue` / `careai-api-green` (whichever is active)
- `docsign-api-blue`

**Mail ports (TCP Port)** — only if you keep running Mailcow:
- host `88.99.167.49`, ports `25`, `465`, `587`, `993`

## 3. Wire up alerts (do this once)
**Settings → Notifications → Setup Notification**, then attach it to every monitor.
Pick whichever you'll actually see:
- **Telegram** (easiest, free, instant): create a bot via @BotFather, paste the token + your chat id. Recommended.
- **Email (SMTP)**: now that you have Mailcow, you can point it at your own mail server, or use Gmail SMTP. Good as a second channel.
- Slack / Discord / Gotify also supported if you prefer.

Tip: set "Resend notification every X minutes if still down" so a problem doesn't get forgotten.

## 4. Recovery
- **autoheal** restarts unhealthy containers automatically within ~30s.
- **restart: always** on postgres/redis means they come back after any stop or reboot.
- **One-command full bring-up** (if you ever need to start everything by hand):
  ```bash
  cd ~/careai
  docker compose -f docker-compose.yml -f docker-compose.docsign.yml up -d
  ```
- **Reboot test**: once a quarter, `sudo reboot` the box and confirm every site + login comes back on its own. Better to find a gap during a planned test than at 2am.

## 5. Still to add (ask and I'll build)
- **Nightly Postgres backup** (pg_dump → `/mnt/nvme_data/backups` + optional off-box copy). This is the backup you wished you'd had — strongly recommended next.
- **Mailcow backup** (it has its own `helper-scripts/backup_and_restore.sh`).
