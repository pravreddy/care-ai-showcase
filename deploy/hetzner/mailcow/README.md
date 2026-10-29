# Mailcow Mail Server — Avyangah Technologies

Self-hosted email for all Avyangah company domains using Mailcow on Hetzner.
Test with `guhya.co.in` first, then migrate other domains from Zoho.

## Architecture (current — nginx reverse proxy)

```
Internet
    │
    ├── Port 80/443 → Nginx (reverse proxy)
    │   ├── signsimple.co.uk      → SignSimple (Docker blue/green)
    │   ├── guhya.co.in           → Static site
    │   └── mail.guhya.co.in      → Mailcow web UI + SOGo webmail
    │
    ├── Port 25    → Mailcow (SMTP inbound)
    ├── Port 465   → Mailcow (SMTPS)
    ├── Port 587   → Mailcow (Submission — apps send here)
    ├── Port 993   → Mailcow (IMAP — email clients)
    └── Port 4190  → Mailcow (Sieve filters)
```

## Quick Start

```bash
# From your local machine
scp deploy/hetzner/mailcow/setup-mailcow.sh deploy@88.99.167.49:/tmp/

# SSH into server
ssh deploy@88.99.167.49

# Run setup
sudo bash /tmp/setup-mailcow.sh mail.guhya.co.in
```

Then follow the 7 steps printed by the script.

## DNS Records for guhya.co.in (at registrar)

| Type | Name | Value |
|------|------|-------|
| A    | mail | 88.99.167.49 |
| MX   | @    | mail.guhya.co.in (priority 10) |
| TXT  | @    | `v=spf1 a mx ip4:88.99.167.49 -all` |
| TXT  | _dmarc | `v=DMARC1; p=quarantine; rua=mailto:dmarc@guhya.co.in` |
| TXT  | dkim._domainkey | *(copy from Mailcow admin after setup)* |

## rDNS (Hetzner Robot → Server → IPs)

| IP | PTR Record |
|----|------------|
| 88.99.167.49 | mail.guhya.co.in |

## After Setup

| URL | Who | What |
|-----|-----|------|
| https://mail.guhya.co.in | Admin (you) | Manage domains, mailboxes, DKIM |
| https://mail.guhya.co.in/SOGo | All users | Webmail — read/send/calendar |

## Migration Plan

| Phase | Domain | Action |
|-------|--------|--------|
| 1 (NOW) | guhya.co.in | Test Mailcow — no Zoho to break |
| 2 (LATER) | signsimple.co.uk | Add domain in Mailcow → switch MX from Zoho |
| 3 (LATER) | careaisoftware.co.uk | Add domain in Mailcow → switch MX from Zoho |
| 4+ | Other companies | Add as needed |

## Adding a New Domain (after Phase 1 testing)

1. Mailcow admin → Mail Setup → Domains → Add domain
2. Set domain quota (e.g. 10GB) and max mailbox quota (e.g. 2GB)
3. Create mailboxes (e.g. info@company.co.uk, noreply@company.co.uk)
4. Copy DKIM key from ARC/DKIM page
5. Add DNS records: MX, SPF, DKIM, DMARC
6. Test: https://www.mail-tester.com (aim for 10/10)
7. Once confirmed working, switch MX from Zoho → mail.guhya.co.in

## Django Integration (SignSimple / CareAI)

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.guhya.co.in
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=noreply@signsimple.co.uk
EMAIL_HOST_PASSWORD=<mailbox password>
DEFAULT_FROM_EMAIL=noreply@signsimple.co.uk
```

## Mobile / Desktop Email Client Settings

| Setting | Value |
|---------|-------|
| IMAP Server | mail.guhya.co.in |
| IMAP Port | 993 (SSL/TLS) |
| SMTP Server | mail.guhya.co.in |
| SMTP Port | 587 (STARTTLS) |
| Username | full email address |

## Server

- Hetzner Dedicated: Xeon E3-1275V6, 64GB RAM, 2x512GB NVMe
- IP: 88.99.167.49
- Cost: €0 extra (included in €40.70/mo)
- Mailcow uses ~4-6GB RAM of 64GB available
