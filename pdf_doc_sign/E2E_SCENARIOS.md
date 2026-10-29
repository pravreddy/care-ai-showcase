# SignSimple — End-to-End Scenarios
> Living document. Update as features change.
> Framework recommendation: **Playwright** (lightweight, fast, no Selenium)

---

## PRODUCT AREAS

1. Public / Free Sign Tool (SC-001 to SC-019)
2. Authentication (SC-020 to SC-027)
3. Organisation Management (SC-028 to SC-041)
4. Document Signing — Sender (SC-042 to SC-050)
5. Document Signing — Signer (SC-051 to SC-055)
6. Sales — Clients (SC-056 to SC-060)
7. Sales — Daily Sales Entry (SC-061 to SC-072)
8. Sales — Invoice Generator (SC-073 to SC-078)
9. Client Portal — Delivery Confirmation (SC-079 to SC-083)
10. Disputes (SC-084 to SC-086)
11. Platform Admin Panel (SC-087 to SC-094)
12. Profile and Subscription (SC-095 to SC-098)
13. Security and Access Control (SC-099 to SC-105)

---

## 1. Public / Free Sign Tool
Route: /free-electronic-signature — No auth required

SC-001  Upload valid PDF
  - Upload test_signsimple.pdf
  - Expect: Editor opens, "Page 1 of 2", sidebar tools visible

SC-002  Upload invalid file type
  - Upload .docx file
  - Expect: Error "Please upload a PDF file"

SC-003  Upload oversized file (>20MB)
  - Expect: Error "File too large. Maximum 20MB"

SC-004  Draw signature and place
  - Sign → Draw tab → draw → Use This Signature → click on PDF
  - Expect: Placing banner shown, then signature overlay appears on document

SC-005  Type signature — 6 font previews
  - Sign → Type tab → type "John Smith"
  - Expect: All 6 font previews show "John Smith", click selects font

SC-006  Colour picker (Draw tab)
  - Sign → Draw tab → click blue dot → draw
  - Expect: Drawn signature is blue

SC-007  Move placed item
  - Place signature → click to select → drag to new position
  - Expect: Item moves

SC-008  Resize via corner handles
  - Place signature → select → drag SE corner outward
  - Expect: Item gets larger, 4 corner dots visible when selected

SC-009  Delete placed item
  - Place signature → select → click red X
  - Expect: Item removed

SC-010  Add Date tool
  - Date tool → click on document
  - Expect: Today's date placed (e.g. "30 Mar 2026")

SC-011  Add Text tool
  - Text → type "Approved" → confirm → place
  - Expect: "Approved" text on document

SC-012  Add Checkmark
  - Checkmark tool → click on document
  - Expect: Green checkmark placed

SC-013  Undo
  - Place 2 items → Undo
  - Expect: Last item removed, first remains

SC-014  Multi-page navigation
  - Upload 2-page PDF → place item page 1 → go to page 2
  - Expect: Page 1 item not visible on page 2
  - Go back to page 1 → item visible again

SC-015  Download signed PDF  *** HIGH PRIORITY ***
  - Place item → Download
  - Expect: "Generating…" spinner → browser saves signed_*.pdf
  - Expect: Success page "Successfully Completed!"

SC-016  Re-download from success page
  - Success page → "Download Document"
  - Expect: Same PDF downloads again

SC-017  Sign another document
  - Success page → "Sign Another Document"
  - Expect: Returns to upload page, clean state

SC-018  Signature size slider
  - Adjust slider to 250px → place signature
  - Expect: Signature larger than default (150px)

SC-019  Signer name pre-fills Type tab
  - Enter "Praveen" in Your Name field → Sign → Type tab
  - Expect: Input pre-filled with "Praveen"

---

## 2. Authentication
Routes: /register, /login, /forgot-password, /set-password/:token

SC-020  Register with email
  - Fill name, email, password → submit
  - Expect: Activation email message shown

SC-021  Register duplicate email
  - Expect: Error "email already exists"

SC-022  Login email/password  *** HIGH PRIORITY ***
  - Enter valid credentials
  - Expect: Redirected to /dashboard

