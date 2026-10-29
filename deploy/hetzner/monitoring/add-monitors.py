#!/usr/bin/env python3
"""
Bulk-add Uptime Kuma monitors for all sites, mail ports, and containers.
So you never click "Add New Monitor" 15 times by hand.

HOW TO RUN (from your Mac):
  1) Open the tunnel in one terminal and leave it running:
        ssh -L 3001:localhost:3001 hetzner-prod
  2) In another terminal:
        pip3 install uptime-kuma-api
        python3 add-monitors.py
     It will ask for your Kuma admin username + password.

Re-running is safe: monitors that already exist (by name) are skipped.
After it runs, set up ONE notification channel in the UI
(Settings -> Notifications) and tick "Apply on all existing monitors".
"""
import getpass
from uptime_kuma_api import UptimeKumaApi, MonitorType

KUMA_URL  = "http://localhost:3001"
SERVER_IP = "88.99.167.49"

# (name, url) — HTTP checks with TLS-cert-expiry alerts
SITES = [
    ("Guhya — website",      "https://guhya.co.in"),
    ("Care AI — website",    "https://careaisoftware.co.uk"),
    ("SignSimple — website", "https://signsimple.co.uk"),
    ("SignSimple.in",        "https://signsimple.in"),
]

# (name, url, keyword) — catches "serving the wrong site" (wrong cert/content)
KEYWORDS = [
    ("Guhya — correct site served", "https://guhya.co.in", "GUHYA"),
]

# (name, url) — REAL app health. These hit nginx -> the LIVE blue/green API,
# so they catch "container up but API/DB down" regardless of colour, with no
# sync needed (nginx already routes to the active colour via active_*.conf).
#   Care AI  /healthz     -> exposed in nginx.conf (location = /healthz), DB check
#   SignSimple /api/health/ -> Django view, routed by existing `location /api/`
HEALTH = [
    ("Care AI — API health",    "https://careaisoftware.co.uk/healthz"),
    ("SignSimple — API health", "https://signsimple.co.uk/api/health/"),
]

# (name, port) — mail ports (only matter if Mailcow stays)
PORTS = [
    ("Mail — SMTP 25",       25),
    ("Mail — SMTPS 465",     465),
    ("Mail — Submission 587", 587),
    ("Mail — IMAPS 993",     993),
]

# containers to watch (alerts the instant one stops)
# Container monitors are pinned to a container NAME. The blue/green app
# containers (careai-api/frontend, docsign-api/frontend) change color on every
# deploy, so a name-pinned monitor goes stale and shows a FALSE "down" once the
# old color is removed. For those apps, rely on the HTTP(s) monitors above
# (they test the live service regardless of color). Here we watch only the
# STABLE, always-on containers.
CONTAINERS = [
    "careai-postgres", "careai-redis", "careai-nginx", "docsign-celery",
]

def main():
    user = input("Kuma admin username: ").strip()
    pw   = getpass.getpass("Kuma admin password: ")

    api = UptimeKumaApi(KUMA_URL)
    api.login(user, pw)
    existing = {m["name"] for m in api.get_monitors()}

    def add(**kw):
        if kw["name"] in existing:
            print(f"  skip (exists): {kw['name']}")
            return
        try:
            api.add_monitor(**kw)
            print(f"  added: {kw['name']}")
        except Exception as e:
            print(f"  FAILED {kw['name']}: {e}")

    print("== Sites (HTTP + cert expiry) ==")
    for name, url in SITES:
        add(type=MonitorType.HTTP, name=name, url=url, interval=60, expiryNotification=True)

    print("== Keyword checks ==")
    for name, url, kw in KEYWORDS:
        add(type=MonitorType.KEYWORD, name=name, url=url, keyword=kw, interval=60)

    print("== App health (live blue/green via nginx) ==")
    for name, url in HEALTH:
        add(type=MonitorType.HTTP, name=name, url=url, interval=60)

    print("== Mail ports ==")
    for name, port in PORTS:
        add(type=MonitorType.PORT, name=name, hostname=SERVER_IP, port=port, interval=60)

    print("== Docker containers ==")
    try:
        from uptime_kuma_api import DockerType
        host = next((h for h in api.get_docker_hosts() if h["name"] == "local-socket"), None)
        if not host:
            host = api.add_docker_host(name="local-socket",
                                       dockerType=DockerType.SOCKET,
                                       dockerDaemon="/var/run/docker.sock")
        hid = host["id"] if isinstance(host, dict) and "id" in host else \
              next(h["id"] for h in api.get_docker_hosts() if h["name"] == "local-socket")
        for c in CONTAINERS:
            add(type=MonitorType.DOCKER, name=f"container: {c}",
                docker_container=c, docker_host=hid, interval=60)
    except Exception as e:
        print(f"  (docker monitors skipped: {e})")
        print("   If this failed, add container monitors in the UI — it's a few clicks.")

    api.disconnect()
    print("\nDone. Refresh the Uptime Kuma dashboard to see them all.")

if __name__ == "__main__":
    main()
