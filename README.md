# 🏥 Care AI - AI-Powered Medical Knowledge Engine

**AI-powered medical knowledge platform for UK care workers**  
**£10/month subscription** — Live NHS data • Local LLM • GDPR-compliant

---

## 🚀 Quick Start

```bash
cd care-ai
docker-compose -f docker-compose.local.yml up -d
docker exec careai-api-local alembic upgrade head
```

**That's it!** Open http://localhost

📖 **Detailed setup:** See [docs/setup/FINAL_CLEAN_SETUP.md](docs/setup/FINAL_CLEAN_SETUP.md)

---

## 📚 Documentation

All documentation is organized in the **[docs/](docs/)** folder:

| Type | Link | Description |
|------|------|-------------|
| **📖 Docs Index** | **[docs/README.md](docs/README.md)** | ⭐ Navigation hub |
| 🚀 Setup | [docs/setup/](docs/setup/) | Installation guides |
| 🐛 Troubleshooting | [docs/troubleshooting/](docs/troubleshooting/) | Common issues |
| 📘 Guides | [docs/guides/](docs/guides/) | Detailed references |

### Popular Docs

- **[Quick Start](docs/setup/QUICK_START.md)** - 5-minute setup
- **[Final Clean Setup](docs/setup/FINAL_CLEAN_SETUP.md)** - Complete guide ⭐
- **[Production Deploy](docs/setup/PRODUCTION_DEPLOY.md)** - Server deployment
- **[Complete Working Guide](docs/guides/COMPLETE_WORKING_GUIDE.md)** - All commands

---

## 🎯 What is Care AI?

Care AI is a **medical AI assistant** for UK care workers that:

✅ **Fetches live data** from NHS.uk (always current)  
✅ **Runs locally** on your server (private LLM with Ollama)  
✅ **No data scraping** needed (MCP architecture)  
✅ **UK GDPR compliant** (data never leaves your server)

### Architecture

```
User Question
    │
    ▼
Frontend (React) → Backend (FastAPI) → MCP Client
                                          │
                                          ├─→ NHS.uk (live)
                                          ├─→ OpenPrescribing (live)
                                          └─→ Ollama LLM (local)
    │
    ▼
Answer + NHS Sources
```

**Key Innovation:** MCP (Model Context Protocol) fetches data live instead of pre-scraping!

---

## 🏗️ Project Structure

```
care-ai/
├── README.md                       # This file
├── docs/                           # 📚 All documentation
│   ├── setup/                      # Setup guides
│   ├── troubleshooting/            # Problem solutions
│   └── guides/                     # References
├── care_ai_engine/                 # 🔧 Backend (FastAPI + Python)
│   ├── app/                        # Application code
│   │   ├── api/                    # API routes
│   │   ├── services/               # Business logic
│   │   ├── models/                 # Database models
│   │   └── mcp/                    # MCP servers & client
│   ├── tests/                      # Test suite
│   ├── alembic/                    # Database migrations
│   └── README.md                   # Backend docs
├── care_ai_frontend/               # 🎨 Frontend (React + Vite)
│   ├── src/                        # React components
│   │   ├── pages/                  # Page components
│   │   ├── components/             # Reusable components
│   │   └── services/               # API client
│   └── README.md                   # Frontend docs
├── docker-compose.local.yml        # Local development
├── docker-compose.yml              # Production (pulls from GitHub)
└── deploy/                         # Deployment configs
```

---

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with PostgreSQL
- **Alembic** - Database migrations
- **Redis** - Caching
- **Ollama** - Local LLM (Llama 3.2)
- **MCP** - Model Context Protocol for live data

### Frontend
- **React 18** - UI library
- **Vite 6** - Build tool & dev server
- **React Router 6** - Routing
- **Lucide React** - Icons
- **NHS Design System** - Styling

### Infrastructure
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **PostgreSQL 16** - Database
- **Redis 7** - Cache

---

## 🎯 Features

### For Care Workers
✅ Ask medical questions in plain English  
✅ Get answers with NHS sources  
✅ Voice note transcription  
✅ Clinical note generation  
✅ 2FA security  
✅ 3-month free trial

### For Developers
✅ RESTful API with OpenAPI docs  
✅ MCP-powered architecture (extensible)  
✅ Comprehensive test suite  
✅ Docker-based deployment  
✅ Alembic migrations  
✅ JWT authentication