SC-023  Login wrong password
  - Expect: Error "Invalid email or password"

SC-024  Google OAuth login
  - Click Sign in with Google → complete flow
  - Expect: Redirected to /dashboard

SC-025  Forgot password flow
  - /forgot-password → enter email → check email → click link → set password
  - Expect: "Password set successfully", can login

SC-026  Set password via invite link
  - Admin creates member with send-email method
  - New user clicks link → /set-password/:token → sets password
  - Expect: Can login

SC-027  Logout
  - Click avatar → Logout
  - Expect: Redirected to /login, localStorage cleared

---

## 3. Organisation Management
Route: /organisation — Auth required

SC-028  Create organisation request
  - Fill name, domain, work email → submit
  - Expect: "Verification email sent", request in Pending list

SC-029  View members list
  - Members tab
  - Expect: All active members shown with role chips

SC-030  Add member — send email
  - Add Member → email, role=Member, method=send email
  - Expect: Password setup URL shown, setup email sent

SC-031  Add member — temp password
  - Add Member → method=temp password
  - Expect: Temporary password shown with copy button

SC-032  Add existing SignSimple user to org
  - Add Member with already-registered email
  - Expect: User added immediately, no new account

SC-033  Change member role
  - Edit (pencil) → change to Admin → save
  - Expect: Role chip updates

SC-034  Remove member
  - Delete (trash) → confirm → Remove
  - Expect: Member removed from list

SC-035  Cannot remove yourself
  - Expect: Error "You cannot remove yourself"

SC-036  Cannot remove Owner
  - Expect: No delete button on Owner row

SC-037  Invite by email link
  - Invite by Email → send
  - Expect: Pending invite appears, email sent

SC-038  Add branch
  - Branches tab → Add Branch → name, city → save
  - Expect: Branch card appears with 0 members

SC-039  Edit org details
  - Settings tab → Edit → change name → Save
  - Expect: "Organisation updated successfully"

SC-040  Brand colour
  - Settings tab → Edit → change colour → Save
  - Expect: Colour saved

SC-041  Request sales access
  - Sales Access tab → select industry → add use case → Request
  - Expect: "Request Submitted!" shown, you receive email with industry

---

## 4. Document Signing — Sender Flow
Routes: /documents/upload, /documents/:id/prepare, /documents/:id/send

SC-042  Upload PDF
  - /documents/upload → upload PDF
  - Expect: Document created, visible in My Documents

SC-043  Upload DOCX (converted to PDF)
  - Upload .docx
  - Expect: Converted, document created

SC-044  Upload JPG/PNG (converted to PDF)
  - Upload .jpg
  - Expect: Converted, document created

SC-045  Prepare document — place signature field
  - Prepare → drag signature field onto document
  - Expect: Field placed

SC-046  Send for signing
  - Send → add signer email → Send
  - Expect: Email sent, status = Pending

SC-047  Send reminder to signer
  - Pending document → Send Reminder
  - Expect: Reminder email sent

SC-048  Download completed document
  - Completed document → Download
  - Expect: PDF with embedded signature

SC-049  Audit certificate
  - Completed → Audit Certificate
  - Expect: PDF with timestamp, IP, email

SC-050  Delete document
  - Delete from list
  - Expect: Document removed

---

## 5. Document Signing — Signer Flow
Route: /sign/:token — No auth required

SC-051  Open signing link
  - Open /sign/:token from email
  - Expect: Document loads in signing view, not our app nav

SC-052  Draw and place signature
  - Click signature field → draw → confirm → place
  - Expect: Signature on document

SC-053  Submit signed document
  - Complete all fields → Submit
  - Expect: "Signed successfully", sender notified

SC-054  Invalid token
  - /sign/invalid-token
  - Expect: "Invalid or expired link"

SC-055  Already signed
  - Open already-used link
  - Expect: "Already signed" message

---

## 6. Sales — Clients
Route: /sales/clients — Auth + sales access required

SC-056  Add client
  - Add Client → name, email, address → Save
  - Expect: Client in list

SC-057  Client legal details (GST, PAN)
  - Add GST number, PAN, legal name → Save
  - Expect: Appear on generated invoices

