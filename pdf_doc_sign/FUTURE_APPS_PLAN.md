# Future Apps — Product Plan

Forward-looking product ideas beyond the SignSimple signing app. Separate
products that may become their own repos; kept here so the thinking isn't lost.

---

# Product A (build first): "ReceiptBook" — a clean record-keeper

**Deliberately narrow.** We are NOT doing the accountant's job or the bank's
job. We just help an owner keep clear records: link every bank transaction to
its receipt so nothing has to be searched for later. That's the whole job in
phase 1.

## What it does

1. User photographs / uploads purchase receipts and invoices (phone or web).
2. **User uploads their own monthly bank statement** — they download it from
   their bank (or it arrives by email) and share the CSV/PDF into the app.
   **No Open Banking, no bank API, no FCA licence** — we don't touch the bank.
3. The app **maps each transaction to its receipt** automatically (amount +
   date + fuzzy vendor name), so the owner never has to hunt for proof of a
   purchase again.
4. Everything is stored and kept (HMRC wants records for ~6 years), so when an
   accountant or HMRC asks, the proof is one click away.

That's it. No VAT calc, no filing, no submission in this phase.

## Why this scope is the right MVP

- **No regulation to clear** — no HMRC recognition, no Open Banking/FCA spend.
  Just storage + matching. Fast and cheap to build.
- It still produces **MTD-ready digital records**, so it's a stepping stone we
  can sell as "be ready for Making Tax Digital" without doing MTD ourselves.
- Solves the real, painful problem directly: missing/unmatched proof of purchase
  (the exact 11-year HMRC headache this came from).

## The main build challenge: statement parsing

Receipts are the easy part (OCR: AWS Textract / Google Document AI / Azure).
The work is reading **varied bank statement formats**:
- Start with **CSV import** + a simple column-mapping step (date / amount /
  description) — every UK bank exports CSV, and it's far easier than PDF.
- Add **PDF statement parsing/OCR** later, bank by bank.
- Matching UX: auto-match what's confident; show **"unmatched transactions"**
  and **"unmatched receipts"** lists so the owner resolves the gaps. That gap
  list *is* the product's value (and the proof-of-completeness for HMRC).
- Learn from each manual correction to improve future matches.

## Pricing / monetisation

- **Cheap on purpose:** free for year 1, then ~**£1/month (£10/year)**.
- Storage is cheap (Hetzner), so the economics work as a low-cost utility /
  acquisition play rather than a big revenue line.
- **Upsell to accountants:** once an owner has clean mapped records, give the
  accountant a read/export/handoff view — accountants pay (per client) to pull
  the receipts + invoices and do the actual filing. The clean data is the asset.

## Compliance-lite (still financial data)

Even with no bank API, you're storing statements + receipts = sensitive
financial data. So: UK-GDPR, encrypt at rest/in transit, and lean into the
~6-year retention as a *feature* ("we keep your proof so HMRC can't catch you
out"). Keep the data model **filing-ready** so Product B can consume it later.

## Storage

- **Hetzner Storage Box** = cheap encrypted archive / backup for the long
  retention tier (SFTP/WebDAV/Borg — not an S3 API).
- Live app images → **S3-compatible object storage** (you already use
  `django-storages` + MinIO; Hetzner Object Storage / Backblaze / Vultr).
- Pattern: object storage = hot tier, Storage Box = cold archive.

## Reuse from the existing stack (not greenfield)

Django + React, `django-storages` + S3/MinIO, the AI-detector/doc-processing
pipeline (→ receipt OCR), multi-tenant orgs, auth, and payments are all reusable.

## AI stack — decision (reuse first, don't buy yet)

- **Reuse the existing self-hosted Ollama** (already running on the Hetzner
  box) + a **free OCR engine** (Tesseract / PaddleOCR). No new spend for the MVP.
- Split the work: the **OCR engine** does pixels→text (CPU-efficient); a
  **small local LLM via Ollama** does text→structured JSON
  (merchant / date / total / VAT). **Avoid vision LLMs on this box** — it's
  CPU-only, they'd be too slow.
- **Keep it behind a swappable interface** so a paid per-page receipt API
  (Textract / Google / Azure) or a GPU box can drop in later as a config
  change, not a rewrite.
- **Run async** via the existing Celery, off-peak, rate-limited; set Docker
  CPU/memory limits so AI can't starve the live apps.
- Privacy bonus: local OCR + LLM keeps financial documents in-house — good for
  an HMRC-records product.

**Hardware reality (today):** one Hetzner box (Xeon E3-1275V6, 4c/8t, 64GB ECC,
no GPU) hosts SignSimple + CareAI + Mailcow + DBs + Ollama, running at ~6–8%
load. Fine for building/testing the MVP. **Plan: split each product (and the AI
workload) onto its own server once there's revenue** — the swappable interface
above makes that a config change rather than a rebuild.

---

# Product B (separate app, later): VAT / tax filing

A **separate product** that uses Product A's clean, mapped data to let the end
user (or accountant) calculate VAT and submit small filings. Kept apart on
purpose — it carries all the regulated complexity Product A avoids:

- Must become **HMRC-recognised MTD-compatible software** (HMRC APIs + OAuth +
  fraud-prevention headers + a recognition/listing process).
- VAT engine (standard / flat-rate / cash accounting), 9-box return, MTD VAT
  submission. **Keep submission review-gated** (user/accountant approves) for
  liability.
- Later: MTD ITSA quarterly updates + accountant portal.
- Not legal/accounting advice — verify HMRC recognition + FCA perimeter with
  HMRC developer docs and a compliance specialist before building this one.

---

# Deferred (not spending on these now)

- **Open Banking auto-import of statements.** Would replace the manual upload,
  but it costs money and adds consent/renewal complexity. When we do it: use a
  licensed aggregator under *their* FCA licence (TrueLayer, Yapily, Tink, Plaid,
  Moneyhub, Salt Edge, Enable Banking) — read-only AIS only; don't become an
  AISP. (The old free GoCardless/Nordigen tier has been wound down.) Build a
  thin provider-abstraction so it's swappable. **Not now.**

## Market context (why Product B will have demand later)

MTD is dragging micro-businesses into software in waves: MTD for Income Tax is
mandatory for sole traders/landlords with gross income **>£50k from Apr 2026,
>£30k from Apr 2027, >£20k from Apr 2028** (~860k people in wave one); MTD for
VAT has applied to VAT-registered businesses since 2022. So a clean-records tool
now (Product A) naturally feeds a filing tool later (Product B) as the rules
pull more people in.

---

# Honest verdict

The narrowed scope is the smart move: a receipt↔transaction mapper with manual
statement upload is cheap, low-risk, has no regulatory burden, and solves the
real pain directly. Keep the filing/VAT and Open Banking as separate, later bets
so this one stays simple. The one real engineering effort is parsing varied bank
statement formats — start with CSV — and a good "unmatched" resolution UX.
Design the data model now so the future filing product can plug straight in.
