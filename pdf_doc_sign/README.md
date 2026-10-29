# SignSimple UK

**Free PDF Document Signing + Daily Sales & Invoicing Platform**

Operated by Avyangah Technologies Limited (Company #08235853).

---

## 📚 Documentation

| Guide | Audience | Description |
|-------|----------|-------------|
| [ADMIN_GUIDE.md](ADMIN_GUIDE.md) | Administrators | Setting up organisations, users, roles, managing the platform |
| [USER_GUIDE.md](USER_GUIDE.md) | End Users | Sign documents, basic sales entry, manage account |
| [SALES_APP_GUIDE.md](SALES_APP_GUIDE.md) | Catering Businesses | **Complete guide** for daily sales, clients, invoices, disputes |
| [deploy/DEPLOY_GUIDE.md](deploy/DEPLOY_GUIDE.md) | DevOps | Production deployment instructions |

---

## Quick Start (Local Development)

```bash
cd pdf_doc_sign

# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker compose up -d --build

# Apply database migrations
docker compose exec backend python manage.py migrate

# Create admin user
docker compose exec backend python manage.py createsuperuser

# Open in browser
# Frontend:  http://localhost:3001
# Backend:   http://localhost:8001
# Admin:     http://localhost:8001/admin/
```

---

## Running Tests

### Backend (Django + pytest)

```bash
# Run all backend tests
docker compose exec backend pytest

# Run with verbose output
docker compose exec backend pytest -v --tb=short

# Run a specific test file
docker compose exec backend pytest tests/test_sales.py -v

# Run a single test
docker compose exec backend pytest tests/test_sales.py::TestClientModel::test_create_client -v
```

### Frontend (React + Jest)

```bash
# Run all frontend tests
docker compose exec frontend npx react-scripts test --watchAll=false --ci

# Run tests in watch mode (interactive, for development)
docker compose exec frontend npx react-scripts test

# Run with coverage report
docker compose exec frontend npx react-scripts test --watchAll=false --ci --coverage
```

### Lint (Frontend)

```bash
# react-scripts build in CI mode treats ESLint warnings as errors
# This catches unused imports, undefined variables, etc.
cd frontend && CI=true npx react-scripts build
```

---

## Database Migrations

```bash
# Check current migration status
docker compose exec backend python manage.py showmigrations

# Create new migration after model changes (dry run first!)
docker compose exec backend python manage.py makemigrations --dry-run
docker compose exec backend python manage.py makemigrations

# Apply migrations
docker compose exec backend python manage.py migrate

# Check no migrations are missing (CI uses this)
docker compose exec backend python manage.py migrate --check
```

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/deploy.yml`) runs on every push to `main`:

1. **Detect changes** — only builds/tests what actually changed
2. **Build Docker images** — backend and frontend, pushed to GHCR
3. **Backend tests** (if backend changed) — migrations, system check, full pytest suite
4. **Frontend tests** (if frontend changed) — ESLint via build, Jest test suite
5. **Deploy** — blue-green deployment to production (only if all tests pass)

| What changed | Backend tests | Frontend tests | Deploy |
|---|---|---|---|
| Backend only | ✅ runs | ⏭️ skipped | ✅ if tests pass |
| Frontend only | ⏭️ skipped | ✅ runs | ✅ if tests pass |
| Both | ✅ runs | ✅ runs | ✅ if both pass |
| Deploy config only | ⏭️ skipped | ⏭️ skipped | ✅ deploys |

---

## Features

### 📝 Document Signing (SignSimple)
- Upload PDF → add signers → send for signature
- Legally binding under UK law (Electronic Communications Act 2000)
- 10 free documents/month, from £2.50/month for 100 docs

### 📊 Daily Sales & Invoicing (Sales Tracker)
- Daily food/catering delivery tracking per client
- Spreadsheet-like entry — one row per day
- Auto-calculates: item_price × people = food cost
- Client dispute system (missing items, quality issues)
- PDF invoice generation with GST/VAT support
- Email invoices directly to clients

### 🏢 Multi-Tenant White-Label
- Organisation → Branch → Client hierarchy
- Custom logos, colours, domains per organisation
- Role-based access: Owner, Admin, Manager, Member, Viewer

---

## Pricing (GBP)

| Plan         | Price     | Documents/Month |
|-------------|-----------|-----------------|
| Free        | £0        | 10              |
| Starter     | £2.50     | 100             |
| Professional| £10       | 1,000           |

**Pay-as-you-go:** £1 per extra 100 documents.

---

## Email Configuration

SignSimple uses **Brevo (formerly Sendinblue)** for transactional emails:

```bash
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-brevo-login
EMAIL_HOST_PASSWORD=xkeysib-your-key
DEFAULT_FROM_EMAIL=SignSimple <noreply@signsimple.co.uk>
```

---

## OAuth Login (5 providers)

| Provider | Setup URL |
|----------|-----------|
| Google | console.cloud.google.com |
| GitHub | github.com/settings/developers |
| Microsoft | portal.azure.com |
| LinkedIn | linkedin.com/developers |

Add credentials to `.env` — login buttons activate automatically.

---

## Project Structure

```
pdf_doc_sign/
├── backend/                    Django 4.2 + DRF
│   ├── authentication/         User, OAuth (5 providers), JWT, email activation
│   ├── core/                   Settings, URLs, WSGI
│   ├── documents/              Document, Signer, AuditLog, Template
│   │   ├── models/             Split: document, signer, fields, audit, template
│   │   ├── views/              Split: document_viewset, public_signing, templates
│   │   ├── services/           PDF generation, signing orchestrator, bulk send
│   │   └── emails/             Notification emails
│   ├── organisations/          Multi-tenant: Org, Branch, Membership, Invitations
│   │   └── middleware.py       TenantMiddleware (auto-injects request.org)
│   ├── sales/                  Daily sales, clients, disputes, invoices, holidays
│   │   └── services/           Invoice PDF generation
│   ├── payments/               TrueLayer + Stripe integration
│   ├── subscriptions/          Plans, billing (GBP)
│   └── tests/                  Backend test suite (pytest)
├── frontend/                   React 18 + Material UI 6
│   └── src/
│       ├── components/
│       │   ├── Auth/           Login, Register, OAuth, SetPassword
│       │   ├── Common/         Layout (sidebar + org selector), PrivateRoute
│       │   ├── Dashboard/      Dashboard overview
│       │   ├── Documents/      Upload, Prepare, Documents list
│       │   ├── DocumentView/   Document detail (split into 8 components)
│       │   ├── Help/           9 public help pages + FAQ
│       │   ├── Landing/        SEO landing page + free sign tool
│       │   ├── Sales/          Daily entry, Invoice generator, Clients, Disputes
│       │   ├── Signing/        Public signing page (no login needed)
│       │   └── Templates/      Document templates library
│       ├── services/           API client (axios + org header injection)
│       ├── hooks/              Custom hooks (useSigningLogic, useUpload)
│       ├── utils/              Error handling, signature utilities
│       └── __tests__/          Frontend test suite (Jest)
├── deploy/                     Production deployment files
├── .github/workflows/          CI/CD pipeline
├── ADMIN_GUIDE.md              Administrator documentation
├── USER_GUIDE.md               User documentation
├── SALES_APP_GUIDE.md          Sales Tracker documentation
└── docker-compose.yml          Local development
```

---

## Admin Panel Quick Reference

| URL Path | Purpose |
|----------|---------|
| `/admin/` | Django Admin (superuser access) |
| `/admin/authentication/user/` | Manage users |
| `/admin/organisations/organisation/` | Manage organisations |
| `/admin/organisations/organisationmembership/` | Assign users to organisations |
| `/admin/sales/client/` | Manage delivery clients |
| `/admin/sales/dailysale/` | View/edit daily sales |
| `/admin/sales/invoice/` | Generate and manage invoices |

---

## Tech Stack

- **Backend:** Django 4.2, Django REST Framework, SimpleJWT, django-allauth
- **Frontend:** React 18, Material UI 6, React Router
- **Database:** PostgreSQL 16
- **Cache/Queue:** Redis 7, Celery
- **Email:** Brevo SMTP (transactional)
- **PDF Generation:** ReportLab
- **Storage:** S3-compatible (optional)
- **Deploy:** Docker Compose, Nginx, Blue-Green deployment

---

## Support

- **Email:** support@avyangah.co.uk
- **Website:** https://signsimple.co.uk

---

*SignSimple — Simple, Secure, Legally Binding*

*Electronic signatures are legally valid under UK law (Electronic Communications Act 2000)*