SC-058  Suggested currency from country
  - Client country = India → save
  - Expect: suggested_currency = INR

SC-059  Edit default packing charge
  - Edit client → change packing charge → Save
  - Expect: New charge used as default in daily sales rows

SC-060  Auto-create portal user on email entry
  - Add client with email → Save
  - Expect: Portal user created, setup email sent to client

---

## 7. Sales — Daily Sales Entry
Route: /sales — Auth + sales access required

SC-061  Select client and view month  *** HIGH PRIORITY ***
  - Select client from dropdown
  - Expect: All days of current month shown

SC-062  Add items to a day
  - Click Items cell → Add Item → name, qty, price → Save Items
  - Expect: Food total calculated, items chip shows count

SC-063  Save single row
  - Edit row → click blue save disk
  - Expect: Row turns green, "Saved 2026-03-30" message

SC-064  Save All
  - Edit multiple days → Save All
  - Expect: All unsaved rows saved, count in success message

SC-065  Copy from previous day
  - Click copy icon
  - Expect: Items + pack + courier copied from last non-holiday row

SC-066  Mark as holiday
  - Toggle Holiday switch
  - Expect: Row grey, Pack/Courier show —, Food shows —

SC-067  Holiday reason
  - Toggle holiday → type "Diwali" → save
  - Expect: Reason saved

SC-068  Month navigation
  - Click left arrow → previous month shown
  - Click Today → current month

SC-069  Packing and courier charges
  - Enter 15 in Pack, 20 in Courier
  - Expect: Total = Food + 35

SC-070  Month total row
  - Enter items multiple days
  - Expect: Bottom total row sums correctly

SC-071  Export Excel
  - Export Excel button
  - Expect: .xlsx file downloads for that month/client

SC-072  Send confirmation email to client
  - Saved row → click email icon
  - Expect: Email sent, icon changes to pending confirmation

---

## 8. Sales — Invoice Generator
Route: /sales/invoices — Auth + sales access required

SC-073  Generate invoice
  - Select client + date range → Generate
  - Expect: Invoice created, PDF available

SC-074  Auto currency from client country
  - Client country = UK → open invoice generator
  - Expect: Currency auto-selects GBP

SC-075  Daily breakdown checkbox
  - Tick "Daily breakdown" → Generate
  - Expect: Invoice PDF has day-by-day rows

SC-076  Download invoice PDF
  - Invoice → Download
  - Expect: PDF with correct totals

SC-077  Email invoice to client
  - Invoice → Send Email
  - Expect: PDF emailed to client contact

SC-078  Mark invoice as paid
  - Invoice → Mark Paid
  - Expect: Status = PAID

---

## 9. Client Portal — Delivery Confirmation
Route: /confirm-delivery/:token — No auth required

SC-079  Open confirmation link
  - Open /confirm-delivery/:token from email
  - Expect: Delivery details shown, Confirm + Report Issue buttons

SC-080  Confirm delivery
  - Click Confirm
  - Expect: "Confirmed" message, Daily Sales row shows Confirmed chip

SC-081  #dispute hash auto-opens form
  - URL with #dispute
  - Expect: Report Issue form opens automatically

SC-082  Raise dispute
  - Report Issue → fill description → submit
  - Expect: Dispute created, org emailed, row shows amber Dispute chip

SC-083  Invalid token
  - /confirm-delivery/invalid
  - Expect: "Invalid or expired link"

---

## 10. Disputes
Route: /disputes — Auth + sales access required

SC-084  View open disputes
  - Expect: List of open disputes for current org only

SC-085  Resolve dispute
  - Resolve → add notes → confirm
  - Expect: Status = RESOLVED

SC-086  Acknowledge dispute
  - Acknowledge
  - Expect: Status = ACKNOWLEDGED

---

## 11. Platform Admin Panel
Route: /platform-admin — Superuser only

SC-087  Access denied for non-superuser  *** SECURITY CRITICAL ***
  - Login as regular user → navigate to /platform-admin
  - Expect: "Access denied" message

SC-088  View all orgs
  - Login as superuser → /platform-admin
  - Expect: All orgs in table with plan, status, member count

