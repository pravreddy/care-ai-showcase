# =============================================================
# Avyangah Technologies — Product Roadmap
# Created: 3 April 2026
# =============================================================
# Priority: MIGRATION > SIGNSIMPLE GROWTH > CAREAI > POSTAL
# =============================================================


# =============================================
# PHASE 1: MIGRATION (April 9-20)
# =============================================
# Goal: Move from Vultr ($44/mo) to Hetzner (~£13/mo)
# Status: Compose files DONE, migration scripts DONE

- [x] Unified docker-compose (base + careai + docsign + postal overlays)
- [x] Caddyfile replacing nginx (auto HTTPS)
- [x] Server setup script for Hetzner
- [x] Migration script (Vultr → Hetzner)
- [x] Deploy script (blue/green)
- [x] Groq LLM integration (replaces Ollama)
- [ ] April 9: Purchase Hetzner CPX32 (3vCPU, 8GB, 160GB)
- [ ] April 9-14: Deploy + test both apps on Hetzner
- [ ] April 15 06:27: Switch DNS (both domains)
- [ ] April 15-20: Monitor, verify everything stable
- [ ] April 20: Destroy Vultr server + close account
- [ ] Sign up PeaSoup S3 (UK storage, £4.99/TB)
- [ ] Update django-storages to use PeaSoup endpoint


# =============================================
# PHASE 2: SIGNSIMPLE GROWTH ENGINE (April 21 - May)
# =============================================
# Goal: Get paying customers. SignSimple is the revenue product.

## 2a. Coupon & Discount System (Django)
# SignSimple needs its own coupon system (CareAI has one, SignSimple doesn't yet)

- [ ] Coupon model for SignSimple:
      - code (unique, e.g. PRAVEEN-6MF-X7K2)
      - type: INDIVIDUAL (tied to email) or ORGANISATION (tied to org)
      - plan_granted: STARTER / PROFESSIONAL / ENTERPRISE
      - duration_days: 90 (3mo) / 180 (6mo) / 365 (1yr)
      - max_uses: 1 for personal, N for org-wide
      - generated_by: CHATBOT / ADMIN / SALES
      - lead_name, lead_email (who it was created for)
      - is_redeemed, redeemed_by, redeemed_at
      - expires_at

- [ ] Coupon API endpoints (org admin + platform admin):
      POST   /api/coupons/generate/     — generate unique coupon (admin or chatbot)
      POST   /api/coupons/redeem/       — redeem coupon at signup
      GET    /api/coupons/validate/{code}/ — check if code is valid
      GET    /api/coupons/              — list all coupons (platform admin)
      PATCH  /api/coupons/{id}/         — deactivate coupon

- [ ] Coupon redemption flow:
      1. User visits signsimple.co.uk/signup?coupon=PRAVEEN-6MF-X7K2
      2. Coupon auto-fills, validated in real-time
      3. User registers → plan auto-upgraded to the coupon's plan
      4. After duration expires → downgrades to FREE (with email warning)

- [ ] Org-level coupons:
      - Org admin generates codes for their team
      - "Give this code to your staff: ACME-TEAM-2026"
      - Each team member redeems → added to org automatically
      - Bulk import: upload CSV of emails → generate + send coupons

## 2b. AI Chatbot Widget
# Lead capture → coupon generation → email via Postal

- [ ] React chat widget component (embeds with single <script> tag)
      - Floating button bottom-right
      - Chat-only (no phone)
      - Branded per org (logo, colours from org settings)
      - Works on signsimple.co.uk, careaisoftware.co.uk, client sites

- [ ] Chat flow (Groq AI powered):
      1. Greeting: "Hi! How can I help you today?"
      2. AI converses naturally about the product
      3. Naturally collects: first name, last name
      4. Offers to send info: "Shall I email you the details?"
      5. Collects email (NOT phone number)
      6. Generates unique coupon based on conversation:
         - Just browsing → 3 month free trial
         - Interested for company → 6 month free trial
         - Specific use case mentioned → 1 year trial
      7. Sends coupon via Postal email

- [ ] Lead model (Django):
      - first_name, last_name, email
      - source: CHATBOT / MANUAL / IMPORT
      - organisation (if mentioned)
      - conversation_summary (AI-generated)
      - coupon_generated (FK to coupon)
      - status: NEW / CONTACTED / CONVERTED / LOST
      - created_at

- [ ] Lead dashboard (React):
      - List all captured leads
      - Filter by status, source, date
      - See which coupons were redeemed
      - Conversion rate metrics

