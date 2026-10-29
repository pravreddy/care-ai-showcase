# SignSimple Sales Tracker — Complete User Guide

## For Catering & Food Delivery Businesses

The Sales Tracker helps you:
- Record daily food deliveries to clients
- Track items, headcount, and charges
- Handle holidays and disputes
- Generate monthly invoices with GST

---

## Table of Contents

1. [Understanding the Data Model](#understanding-the-data-model)
2. [Initial Setup](#initial-setup)
3. [Adding Clients](#adding-clients)
4. [Recording Daily Sales](#recording-daily-sales)
5. [Handling Holidays](#handling-holidays)
6. [Managing Disputes](#managing-disputes)
7. [Generating Invoices](#generating-invoices)
8. [Reports & Analytics](#reports--analytics)
9. [Client Portal (Optional)](#client-portal)
10. [Tips & Best Practices](#tips--best-practices)

---

## Understanding the Data Model

```
Organisation (Your Catering Company)
    │
    ├── Branch (Kitchen Location)
    │       │
    │       └── Client (Company receiving food)
    │               │
    │               ├── DailySale (One record per day)
    │               │       ├── Date
    │               │       ├── Items delivered
    │               │       ├── Number of people
    │               │       ├── Item price
    │               │       ├── Packing charges
    │               │       ├── Courier charges
    │               │       └── Total
    │               │
    │               ├── Invoice (Monthly summary)
    │               │
    │               └── Dispute (If client reports issue)
    │
    └── Holiday (Organisation-wide holidays like Diwali)
```

---

## Initial Setup

### Step 1: Create Your Organisation

1. Go to: **https://signsimple.co.uk/admin/**
2. Login with your admin credentials
3. Click **"Organisations"** → **"Add Organisation"**
4. Fill in:
   - **Name:** Your company name (e.g., "Praveen's Kitchen Pvt Ltd")
   - **Slug:** Auto-generated URL-friendly name
   - **Owner:** Select yourself
   - **Company Details:** GST number, address, etc.
5. Click **"Save"**

### Step 2: Add Branches (Kitchen Locations)

If you have multiple kitchens:

1. Go to **"Organisations"** → Click your organisation
2. Scroll to **"Branches"** section
3. Click **"Add another Branch"**
4. Enter:
   - **Name:** "Bangalore Kitchen"
   - **Code:** "BLR-01"
   - **Address/City:** Kitchen location
5. Add more branches as needed
6. Click **"Save"**

---

## Adding Clients

A **Client** is a company/office that receives food deliveries from you.

### Step-by-Step

1. Go to: **Admin → Sales → Clients**
2. Click **"Add Client"**
3. Fill in the form:

### Basic Information

| Field | Description | Example |
|-------|-------------|---------|
| **Organisation** | Your company | "Praveen's Kitchen Pvt Ltd" |
| **Branch** | Which kitchen serves them | "Bangalore Kitchen" |
| **Name** | Client company name | "TechCorp Bangalore" |
| **Contact Person** | Their admin/HR | "Priya Sharma" |
| **Contact Email** | For invoices | "priya@techcorp.in" |
| **Contact Phone** | For delivery issues | "+91 98765 43210" |
| **Address** | Delivery address | "123 Tech Park, Whitefield" |
| **City** | City | "Bangalore" |

### Pricing Model

Choose how you charge this client:

| Model | How It Works | Use When |
|-------|--------------|----------|
| **ITEMISED** | List items + prices each day | Most flexible, different items daily |
| **PER_HEAD** | Fixed rate × number of people | Same menu, variable headcount |
| **FIXED** | Same amount every day | Fixed contract |

### Default Values

Set defaults to speed up daily entry:

| Field | Description | Example |
|-------|-------------|---------|
| **Default Num People** | Typical headcount | 50 |
| **Default Packing Charge** | Standard packing fee | ₹100 |
| **Default Courier Charge** | Standard delivery fee | ₹200 |
| **Skip Weekends** | Auto-mark Sat/Sun as holidays | ✅ Yes |

### Pricing Details (for PER_HEAD or FIXED models)

| Field | Description | Example |
|-------|-------------|---------|
| **Fixed Daily Rate** | For FIXED pricing | ₹5000 |
| **Per Head Rate** | For PER_HEAD pricing | ₹120 |

4. Click **"Save"**

---

## Recording Daily Sales

### Method 1: Admin Panel

1. Go to: **Admin → Sales → Daily sales**
2. Click **"Add Daily sale"**
3. Fill in:

| Field | What to Enter | Example |
|-------|---------------|---------|
| **Client** | Select client | "TechCorp Bangalore" |
| **Date** | Delivery date | 2026-03-26 |
| **Is Holiday** | Was it a holiday? | ❌ No |
| **Num People** | Headcount served | 48 |
| **Items Description** | What was delivered | "5 Chapathi, 10 Phulka, 9 Aloo Matar..." |
| **Item Price** | Price per person | ₹230 |
| **Food Price Per Day** | Auto-calculated (or enter manually) | ₹11,040 |
| **Packing Charges** | Packing fee | ₹100 |
| **Courier Charges** | Delivery fee | ₹200 |
| **Total Charge** | Auto-calculated | ₹11,340 |

4. Click **"Save"**

### Method 2: Frontend App (Coming Soon)

The frontend will have a quick-entry form at: `https://signsimple.co.uk/sales`

### Auto-Calculation Logic

```
If num_people > 0 AND item_price > 0:
    food_price_per_day = item_price × num_people

total_charge = food_price_per_day 
             + packing_charges 
             + courier_charges 
             + other_charges 
             - discount
```

### Example Daily Entry

**Scenario:** TechCorp ordered lunch for 48 people on March 26, 2026.

| Field | Value |
|-------|-------|
| Client | TechCorp Bangalore |
| Date | 2026-03-26 |
| Is Holiday | No |
| Num People | 48 |
| Items | "5 Chapathi, 10 Phulka, 9 Aloo Matar Gravy, 9 half rice, 6 dal fry" |
| Item Price | ₹230 |
| Food Price | ₹11,040 (48 × 230) |
| Packing | ₹100 |
| Courier | ₹200 |
| **Total** | **₹11,340** |

---

## Handling Holidays

### Option 1: Mark Individual Day as Holiday

1. Go to **Daily Sales → Add**
2. Select Client and Date
3. Check **"Is Holiday"** ✅
4. Enter **Holiday Reason:** "Sunday" or "Diwali"
5. Save

**Result:** All charges automatically set to ₹0.

### Option 2: Organisation-Wide Holidays

For holidays that apply to ALL clients (like Diwali):

1. Go to: **Admin → Sales → Holidays**
2. Click **"Add Holiday"**
3. Enter:
   - **Organisation:** Your company
   - **Date:** 2026-10-20
   - **Name:** "Diwali"
   - **Applies to all clients:** ✅ Yes
4. Save

### Option 3: Client-Specific Holidays

If only one client is closed:

1. Go to **Holidays → Add**
2. Set **"Applies to all clients":** ❌ No
3. Select **"Specific client":** TechCorp Bangalore
4. Save

### Weekend Handling

If a client has **"Skip Weekends"** enabled:
- Saturdays and Sundays are automatically treated as holidays
- You don't need to manually mark them

---

## Managing Disputes

When a client reports an issue with a delivery:

### Creating a Dispute

1. Go to: **Admin → Sales → Disputes**
2. Click **"Add Dispute"**
3. Fill in:

| Field | Description | Example |
|-------|-------------|---------|
| **Daily Sale** | Which day's delivery | TechCorp — 2026-03-26 |
| **Raised By** | Who reported it | (Select user or leave blank) |
| **Dispute Type** | Category of issue | Missing Item |
| **Description** | Details | "2 Phulka missing from delivery" |
| **Photo** | Evidence (optional) | Upload image |

4. Click **"Save"**

### Dispute Types

| Type | Use When |
|------|----------|
| **MISSING_ITEM** | Item was not delivered |
| **WRONG_ITEM** | Wrong item delivered |
| **QUALITY** | Food quality issue |
| **QUANTITY** | Less quantity than ordered |
| **OVERCHARGE** | Billed more than delivered |
| **OTHER** | Any other issue |

### Dispute Statuses

| Status | Meaning |
|--------|---------|
| **OPEN** | New dispute, needs attention |
| **ACKNOWLEDGED** | You're looking into it |
| **RESOLVED** | Issue fixed |
| **REJECTED** | Dispute not valid |

### Resolving a Dispute

1. Open the dispute
2. Change **Status** to "Resolved" or "Rejected"
3. Add **Resolution Notes:** "Credit of ₹50 applied to next invoice"
4. Save

The daily sale status automatically updates from "Disputed" to "Confirmed".

---

## Generating Invoices

### Step-by-Step

1. Go to: **Admin → Sales → Invoices**
2. Click **"Add Invoice"**
3. Fill in:

| Field | Description | Example |
|-------|-------------|---------|
| **Client** | Which client | TechCorp Bangalore |
| **From Date** | Billing period start | 2026-03-01 |
| **To Date** | Billing period end | 2026-03-31 |
| **Tax Percentage** | GST rate | 18 |

4. Click **"Save"**

### What Happens Automatically

- **Invoice Number** generated: `INV-2026-03-00001`
- **Working Days** counted (excludes holidays)
- **Totals** calculated from all daily sales in the period:
  - Total Food
  - Total Packing
  - Total Courier
  - Total Other
  - Total Discount
  - Subtotal
  - Tax Amount
  - **Grand Total**
- Daily sales marked as **"Invoiced"**

### Invoice Fields Explained

| Field | Description |
|-------|-------------|
| **Invoice Number** | Auto-generated: `INV-YYYY-MM-NNNNN` |
| **Working Days** | Number of non-holiday days |
| **Total Food** | Sum of food_price_per_day |
| **Total Packing** | Sum of packing_charges |
| **Total Courier** | Sum of courier_charges |
| **Subtotal** | Sum of total_charge |
| **Tax Amount** | Subtotal × Tax% |
| **Grand Total** | Subtotal + Tax |

### Example Invoice

**TechCorp Bangalore — March 2026**

| Metric | Value |
|--------|-------|
| Working Days | 22 |
| Total Food | ₹2,42,880 |
| Total Packing | ₹2,200 |
| Total Courier | ₹4,400 |
| Subtotal | ₹2,49,480 |
| GST (18%) | ₹44,906 |
| **Grand Total** | **₹2,94,386** |

### Invoice Status

| Status | Meaning |
|--------|---------|
| **DRAFT** | Not yet sent |
| **SENT** | Emailed to client |
| **PAID** | Payment received |
| **OVERDUE** | Past due date |
| **CANCELLED** | Voided |

---

## Reports & Analytics

### Daily Sales List View

Go to: **Admin → Sales → Daily sales**

Use filters to see:
- Sales by client
- Sales by date range
- Sales by status (Draft/Confirmed/Disputed/Invoiced)

### Quick Stats (via Django Shell)

```python
from sales.models import DailySale, Invoice
from django.db.models import Sum

# Total sales this month
DailySale.objects.filter(
    date__month=3, 
    date__year=2026,
    is_holiday=False
).aggregate(total=Sum('total_charge'))

# Unpaid invoices
Invoice.objects.filter(status='SENT').aggregate(total=Sum('grand_total'))
```

---

## Client Portal

### When to Enable

Give clients login access if they want to:
- View their delivery history
- Check daily items and charges
- Raise disputes online
- Download past invoices

### Setup Steps

1. **Create User Account**
   - Admin → Authentication → Users → Add
   - Email: `priya@techcorp.in`
   - Is Staff: ❌ No (no admin access)

2. **Link to Client**
   - Admin → Sales → Clients → TechCorp
   - Set **"User"** field to `priya@techcorp.in`
   - Save

3. **Share Login URL**
   - Send: `https://signsimple.co.uk/login`
   - Client logs in and sees only their data

### What Clients Can Do

| Action | Allowed? |
|--------|----------|
| View their deliveries | ✅ Yes |
| See items & charges | ✅ Yes |
| Raise disputes | ✅ Yes |
| Download invoices | ✅ Yes |
| Edit daily sales | ❌ No |
| See other clients | ❌ No |

---

## Tips & Best Practices

### Daily Workflow

1. **End of each day:** Enter today's deliveries (takes 30 seconds per client)
2. **Don't batch:** Enter daily to avoid forgetting details
3. **Use defaults:** Set up default charges per client to speed up entry

### Monthly Workflow

1. **1st of month:** Generate invoices for previous month
2. **Review:** Check for any missed entries or disputes
3. **Send:** Email invoices to clients
4. **Track:** Update status when paid

### Handling Common Scenarios

**Scenario 1: Client was closed unexpectedly**
- Go to that day's entry
- Check "Is Holiday"
- Add reason: "Client office closed"

**Scenario 2: Partial delivery (half the usual)**
- Enter actual num_people served
- Total auto-calculates correctly

**Scenario 3: Extra items requested**
- Add to "Items Description"
- Adjust item_price or add to other_charges

**Scenario 4: Client disputes after invoice sent**
- Create dispute for the specific day
- Resolve and note: "Credit in next invoice"
- Adjust next month's invoice accordingly

### Data Entry Tips

- **Items Description:** Be specific enough to resolve disputes
  - ❌ Bad: "Lunch"
  - ✅ Good: "5 Chapathi, 10 Phulka, 9 Aloo Matar, 9 rice, 6 dal"

- **Use Line Items (optional):** For detailed per-item pricing:
  - Go to Daily Sale → Line Items section
  - Add: "8 Veg Biryani @ ₹230 = ₹1,840"

---

## Quick Reference: Admin URLs

| URL | Purpose |
|-----|---------|
| `/admin/sales/client/` | Manage clients |
| `/admin/sales/dailysale/` | Daily sales entry |
| `/admin/sales/invoice/` | Generate invoices |
| `/admin/sales/dispute/` | Handle disputes |
| `/admin/sales/holiday/` | Organisation holidays |
| `/admin/organisations/organisation/` | Your company settings |
| `/admin/organisations/branch/` | Kitchen locations |

---

## Keyboard Shortcuts (Admin Panel)

| Action | Shortcut |
|--------|----------|
| Save | `Ctrl + S` |
| Save and add another | `Ctrl + Shift + S` |
| Search | `/` |

---

## Need Help?

- **Email:** support@avyangah.co.uk
- **Admin Guide:** See ADMIN_GUIDE.md

---

*SignSimple Sales Tracker — Operated by Avyangah Technologies Limited*
