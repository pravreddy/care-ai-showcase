# SignSimple — Improvement Backlog

Two parts: a **Done (shipped)** log of changes already made, then the
**ideas / not-yet-built** list. Notes only — delete freely.

## Done (shipped)

- **In-progress signatures visible** — signers and the owner preview now see
  prior signatures stamped into the PDF (was a blank original until everyone
  signed). `generate_progress_pdf_bytes` + both PDF endpoints.
- **Signing-progress bar** ("X of N signed") on the document review page.
- **Initials field** added to the Prepare sidebar / right-click menu.
- **Signer order controls** on the Send page — position badges + up/down reorder.
- **Sequential signing** — optional "Sign in order" toggle: only signer #1 is
  emailed, each next signer is released as the previous completes, and
  out-of-turn submissions are rejected. (Migration
  `0007_document_sequential_signing`.)
- **Cancel / clear on signing fields** — a red × on every filled field lets a
  signer undo it; clearing a signature field resets the whole signature.
  Always-visible so it works on touch too. Plus a sidebar **Clear** button for
  free-form (no-field) signing. (`useSigningLogic` clearField/clearSignature,
  `SigningOverlay`, `SigningPage`.)

---

# Ideas — not yet built

## 1. Signature rendering: size + background removal  ← NEW (priority)

**Problem observed:** in the signed/preview PDF, uploaded signatures render
far too small relative to the signature line (e.g. Padmaja's signature on the
Guarantor page is tiny), and uploaded photos keep their original background
(white/coloured box) instead of sitting cleanly on the line.

Two separate sub-problems:

### 1a. Signatures are too small / not adjustable
- The image is drawn inside the field box with `preserveAspectRatio=True`, so
  a small field box (or a signature image with lots of transparent/whitespace
  padding) makes the visible ink look tiny.
- Ideas:
  - Trim transparent/whitespace margins of the signature image before drawing
    so the actual ink fills the field box (auto-crop to ink bounding box).
  - Increase default signature field height (currently ~5%) and let it scale.
  - Bring the free-sign tool's existing **SIG SIZE** slider into the
    authenticated signer flow so signers can resize their signature.
- Where: `backend/documents/services/pdf_generator.py` → `_draw_positioned_fields`
  (the `canvas.drawImage(..., preserveAspectRatio=True, mask='auto')` call);
  default sizes in `backend/documents/models/fields.py` (width/height_percent)
  and `frontend/src/components/Documents/PrepareDocument.js` (FIELD_TYPES);
  slider logic already exists in `frontend/src/components/FreeSignTool/`.

### 1b. Remove background from uploaded signature images
- An uploaded signature on white/coloured paper shows an opaque box over the
  document line. We want the background made transparent so only the ink shows.
- Ideas:
  - Lightweight: Pillow — convert to RGBA, threshold near-white/near-uniform
    pixels to alpha=0, then auto-crop to the ink. Cheap, no model. Good enough
    for most pen-on-paper signatures. Watch anti-alias halos + low-contrast ink.
  - Heavier/robust: a background-removal model (e.g. rembg/ONNX) — better on
    messy backgrounds but adds a big dependency and CPU cost. Probably overkill.
  - Do it server-side on upload for reliability (Pillow), with an optional
    before/after preview in the UI.
- Where to hook: process the image right after it's received, before it's saved
  as the signature — `backend/documents/views/public_signing.py`
  (`SignDocumentView.post`) or in `FieldProcessor` before setting
  `filled_signature`; client-side entry point is
  `frontend/src/components/Signing/UploadSignature.js`.

## 2. AI auto field-placement  (earlier idea)
Auto-detect signature/initial/date anchors in the PDF (e.g. "Signature: ……",
"Initialled (Vista)", "Initialled (Licensee)", "E-Mail: ……") and pre-place
fields for the right signer, instead of manual drag-and-drop. The labelled
lines in the Office Agreement are exactly the kind of anchors a model/regex
pass could find. Worth doing as a nice standalone feature once the core
signing fixes above are solid. Can reuse the **same self-hosted Ollama + OCR
stack** as ReceiptBook (see FUTURE_APPS_PLAN.md) — the local model detects the
anchor labels and returns field positions/signer, so the owner doesn't drag
and drop. No per-call cost.

## 3. Sequential signing: "Remind all" behaviour  (minor heads-up)
With sequential signing on, "Remind all pending" currently emails signers who
haven't reached their turn. Consider limiting reminders to the current-turn
signer only. It's an explicit owner action, so low priority.

## 4. Automated escalating reminders (3-day) + final notice  ← NEW

**Goal:** stop relying on the owner clicking "Remind". Auto-email pending
signers once a day for 3 days; the last email warns the document will be
cancelled/needs re-sending if still unsigned.

- Infra already exists: Celery + celery-beat are in docker-compose, and
  `django-celery-beat` is installed. So a daily scheduled task is the natural
  home — no new infra needed.
- Suggested daily beat task: for each PENDING signer past 1/2/3 days since
  send (or since last reminder), send an escalating email:
    - Day 1: gentle nudge
    - Day 2: firmer reminder
    - Day 3: final notice — "this will be cancelled / you'll need it re-sent"
- Track escalation so wording/stop is correct: add `reminder_count` and
  `last_reminder_at` to `DocumentSigner` (small migration), or a reminder log.
- After the final notice + grace period, optionally auto-set the document to
  CANCELLED/EXPIRED (note: `Document.expires_at` already exists for the long
  90-day expiry; the 3-day signing window is a *separate, shorter* deadline —
  don't conflate them).
- Respect sequential mode: only remind the current-turn signer (ties to #3).
- Needs 3 new email templates + a final-notice template
  (`backend/documents/emails/`). Reuse `send_reminder_email`.
- **Depends on #5** — daily reminders across many documents = real volume, which
  is exactly why the current SMTP provider's per-day cap is a problem.

## 5. Move SMTP to self-hosted Mailcow (from Brevo)  ← NEW

**Goal:** send unlimited transactional mail (esp. the #4 daily reminders)
without Brevo's per-day limits, on our own mail server (Mailcow).

**Code side is trivial.** Django email is already fully env-driven
(`EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`). Switching =
changing env vars to point at Mailcow's SMTP. No application code change.

**The real work is deliverability + ops, not code:**
- DNS auth is mandatory or signing-link mail lands in spam: **SPF** (include
  the server IP), **DKIM** (Mailcow generates a selector — publish it),
  **DMARC** (start `p=none` and monitor), and **rDNS/PTR** matching the HELO
  hostname. Valid TLS cert too.
- Confirm the host allows **outbound port 25** (AWS/GCP/DO often block it).
- **Warm up the IP** gradually and check it's not on blocklists (Spamhaus etc.).
- Add **bounce/complaint handling** — a transactional provider does this for
  you; self-hosting means we own it (Rspamd + bounce parsing).
- Monitor with mail-tester.com + Google Postmaster Tools.

**My recommendation: hybrid, not a hard cutover.** The signing-link/reminder
emails *are* the product — if they don't arrive, signing breaks. So:
- Keep a reputable, well-warmed path for the critical signing/reminder mail
  (could be Mailcow once its reputation is proven, or keep a provider as
  fallback), and use self-hosted for volume/non-critical mail.
- Because Django is env-configurable, keep provider choice swappable (even a
  per-message routing if needed) so we can fail over without code changes.
- Don't point production signing mail at a brand-new, un-warmed IP.
