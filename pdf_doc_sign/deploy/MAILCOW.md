# Mailcow — self-hosted mail for SignSimple

How SignSimple (this app) sends email, and the state of the self-hosted
Mailcow server it will send through. Server provisioning scripts live in the
**parent `care-ai` repo** (`deploy/hetzner/mailcow/`), not here — this file is
the app-side view + status + the to-do list before we route production mail.

> ⚠️ Don't commit secrets. `mailcow.conf` contains generated DB/Redis/API
> passwords and DKIM private keys — keep it out of git (`.gitignore` it) and
> never paste live passwords into committed files or chat.

## Server (current)

- Host: `careai-hetzner` (Hetzner, 8 cores / 62GB) — IP `88.99.167.49`
- Admin UI: `https://88.99.167.49:8443` (self-signed cert for now → cert warning)
- Planned hostname: `mail.guhya.co.in` (later `mail.signsimple.co.uk`)
- Ports: SMTP `25`, submission `587` (STARTTLS) / `465` (SSL), IMAPS `993`.
  Non-SSL IMAP disabled (`IMAP_PORT=0`), POP3 disabled (`POPS_PORT=0`).

## Status

- ✅ Mailcow running; admin login works
- ✅ Domain `guhya.co.in` added; **DKIM 2048-bit** generated → TXT
  `dkim._domainkey` published in Spaceship DNS
- ✅ Test mailbox `test@guhya.co.in`
- ❌ Not yet wired into the SignSimple app (still on Brevo)
- ❌ `signsimple.co.uk` not yet added / MX still on Zoho

## Wiring SignSimple → Mailcow (when ready)

Django email is fully env-driven — switching providers is just env vars in
`backend/.env` (no app code change):

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.guhya.co.in        # later mail.signsimple.co.uk
EMAIL_PORT=587
EMAIL_USE_TLS=True                 # or port 465 + EMAIL_USE_SSL=True
EMAIL_HOST_USER=noreply@signsimple.co.uk
EMAIL_HOST_PASSWORD=__set_in_env_not_in_git__
DEFAULT_FROM_EMAIL=SignSimple <noreply@signsimple.co.uk>
```

Create a dedicated sending mailbox (e.g. `noreply@signsimple.co.uk`) rather
than sending app mail from the `test@guhya.co.in` account.

## Before routing PRODUCTION mail — checklist

**Security**
- [ ] Change the default admin password (`admin` / `moohoo`) — it's a known default
- [ ] Real Let's Encrypt cert for the mail hostname (replace self-signed; fixes
      the cert warning and gives valid SMTP/IMAP TLS)
- [ ] Confirm `mailcow.conf` / mailbox passwords / DKIM keys are NOT in git

**Deliverability (the make-or-break — signing links must land in inbox)**
- [ ] SPF for the sending domain (include the server IP)
- [x] DKIM — done for `guhya.co.in`; repeat for `signsimple.co.uk`
- [ ] DMARC (start `p=none`, monitor reports)
- [ ] rDNS / PTR: `88.99.167.49` → the mail hostname (set at Hetzner)
- [ ] Confirm Hetzner allows outbound port 25 (may need an unblock request)
- [ ] Warm up the IP gradually; check it's not on Spamhaus-type blocklists
- [ ] Test score with mail-tester.com + set up Google Postmaster Tools

**Cutover for signsimple.co.uk (only after tests pass)**
- [ ] Add `signsimple.co.uk` as a domain in Mailcow
- [ ] Send test mail from the app via Mailcow, confirm inbox placement
- [ ] Switch MX `signsimple.co.uk` from Zoho → Mailcow (this is the point of
      no return for live mail — do it last, after everything above is green)

## Recommendations & notes (for future updates)

**Do first (urgent):**
1. **Change the default admin password** (`admin` / `moohoo`). It's Mailcow's
   public default — anyone who finds the panel can log in. Also replace the
   self-signed cert with a real Let's Encrypt cert for the mail host so TLS on
   587/465/993 (and the admin UI) is valid.
2. **Keep secrets out of git.** `mailcow.conf` holds generated DB/Redis/API
   passwords and the DKIM private key. If an earlier `git add -A` in the
   care-ai repo swept it in, remove it and `.gitignore` it. Mailbox passwords
   live in env only — never in committed files.

**Overall approach: hybrid, not a hard cutover.** The signing/reminder emails
*are* the product — if they don't land in the inbox, signing breaks. So keep a
proven path for the critical mail and only move it to Mailcow once reputation +
deliverability are verified (SPF/DKIM/DMARC/PTR all green, good mail-tester
score, IP warmed and not blocklisted). Keep provider choice in env so we can
fail back instantly without a deploy.

**Sequence that protects live mail:** test on `guhya.co.in` → prove inbox
placement from the app → add `signsimple.co.uk` → switch its MX from Zoho to
Mailcow **last** (that's the one irreversible step).

This server also unblocks the planned 3-day escalating reminders (see
IMPROVEMENTS_BACKLOG.md #4 and #5), which need volume Brevo's per-day cap
won't allow.
