# Care AI Engine

**AI-powered medical knowledge engine for UK care workers.**  
**£10/month** — Live NHS data, local LLM, UK GDPR-compliant.

---

## 📚 Table of Contents

- [Understanding MCP vs RAG](#understanding-mcp-vs-rag)
- [How It Works](#how-it-works-mcp-architecture)
- [Local Development Setup](#local-development-setup)
- [Production Deployment](#production-deployment)
- [API Documentation](#api-endpoints)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🎓 Understanding MCP vs RAG

### Quick Answer
**MCP ≠ Memory | RAG ≠ Research**

- **MCP** = Model Context Protocol (HOW we fetch data)
- **RAG** = Retrieval Augmented Generation (WHAT we do with data)
- **Your app uses BOTH** - MCP enhances RAG

### MCP (Model Context Protocol)

MCP is like **USB ports for AI** - a standard way to connect data sources:

```
Traditional approach:
AI Model → Hard-coded to specific databases

MCP approach:
AI Model → MCP Client → Can connect to ANY MCP server
                         ├─ NHS Server (medicines, conditions)
                         ├─ BNF Server (prescribing data)
                         └─ More servers easily added
```

**What MCP provides:**
- ✅ Live data fetching (always current)
- ✅ Zero maintenance (no scraping jobs)
- ✅ Modular architecture (add sources easily)
- ✅ Automatic caching (fast responses)

### RAG (Retrieval Augmented Generation)

RAG is a **3-step process** for AI answers:

```
1. RETRIEVE  → Fetch relevant information (using MCP!)
2. AUGMENT   → Add that info to the AI prompt
3. GENERATE  → AI answers using retrieved info
```

### How They Work Together

```
USER: "What are side effects of Amlodipine?"
  │
  ▼
┌─────────────────────────────────────────┐
│   RAG PROCESS                           │
│                                         │
│  1️⃣ RETRIEVE (using MCP)               │
│     ├─ MCP Client: Call NHS server     │
│     ├─ NHS Server: Fetch live from NHS │
│     └─ Returns: Current NHS data       │
│                                         │
│  2️⃣ AUGMENT (Build Prompt)             │
│     Combine: NHS data + Question        │
│                                         │
│  3️⃣ GENERATE (LLM Answer)              │
│     Ollama: Answer using NHS data       │
└─────────────────────────────────────────┘
  │
  ▼
ANSWER: "Common side effects include..."
```

### Traditional RAG vs MCP-Enhanced RAG

| Feature | Traditional RAG | MCP-Enhanced RAG |
|---------|----------------|------------------|
| **Setup Time** | 8-12 hours (scraping) | 5 minutes (deploy server) |
| **Data Freshness** | 1-7 days old | Real-time (seconds old) |
| **Storage** | 5-10 GB (ChromaDB) | ~100 MB (cache only) |
| **Maintenance** | Weekly scraping jobs | Zero (auto-updates) |
| **Adding Sources** | New scraper + DB | Just add .py file |
| **Query Time (first)** | 300ms | 2s (network call) |
| **Query Time (cached)** | 300ms | 200ms |

**Bottom Line:** MCP makes RAG faster to set up, always current, and easier to maintain.

---

## How It Works (MCP Architecture)

```
   User Question
        │
        ▼
  ┌───────────┐         ┌──────────────────┐
  │  FastAPI   │────────▶│   MCP Client     │
  │  (+ JWT)   │         │                  │
  └───────────┘         └────────┬─────────┘
        ▲                        │
        │                        │  Calls MCP tools
        │                        ▼
        │               ┌──────────────────┐
        │               │  NHS MCP Server  │──── LIVE ───▶ NHS.uk
        │               │  (4 tools)       │──── LIVE ───▶ OpenPrescribing
        │               └──────────────────┘
        │
        │  NHS context + question
        ▼
  ┌───────────┐
  │   Ollama   │  ← Local LLM (Llama 3.2)
  │  (Private) │  ← No data leaves your server
  └───────────┘
        │
        ▼
   Answer + NHS source URLs
```

### MCP Tools Available

| Tool | What It Does | Example |
|------|-------------|---------|
| `get_medicine_info` | Fetch live medicine details from NHS.uk | "Get Amlodipine info" |
| `get_condition_info` | Fetch live condition details from NHS.uk | "Get diabetes info" |
| `search_nhs` | Search NHS.uk for any medical topic | "Search for hypertension" |
| `get_bnf_info` | Search British National Formulary | "Search paracetamol BNF" |

---

## 🚀 Local Development Setup

### Prerequisites

- **Docker Desktop** (Mac/Windows) or **Docker + Docker Compose** (Linux)
- **16GB RAM minimum** (for Ollama LLM)
- **Git**
- **PostgreSQL** (or use Docker)
- **Redis** (or use Docker)

### Step 1: Clone and Navigate

```bash
# Clone the repository
git clone https://github.com/your-org/care-ai.git
cd care-ai/care_ai_engine
```

### Step 2: Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Important `.env` variables:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://careai:careai_secret@localhost:5432/careai

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# JWT Secret (generate a random string)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Environment
ENVIRONMENT=development
DEBUG=true

# CORS (for local frontend development)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 3: Install Dependencies

#### Option A: Using Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, API, Ollama)
docker-compose up -d

# Check logs
docker-compose logs -f careai-api

# Pull LLM model (this takes a few minutes)
docker-compose exec ollama ollama pull llama3.2:3b
```

#### Option B: Local Python Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (if not using Docker)
# Install via Homebrew (Mac) or apt (Linux)
brew services start postgresql@15

# Start Redis
brew services start redis
```

### Step 4: Database Setup

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run database migrations
./scripts/fix_database.sh

# Or manually:
alembic upgrade head
```

### Step 5: Verify Installation

```bash
# Test database connection
alembic current

# Test Redis connection
redis-cli ping  # Should return: PONG

# If using Docker Compose:
docker-compose ps  # All services should be "Up"
```

### Step 6: Start the Application

#### Using Docker Compose:

```bash
# Already started in Step 3, just verify:
curl http://localhost:8000/health
```

#### Using Local Python:

```bash
# Activate virtual environment
source venv/bin/activate

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Ollama (if not using Docker)
ollama serve
ollama pull llama3.2:3b
```

### Step 7: Test the API

```bash
# Health check
curl http://localhost:8000/health

# Should return:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ollama": "running",
    "mcp_nhs": "available"
  }
}

# Register a test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User",
    "organisation": "Test Org"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "Test123!"
  }'

# Copy the access_token from the response

# Ask a medical question
curl -X POST http://localhost:8000/api/agent/ask \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is paracetamol used for?"
  }'
```

---

## 🧪 Testing

### Setup Test Environment

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Create test database
./scripts/manage_db.sh test-db

# Or manually:
createdb careai_test
DATABASE_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test" \
  alembic upgrade head
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific tests
pytest tests/unit/test_auth_service.py
pytest tests/integration/test_auth_endpoints.py

# View coverage report
open htmlcov/index.html  # Mac
# or
xdg-open htmlcov/index.html  # Linux
```

### Test Structure

```
tests/
├── conftest.py              # Test fixtures
├── unit/                    # Unit tests
│   └── test_auth_service.py
└── integration/             # Integration tests
    └── test_auth_endpoints.py
```

**For detailed testing guide, see:** [TESTING.md](TESTING.md)

---

## 🔧 Troubleshooting Local Development

### Common Issues

#### 1. "Database does not exist"

```bash
# Create database
createdb careai

# Or using psql
psql -U postgres
CREATE DATABASE careai;
\q

# Run migrations
alembic upgrade head
```

#### 2. "Cannot connect to Redis"

```bash
# Check if Redis is running
redis-cli ping

# If not, start Redis
# Mac:
brew services start redis

# Linux:
sudo systemctl start redis

# Docker:
docker-compose up -d redis
```

#### 3. "Ollama not found"

```bash
# Using Docker Compose:
docker-compose up -d ollama
docker-compose exec ollama ollama pull llama3.2:3b

# Using local Ollama:
# Install from https://ollama.ai
ollama serve
ollama pull llama3.2:3b
```

#### 4. "Port already in use"

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

#### 5. "Import errors"

```bash
# Make sure you're in the right directory
cd care_ai_engine

# Set Python path
export PYTHONPATH=$PWD

# Reinstall dependencies
pip install -r requirements.txt
```

#### 6. "Column does not exist" errors

```bash
# This means migrations haven't been run
./scripts/fix_database.sh

# Or manually
alembic upgrade head
```

#### 7. "MCP tools not working"

```bash
# Check NHS website is accessible
curl -I https://www.nhs.uk

# Check MCP server is loaded
curl http://localhost:8000/api/agent/mcp/tools

# Check logs for errors
docker-compose logs careai-api
# or
tail -f logs/app.log
```

#### 8. "Tests failing"

```bash
# Recreate test database
./scripts/manage_db.sh test-db

# Check test database connection
psql -U careai -d careai_test -c "SELECT 1;"

# Run with verbose output
pytest -vv

# Run specific failing test
pytest tests/unit/test_auth_service.py::TestAuthService::test_register_user_success -vv
```

---

## 🐳 Docker Compose Services

```yaml
services:
  careai-api:      # FastAPI application
  postgres:        # PostgreSQL database
  redis:           # Redis cache
  ollama:          # Local LLM server
```

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f careai-api

# Restart a service
docker-compose restart careai-api

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build

# Access database
docker-compose exec postgres psql -U careai -d careai

# Access Redis CLI
docker-compose exec redis redis-cli

# Check Ollama models
docker-compose exec ollama ollama list
```

---

## 📋 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register (3-month free trial) |
| POST | `/api/auth/login` | Login, get JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Current user profile |

### Medical Agent (MCP-Powered)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/agent/ask` | Ask a medical question (live NHS data + LLM) |
| POST | `/api/agent/mcp/call` | Call MCP tool directly (raw NHS data) |
| GET | `/api/agent/mcp/tools` | List available MCP tools |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Full health check (MCP + Ollama + NHS) |
| GET | `/ping` | Liveness probe |

### Example: Ask a Question

```bash
curl -X POST http://localhost:8000/api/agent/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the side effects of Amlodipine?"}'
```

```json
{
  "answer": "Common side effects of Amlodipine include...",
  "sources": [
    {
      "source": "NHS Medicines",
      "name": "Amlodipine",
      "url": "https://www.nhs.uk/medicines/amlodipine/",
      "type": "live"
    }
  ],
  "confidence": "high",
  "model_used": "llama3.2:3b",
  "tools_used": ["search_nhs"],
  "data_freshness": "live"
}
```

---

## 📁 Project Structure

```
care_ai_engine/
├── app/
│   ├── api/                        # API routes
│   │   ├── auth_routes.py          # JWT auth endpoints
│   │   ├── agent_routes.py         # Medical AI + MCP endpoints
│   │   ├── notes_routes.py         # Voice notes
│   │   ├── partner_routes.py       # Partner API
│   │   ├── coupon_routes.py        # Coupon system
│   │   └── health_routes.py        # Health checks
│   ├── core/                       # Infrastructure
│   │   ├── config.py               # Environment-based settings
│   │   ├── database.py             # Async PostgreSQL
│   │   └── logging.py              # JSON structured logging
│   ├── mcp/                        # ★ MCP Architecture
│   │   ├── servers/
│   │   │   └── nhs_server.py       # NHS MCP server (4 tools)
│   │   └── client/
│   │       └── mcp_client.py       # MCP client (routes tool calls)
│   ├── middleware/
│   │   └── auth.py                 # JWT dependency
│   ├── models/
│   │   ├── database.py             # SQLAlchemy ORM
│   │   └── schemas.py              # Pydantic models
│   ├── services/
│   │   ├── auth_service.py         # Auth logic
│   │   ├── llm_service.py          # Ollama client
│   │   ├── medical_agent.py        # ★ MCP-powered RAG pipeline
│   │   ├── cache_service.py        # Redis caching
│   │   ├── totp_service.py         # 2FA
│   │   └── security_service.py     # Security utilities
│   └── main.py                     # App factory
├── alembic/                        # Database migrations
│   └── versions/
│       └── 001_initial_schema.py
├── tests/                          # Test suite
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── scripts/                        # Management scripts
│   ├── fix_database.sh
│   ├── manage_db.sh
│   └── setup_tests.sh
├── config/
│   └── nginx.conf.example          # Production reverse proxy
├── docker-compose.yml              # Full stack
├── Dockerfile                      # Production image
├── requirements.txt                # Production dependencies
├── requirements-test.txt           # Test dependencies
├── pytest.ini                      # Test configuration
└── .env.example                    # Environment template
```

---

## 🚀 Production Deployment

See [deploy/README.md](../deploy/README.md) for production deployment guide.

Quick deploy:

```bash
cd deploy
chmod +x server-setup.sh
./server-setup.sh
```

---

## 📚 Additional Documentation

- **[TESTING.md](TESTING.md)** - Complete testing guide
- **[DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md)** - Migration management
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and diagrams
- **[INDEX.md](INDEX.md)** - Documentation navigation guide

---

## 🔐 Security Notes

- ✅ JWT authentication with access/refresh tokens
- ✅ Password hashing with bcrypt
- ✅ 2FA support (TOTP)
- ✅ Rate limiting via Redis
- ✅ CORS configuration
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (ORM)
- ✅ No data leaves your server (local LLM)

---

## 🎯 Adding New Data Sources

The MCP architecture makes this trivial. Want to add NICE guidelines, CQC data, or MHRA alerts?

1. Create a new MCP server file:
```python
# app/mcp/servers/nice_server.py
TOOLS = [
    {
        "name": "get_nice_guideline",
        "description": "Fetch NICE clinical guidelines",
        "inputSchema": { ... }
    }
]

async def handle_tool_call(tool_name, arguments):
    # Fetch live from NICE API
    ...
```

2. Register it in the MCP client:
```python
# app/mcp/client/mcp_client.py
from app.mcp.servers.nice_server import TOOLS as NICE_TOOLS
```

That's it. No database migrations. No scraping jobs. No ChromaDB reindexing.

---

## 📊 Performance Tips

### Caching Strategy

```python
# MCP responses are cached in Redis
# Default TTL: 1 hour for NHS data

# To adjust cache TTL:
await cache_service.set(
    key=f"mcp:{tool_name}:{hash(arguments)}",
    value=result,
    ttl=3600  # seconds
)
```

### Database Connection Pool

```python
# config.py
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 10
```

### LLM Performance

```bash
# Use smaller model for faster responses
OLLAMA_MODEL=llama3.2:1b  # Faster, less accurate

# Use larger model for better quality
OLLAMA_MODEL=llama3.2:3b  # Balanced (recommended)
OLLAMA_MODEL=llama3.1:8b  # Slower, more accurate
```

---

## 💡 Development Tips

### Auto-reload

```bash
# FastAPI auto-reloads on code changes
uvicorn app.main:app --reload
```

### Debug Logging

```bash
# Enable debug logging
DEBUG=true python -m uvicorn app.main:app --reload
```

### Database GUI

```bash
# Use pgAdmin or DBeaver to browse the database
# Connection details from .env file
```

### API Testing

```bash
# Use the interactive API docs
open http://localhost:8000/docs

# Or Redoc
open http://localhost:8000/redoc
```

---

## 🆘 Getting Help

1. **Check documentation** in this folder
2. **Run health check**: `curl http://localhost:8000/health`
3. **Check logs**: `docker-compose logs -f` or `tail -f logs/app.log`
4. **Run tests**: `pytest -vv`
5. **Check database**: `alembic current`

---

## 📝 License

Proprietary — Care AI Ltd.

---

## 🎉 Quick Start Checklist

- [ ] Clone repository
- [ ] Copy `.env.example` to `.env`
- [ ] Start Docker Compose: `docker-compose up -d`
- [ ] Pull LLM model: `docker-compose exec ollama ollama pull llama3.2:3b`
- [ ] Run migrations: `./scripts/fix_database.sh`
- [ ] Test health: `curl http://localhost:8000/health`
- [ ] Register test user
- [ ] Ask a question
- [ ] Run tests: `pytest`
- [ ] Read [TESTING.md](TESTING.md)

**Welcome to Care AI! 🚀**