## 2c. Internationalisation (i18n)
# Make SignSimple work in multiple languages

- [ ] Phase 1 (EU + English):
      - Install react-i18next
      - Extract all English strings to en.json
      - Add: French (fr), German (de), Spanish (es), Portuguese (pt)
      - Language selector in UI
      - PDF signing pages in visitor's language

- [ ] Phase 2 (Asia + Middle East):
      - Chinese simplified (zh-CN), Japanese (ja)
      - Arabic (ar) — needs RTL layout support
      - Hindi (hi)

- [ ] Backend i18n:
      - Email templates in multiple languages
      - Error messages localised
      - Document signing page follows signer's browser language

## 2d. Website Content Updates

- [ ] Remove "data stays in UK" → replace with:
      "Documents stored securely in the United Kingdom.
       Processing powered by GDPR-compliant European infrastructure.
       Storage provided by ISO 27001 certified UK datacentres."
- [ ] Add PeaSoup / NHS trust logos on security page
- [ ] Add multi-language landing pages (SEO for EU markets)


# =============================================
# PHASE 3: POSTAL EMAIL SERVICE (May - June)
# =============================================
# Goal: Self-hosted email service replacing Brevo/Mailgun

- [x] Django messaging app (models, views, webhooks, postal client)
- [x] React dashboard (TypeScript, MUI, Recharts)
- [ ] Request Hetzner port 25 unblock (after first invoice)
- [ ] OR: Get small Kamatera for Postal ($4-8/mo, port 25 open)
- [ ] Deploy Postal with docker-compose.postal.yml
- [ ] Connect Django messaging app to Postal
- [ ] Migrate transactional emails from Brevo/Gmail to own Postal
- [ ] Chatbot email delivery via Postal
- [ ] Coupon emails via Postal


# =============================================
# PHASE 4: CAREAI IMPROVEMENTS (June - July)
# =============================================
# Goal: Make CareAI production-ready

- [ ] Groq integration testing (all clinical endpoints)
- [ ] Voice transcription testing (Whisper)
- [ ] NHS data scraper improvements
- [ ] Care notes templates
- [ ] Add coupon system for CareAI Pro subscriptions
- [ ] Chatbot for careaisoftware.co.uk (same widget, different branding)
- [ ] Future: dedicated Ollama server when revenue justifies it


# =============================================
# PHASE 5: INDIA EXPANSION (.in domain)
# =============================================
# Goal: Deploy for Indian market

- [ ] Research Indian VPS (Contabo Mumbai ~€5/mo)
- [ ] .in domain registration
- [ ] Hindi + Telugu + Tamil language support
- [ ] Indian SMS provider (MSG91) for OTP
- [ ] Indian payment gateway (Razorpay)
- [ ] Guhya app deployment (separate compose)


# =============================================
# PHASE 6: INTEGRATION TESTS (Ongoing)
# =============================================
# Goal: Automated testing so manual testing is eliminated

- [ ] SignSimple pytest:
      - Auth: register, login, OAuth, password reset
      - Documents: upload, add signers, sign, download
      - Organisations: create, invite, roles, branches
      - Sales: clients, daily sales, invoices, disputes
      - Coupons: generate, validate, redeem, expire
      - Payments: checkout, webhook, subscription upgrade

- [ ] CareAI pytest:
      - Auth: register, login, OAuth
      - LLM: clinical notes, summaries (Groq)
      - Voice: upload audio, transcription
      - NHS: data scraping, MCP tools
      - Coupons: generate, redeem

- [ ] Integration:
      - Chatbot → lead capture → coupon → email → signup
      - End-to-end document signing flow
      - Multi-org data isolation testing


# =============================================
# INFRASTRUCTURE SUMMARY
# =============================================
#
# Current (Vultr):         ~£37/mo
# After migration:         ~£13/mo (Hetzner) + £0.05/mo (PeaSoup) = ~£13/mo
# Monthly savings:         ~£24/mo = £288/year
#
# Hetzner CPX32 (Germany): All apps, compute, processing
# PeaSoup S3 (UK):         Document storage, UK data residency
# Groq (Cloud):            AI for CareAI (free tier)
# Postal (Hetzner/Kamatera): Email service (later)
# Namecheap/Spaceship:     Domain names
#
# Split-ready: Each service uses env vars for connections.
# Change DB_HOST, REDIS_HOST, POSTAL_API_URL to move services
# to separate servers without code changes.