### For Partners
✅ API access with keys  
✅ Coupon system  
✅ Usage tracking  
✅ Partner dashboard

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- 16GB RAM (for Ollama LLM)
- Git

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/care-ai.git
cd care-ai

# 2. One-command setup
cd care-ai && \
docker-compose -f docker-compose.local.yml down -v && \
docker-compose -f docker-compose.local.yml up -d ollama && \
sleep 10 && \
docker exec careai-ollama-local ollama pull llama3.2:3b && \
docker-compose -f docker-compose.local.yml build && \
docker-compose -f docker-compose.local.yml up -d && \
sleep 20 && \
docker exec careai-api-local alembic upgrade head && \
curl http://localhost:8000/health
```

### Access Your App

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

📖 **Detailed guide:** [docs/setup/FINAL_CLEAN_SETUP.md](docs/setup/FINAL_CLEAN_SETUP.md)

---

## 🧪 Testing

```bash
# Backend tests
docker exec careai-api-local pytest

# With coverage
docker exec careai-api-local pytest --cov=app --cov-report=html

# Health check
curl http://localhost:8000/health
```

📖 **Testing guide:** See care_ai_engine/TESTING.md

---

## 🚀 Production Deployment

```bash
# On server
cd care-ai
docker-compose pull
docker-compose up -d
docker exec careai-api alembic upgrade head
```

📖 **Full guide:** [docs/setup/PRODUCTION_DEPLOY.md](docs/setup/PRODUCTION_DEPLOY.md)

---

## 📖 API Documentation

### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "User Name"
}

# Login
POST /api/v1/auth/login
{
  "username": "user@example.com",
  "password": "SecurePass123!"
}
```

### Medical AI

```bash
# Ask question
POST /api/v1/agent/ask
Authorization: Bearer <token>
{
  "question": "What is paracetamol used for?"
}

# Response
{
  "answer": "Paracetamol is used to treat...",
  "sources": [
    {
      "source": "NHS Medicines",
      "url": "https://www.nhs.uk/medicines/paracetamol/",
      "type": "live"
    }
  ]
}
```

### Interactive Docs

Open http://localhost:8000/docs for full interactive API documentation.

---

## 🔗 Useful Links

- **Backend Docs**: [care_ai_engine/README.md](care_ai_engine/README.md)
- **Frontend Docs**: [care_ai_frontend/README.md](care_ai_frontend/README.md)
- **All Documentation**: [docs/README.md](docs/README.md)
- **Setup Guide**: [docs/setup/FINAL_CLEAN_SETUP.md](docs/setup/FINAL_CLEAN_SETUP.md)
- **Troubleshooting**: [docs/troubleshooting/](docs/troubleshooting/)

---

## 🐛 Troubleshooting

Common issues and solutions are in [docs/troubleshooting/](docs/troubleshooting/):

- [Database Connection Issues](docs/troubleshooting/FIX_DATABASE_CONNECTION.md)
- [Migration Errors](docs/troubleshooting/FIX_MIGRATION_ERROR.md)
- [Database Setup Problems](docs/troubleshooting/SIMPLE_DATABASE_SETUP.md)

### Quick Fixes

```bash
# View logs
docker-compose -f docker-compose.local.yml logs -f

# Restart service
docker-compose -f docker-compose.local.yml restart api

# Clean restart
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

📖 **Testing guide:** [docs/guides/MISSING_TESTS_ANALYSIS.md](docs/guides/MISSING_TESTS_ANALYSIS.md)

---

## 📝 License

Proprietary — Care AI Ltd.

---

## 📞 Support

- **Documentation**: [docs/README.md](docs/README.md)
- **Issues**: GitHub Issues
- **Health Check**: `curl http://localhost:8000/health`

---

## ✅ Quick Checklist

Before deploying:
- [ ] Tested locally
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Can register/login
- [ ] Can ask questions
- [ ] Database migrations run successfully
- [ ] All tests pass: `pytest`
- [ ] Read [Production Deploy Guide](docs/setup/PRODUCTION_DEPLOY.md)

---

**Built with ❤️ for UK care workers**

🚀 **Get started:** [docs/setup/FINAL_CLEAN_SETUP.md](docs/setup/FINAL_CLEAN_SETUP.md)