SC-089  Sales Requests tab shows pending
  - Org has requested but not yet enabled
  - Expect: Amber row in Sales Requests tab

SC-090  Enable sales
  - Click Enable Sales on org
  - Expect: Green Enabled chip, notification email sent

SC-091  Disable sales
  - Disable on enabled org → confirm
  - Expect: Sales disabled

SC-092  Change plan (superuser only)
  - Edit pencil → change to STARTER → save
  - Expect: Plan updates

SC-093  Edit button hidden for non-superuser
  - Avyangah org ADMIN (not superuser) opens platform admin
  - Expect: Edit pencil not shown

SC-094  Search
  - Type org name in search
  - Expect: Table filters

---

## 12. Profile and Subscription
Routes: /profile, /subscription

SC-095  Update name
  - Profile → change Full Name → Save
  - Expect: Name updates in header

SC-096  Change password
  - Change Password → old + new → Save
  - Expect: "Password changed"

SC-097  View plan
  - /subscription
  - Expect: Current plan shown

SC-098  Upgrade plan
  - Upgrade → select plan → checkout
  - Expect: Payment page loads

---

## 13. Security and Access Control

SC-099  No sales access = no sales routes  *** SECURITY CRITICAL ***
  - User with no sales org logs in
  - Expect: No Sales section in sidebar, /sales redirects

SC-100  Org data isolation  *** SECURITY CRITICAL ***
  - Login as Café Gopala admin
  - Expect: Only sees Café Gopala data, not other orgs

SC-101  Client portal user restricted view
  - Login as client portal user
  - Expect: Only Deliveries + Concerns in sidebar

SC-102  Removing superuser blocks Django admin
  - Remove is_superuser via SQL → user tries /admin/
  - Expect: 403

SC-103  Removing org membership revokes access
  - Remove user from org
  - User logs in again
  - Expect: No sales section

SC-104  Multi-org switcher
  - User in 2 orgs
  - Expect: Org dropdown in top bar, switching loads correct data

SC-105  Tenant middleware blocks cross-org requests
  - Send request with X-Organisation-ID of a different org
  - Expect: 403 or empty response

---

## RECOMMENDED FRAMEWORK: Playwright

Not Selenium — reasons:
  - Runs in Node.js, no Java or WebDriver
  - Faster than Selenium, built-in smart waiting
  - Record tests with: npx playwright codegen https://signsimple.co.uk
  - Headless in CI, visual in local

Setup:
  cd pdf_doc_sign/frontend
  npm install -D @playwright/test
  npx playwright install chromium

File structure:
  frontend/e2e/
    free-sign.spec.js       SC-001 to SC-019
    auth.spec.js            SC-020 to SC-027
    organisation.spec.js    SC-028 to SC-041
    documents.spec.js       SC-042 to SC-055
    daily-sales.spec.js     SC-061 to SC-072
    invoices.spec.js        SC-073 to SC-078
    client-portal.spec.js   SC-079 to SC-083
    platform-admin.spec.js  SC-087 to SC-094
    security.spec.js        SC-099 to SC-105

Priority order for writing tests first:
  1. SC-015  Download signed PDF (broke once, highest risk)
  2. SC-022  Login (everything depends on this)
  3. SC-061  Daily sales entry (core business flow)
  4. SC-100  Org data isolation (security)
  5. SC-087  Platform admin access (security)

---

## STATUS TRACKER

| ID     | Scenario                        | Unit ✓ | E2E ✓ | Last verified |
|--------|---------------------------------|--------|-------|---------------|
| SC-001 | Upload valid PDF                | yes    | no    | 30 Mar 2026   |
| SC-015 | Download signed PDF             | yes    | no    | 30 Mar 2026   |
| SC-022 | Login email/password            | yes    | no    | —             |
| SC-061 | Daily sales select client       | yes    | no    | —             |
| SC-066 | Mark day as holiday             | yes    | no    | 30 Mar 2026   |
| SC-087 | Platform admin access control   | yes    | no    | 30 Mar 2026   |
| SC-100 | Org data isolation              | yes    | no    | —             |
