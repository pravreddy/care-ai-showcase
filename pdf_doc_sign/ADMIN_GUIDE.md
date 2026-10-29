# SignSimple Platform — Administrator Guide

**One Platform, Two Applications:**
- **SignSimple** — PDF Document Signing (e-signatures)
- **Sales Tracker** — Daily Sales & Invoicing for Catering Businesses

Both apps share the same database, users, and organisations.

---

## Table of Contents

1. [Understanding the Two User Types](#understanding-the-two-user-types)
2. [Platform Setup Flow](#platform-setup-flow)
3. [Creating an Organisation (Catering Company)](#creating-an-organisation-catering-company)
4. [Adding Staff Members](#adding-staff-members)
5. [Setting Up Clients (Food Recipients)](#setting-up-clients-food-recipients)
6. [Client Portal Access](#client-portal-access)
7. [Daily Sales Workflow](#daily-sales-workflow)
8. [Invoice Generation](#invoice-generation)
9. [Dispute Handling](#dispute-handling)
10. [White-Label Branding](#white-label-branding)

---

## Understanding the Two User Types

There are **two different types of users** in the Sales Tracker:

### 1. Organisation Staff (You and Your Team)

| Who | What they do | Access |
|-----|--------------|--------|
| **Organisation Owner** | Created the company account | Full admin access |
| **Organisation Admin** | Manages users, clients, invoices | Admin panel + frontend |
| **Manager/Member** | Enters daily sales data | Frontend only |

**These users log in to manage and enter data.**

### 2. Clients (Companies Receiving Food)

| Who | What they do | Access |
|-----|--------------|--------|
| **Client (no login)** | Receives invoices by email | No login needed |
| **Client (with login)** | Views deliveries, raises disputes | Client portal (limited) |

**Clients are NOT the same as users — they are records of companies you deliver to.**

---

## Platform Setup Flow

Here's the recommended order for setting up:

```
1. Create Superuser (one-time, done during deployment)
      ↓
2. Create Organisation (your catering company)
      ↓
3. Add Branches (your kitchen locations)
      ↓
4. Add Staff Users (your team members)
      ↓
5. Add Clients (offices/companies you deliver to)
      ↓
6. Start Recording Daily Sales
```

---

## Creating an Organisation (Catering Company)

### What is an Organisation?

Your catering business = 1 Organisation in SignSimple.

**Example:**
- Organisation: "Praveen's Kitchen Pvt Ltd"
- Branches: "Bangalore Kitchen", "Hyderabad Kitchen"
- Clients: "TechCorp Office", "StartupXYZ", "BigBank Tower"

### Step-by-Step: Create Your Organisation

1. **Login to Admin Panel**
   - Go to: `https://signsimple.co.uk/admin/`
   - Use your superuser credentials

2. **Go to Organisations**
   - Click **"Organisations"** in the sidebar
   - Click **"Add Organisation"**

3. **Fill in Basic Details**

   | Field | What to Enter | Example |
   |-------|---------------|---------|
   | Name | Your company name | "Praveen's Kitchen Pvt Ltd" |
   | Slug | URL-friendly (auto-fills) | "praveens-kitchen" |
   | Owner | Select yourself | admin@example.com |
   | Status | Set to Active | "Active" |

4. **Fill in Company Details**
   - Company Number (CIN for India, Companies House for UK)
   - GST/VAT Number
   - Address, City, Postcode
   - Phone, Email

5. **Set Subscription** (for document signing limits)
   - Plan: FREE / STARTER / PROFESSIONAL
   - For Sales Tracker alone, FREE is fine

6. **Click "Save"**

### Adding Branches (Kitchen Locations)

If you have multiple kitchens:

1. Scroll down to **"Branches"** section in the Organisation form
2. Click **"Add another Branch"**
3. Enter:
   - Name: "Bangalore Kitchen"
   - Code: "BLR-01" (optional internal code)
   - City: "Bangalore"
4. Add more branches as needed
5. Click **"Save"**

---

## Adding Staff Members

### Who Needs a User Account?

| Person | Needs Account? | Role |
|--------|----------------|------|
| You (owner) | ✅ Yes | OWNER |
| Office manager | ✅ Yes | ADMIN |
| Kitchen supervisor | ✅ Yes | MANAGER |
| Data entry person | ✅ Yes | MEMBER |
| Client company | ❌ Usually no | (see Client Portal section) |

### Step-by-Step: Add a Staff Member

**Step 1: Create the User Account**

1. Go to **Admin → Authentication → Users**
2. Click **"Add User"**
3. Enter:
   - Email: `manager@praveenskitchen.com`
   - Password: (set a temporary password)
   - Full Name: "Ramesh Kumar"
   - Is Staff: ✅ Check if they need admin panel access
4. Click **"Save"**

**Step 2: Link User to Organisation**

1. Go to **Admin → Organisations → Organisation memberships**
2. Click **"Add Organisation membership"**
3. Enter:
   - User: Select "manager@praveenskitchen.com"
   - Organisation: Select "Praveen's Kitchen Pvt Ltd"
   - Branch: Select their kitchen (optional)
   - Role: Select "MANAGER"
   - Is Active: ✅ Check
4. Click **"Save"**

**Now this person can log in and enter daily sales.**

### Role Permissions

| Role | Can Enter Sales | Can Edit Others' Sales | Can Generate Invoices | Can Manage Users | Admin Panel |
|------|-----------------|------------------------|----------------------|------------------|-------------|
| OWNER | ✅ | ✅ | ✅ | ✅ | ✅ |
| ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ |
| MANAGER | ✅ | ✅ | ✅ | ❌ | Limited |
| MEMBER | ✅ | ❌ Own only | ❌ | ❌ | ❌ |
| VIEWER | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## Setting Up Clients (Food Recipients)

### What is a Client?

A **Client** is a company/office that receives food deliveries from you.

**Important:** A Client is NOT a user account. It's a record of who you deliver to.

### Step-by-Step: Add a Client

1. Go to **Admin → Sales → Clients**
2. Click **"Add Client"**
3. Fill in:

   | Field | What to Enter | Example |
   |-------|---------------|---------|
   | **Organisation** | Your company | "Praveen's Kitchen Pvt Ltd" |
   | **Branch** | Which kitchen serves them | "Bangalore Kitchen" |
   | **Name** | Client company name | "TechCorp Bangalore Office" |
   | **Contact Person** | Their admin/HR contact | "Priya Sharma" |
   | **Contact Email** | For invoices | "priya@techcorp.in" |
   | **Contact Phone** | For delivery issues | "+91 98765 43210" |
   | **City** | Their location | "Bangalore" |

4. **Set Pricing Model:**
   - **ITEMISED**: You list items + prices each day (most flexible)
   - **PER_HEAD**: Fixed rate × number of people
   - **FIXED**: Same amount every day

5. **Set Defaults:**
   - Default Num People: 50 (typical headcount)
   - Default Packing Charge: ₹100
   - Default Courier Charge: ₹200
   - Skip Weekends: ✅ (auto-mark Sat/Sun as holidays)

6. **Leave "User" blank** (for now — see Client Portal section below)

7. Click **"Save"**

---

## Client Portal Access

### Do Clients Need Login?

**Usually NO.** Most clients just:
- Receive invoices by email
- Pay via bank transfer
- Call you if there's an issue

### When to Give Client Login

Give login access if the client wants to:
- View their delivery history online
- Raise disputes through the system
- Download past invoices themselves

### Step-by-Step: Enable Client Portal

1. **Create a User Account for the Client**
   - Go to **Admin → Authentication → Users**
   - Add user: `priya@techcorp.in`
   - Set password (they can reset it later)
   - Is Staff: ❌ Unchecked (no admin access)

2. **Link User to Client Record**
   - Go to **Admin → Sales → Clients**
   - Find "TechCorp Bangalore Office"
   - In the **"User"** field, select `priya@techcorp.in`
   - Save

3. **Send Login Details**
   - Email the client their login URL and credentials
   - They can now log in and see ONLY their own deliveries

### What Can Clients See/Do?

| Feature | Client Access |
|---------|---------------|
| View their deliveries | ✅ Yes (their own only) |
| View delivery items & charges | ✅ Yes |
| Raise disputes | ✅ Yes |
| Edit daily sales | ❌ No (read-only) |
| See other clients | ❌ No |
| Access admin panel | ❌ No |
| Download invoices | ✅ Yes (their own only) |

---

## Daily Sales Workflow

### Option 1: Admin Panel (Full Access)

1. Go to **Admin → Sales → Daily sales**
2. Click **"Add Daily sale"**
3. Select Client, Date, enter details
4. Save

**Best for:** Admins, bulk data entry, corrections

### Option 2: Frontend App (Recommended for Daily Use)

1. Log in at `https://signsimple.co.uk/login`
2. Go to **Sales** in the sidebar
3. Select Client from dropdown
4. Select Date
5. Enter:
   - Number of people
   - Items delivered
   - Prices
6. Click **Save**

**Best for:** Kitchen supervisors, daily quick entry

### Recording a Holiday

**Method 1: Via Admin**
1. Daily sales → Add
2. Check "Is Holiday"
3. Enter reason: "Diwali" / "Sunday" / "Company Holiday"
4. Save (all charges will be ₹0)

**Method 2: Organisation-wide Holidays**
1. Go to **Admin → Sales → Holidays**
2. Add: Date, Name ("Diwali"), Organisation
3. Check "Applies to all clients"
4. These dates auto-show as holidays for all clients

---

## Invoice Generation

### Generate Invoice for a Client

1. Go to **Admin → Sales → Invoices**
2. Click **"Add Invoice"**
3. Select:
   - **Client:** TechCorp Bangalore Office
   - **From Date:** 2026-03-01
   - **To Date:** 2026-03-31
   - **Tax Percentage:** 18 (GST)
4. Click **"Save"**

### What Happens:

- Invoice number auto-generated (e.g., INV-2026-03-00001)
- All daily sales in that date range are summed up
- Holidays excluded (₹0 days skipped)
- Tax calculated
- PDF generated
- Daily sales marked as "Invoiced"

### Sending Invoice to Client

1. Open the invoice
2. Download PDF
3. Email to client's contact email
4. Or use the "Send Invoice" button (if email is configured)

---

## Dispute Handling

### When Client Raises an Issue

If a client calls about missing items or quality issues:

1. Go to **Admin → Sales → Disputes**
2. Click **"Add Dispute"**
3. Select:
   - **Daily Sale:** Find the specific date
   - **Dispute Type:** Missing Item / Quality Issue / etc.
   - **Description:** "2 Phulka missing from delivery"
4. Status: "Open"
5. Save

### Resolving Disputes

1. Investigate the issue
2. Open the dispute
3. Update Status: "Resolved" or "Rejected"
4. Add Resolution Notes: "Credit applied to next invoice"
5. Save

### Client-Raised Disputes (via Portal)

If client has portal access:
1. They log in
2. View their deliveries
3. Click "Raise Dispute" on a specific day
4. You receive notification
5. Resolve via admin panel

---

## White-Label Branding

### Set Your Company Logo & Colours

1. Go to **Admin → Organisations → [Your Org]**
2. In "White-Label Branding" section:
   - **Logo:** Upload your company logo (PNG, 200×50px recommended)
   - **Primary Colour:** Your brand colour (hex, e.g., `#1565c0`)
   - **Secondary Colour:** Accent colour

### Where Branding Appears

- ✅ Document signing pages
- ✅ Invoice PDFs
- ✅ Client portal
- ✅ Email templates

---

## Quick Reference: Admin URLs

| URL | Purpose |
|-----|---------|
| `/admin/` | Main admin dashboard |
| `/admin/authentication/user/` | Manage all users |
| `/admin/organisations/organisation/` | Manage organisations |
| `/admin/organisations/organisationmembership/` | Link users to orgs |
| `/admin/organisations/branch/` | Manage branches |
| `/admin/sales/client/` | Manage clients (food recipients) |
| `/admin/sales/dailysale/` | View/edit daily sales |
| `/admin/sales/invoice/` | Generate invoices |
| `/admin/sales/dispute/` | Handle disputes |
| `/admin/sales/holiday/` | Organisation holidays |

---

## Summary: Who Does What

| Person | Creates Account? | Role | What They Access |
|--------|------------------|------|------------------|
| **You (Owner)** | ✅ Superuser | OWNER | Everything |
| **Your Manager** | ✅ User + Membership | ADMIN/MANAGER | Admin + Frontend |
| **Your Data Entry Staff** | ✅ User + Membership | MEMBER | Frontend only |
| **Client (no portal)** | ❌ No account | — | Receives invoices by email |
| **Client (with portal)** | ✅ User + linked to Client | — | Client portal (read-only) |

---

## Need Help?

- **Email:** support@avyangah.co.uk
- **Website:** https://signsimple.co.uk

---

*SignSimple — Operated by Avyangah Technologies Limited (Company #08235853)*
