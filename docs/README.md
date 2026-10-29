# 📚 Care AI Documentation

**Organized documentation for Care AI project**

---

## 🚀 Quick Links

- **[README.md](../README.md)** - Start here! Main project documentation
- **[Quick Start](setup/QUICK_START.md)** - Get running in 5 minutes
- **[Final Clean Setup](setup/FINAL_CLEAN_SETUP.md)** - Complete clean installation

---

## 📖 Documentation Structure

```
docs/
├── setup/                  # Installation & deployment guides
├── troubleshooting/        # Common problems & solutions
└── guides/                 # Detailed guides & references
```

---

## 🔧 Setup & Installation

| Document | Description | Time | For |
|----------|-------------|------|-----|
| **[Quick Start](setup/QUICK_START.md)** | Fastest way to get started | 5 min | First-time users |
| **[Final Clean Setup](setup/FINAL_CLEAN_SETUP.md)** | Step-by-step clean installation | 15 min | ⭐ Recommended |
| **[Simple Docker](setup/SIMPLE_DOCKER.md)** | Basic Docker commands | 2 min | Quick reference |
| **[Docker Build Guide](setup/DOCKER_BUILD_GUIDE.md)** | Detailed Docker setup | 20 min | Advanced users |
| **[Ultimate Simple Setup](setup/ULTIMATE_SIMPLE_SETUP.md)** | One-command setup | 1 min | Quick deploy |
| **[Production Deploy](setup/PRODUCTION_DEPLOY.md)** | Production server setup | 30 min | Production |

---

## 🐛 Troubleshooting

| Document | Problem | Solution |
|----------|---------|----------|
| **[Fix Database Connection](troubleshooting/FIX_DATABASE_CONNECTION.md)** | Database connection errors | Database URL fix |
| **[Fix Migration Error](troubleshooting/FIX_MIGRATION_ERROR.md)** | Alembic migration failures | Migration troubleshooting |
| **[Simple Database Setup](troubleshooting/SIMPLE_DATABASE_SETUP.md)** | Database setup issues | Alternative setup methods |

---

## 📘 Guides & References

| Document | Topic | Details |
|----------|-------|---------|
| **[Complete Working Guide](guides/COMPLETE_WORKING_GUIDE.md)** | Full reference | All commands & workflows |
| **[Missing Tests Analysis](guides/MISSING_TESTS_ANALYSIS.md)** | Testing coverage | What tests are missing |

---

## 🎯 What Should I Read?

### I'm brand new here
1. Read [README.md](../README.md)
2. Follow [Final Clean Setup](setup/FINAL_CLEAN_SETUP.md)
3. Test with examples from [Quick Start](setup/QUICK_START.md)

### I have an error
1. Check [Troubleshooting](#-troubleshooting) section
2. Look at logs: `docker-compose logs -f`
3. See [Complete Working Guide](guides/COMPLETE_WORKING_GUIDE.md)

### I want to deploy to production
1. Test locally first with [Final Clean Setup](setup/FINAL_CLEAN_SETUP.md)
2. Follow [Production Deploy](setup/PRODUCTION_DEPLOY.md)
3. Setup monitoring and backups

### I want to contribute
1. Read [README.md](../README.md)
2. Check [Missing Tests Analysis](guides/MISSING_TESTS_ANALYSIS.md)
3. Follow coding standards in backend/frontend READMEs

---

## 📂 Project Structure

```
care-ai/
├── README.md                    # ⭐ Start here
├── docs/                        # All documentation
│   ├── setup/                   # Setup guides
│   ├── troubleshooting/         # Problem solutions
│   └── guides/                  # Detailed guides
├── care_ai_engine/              # Backend (FastAPI)
│   └── README.md                # Backend docs
├── care_ai_frontend/            # Frontend (React)
│   └── README.md                # Frontend docs
└── docker-compose.local.yml     # Local development
```

---

## 🔗 Quick Commands

### Local Development
```bash
# Start everything
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Stop
docker-compose -f docker-compose.local.yml down
```

### Production
```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Testing
```bash
# Backend tests
docker exec careai-api-local pytest

# Health check
curl http://localhost:8000/health
```

---

## 📞 Need Help?

1. **Check documentation** in this folder
2. **View logs**: `docker-compose logs -f`
3. **Health check**: `curl http://localhost:8000/health`
4. **Common errors**: See [Troubleshooting](#-troubleshooting)

---

## 🎓 Learning Path

**Day 1: Setup**
- [ ] Read [README.md](../README.md)
- [ ] Follow [Final Clean Setup](setup/FINAL_CLEAN_SETUP.md)
- [ ] Test health endpoint

**Day 2: Understand**
- [ ] Read [Complete Working Guide](guides/COMPLETE_WORKING_GUIDE.md)
- [ ] Explore API docs at http://localhost:8000/docs
- [ ] Try registering and asking questions

**Day 3: Deploy**
- [ ] Test thoroughly locally
- [ ] Follow [Production Deploy](setup/PRODUCTION_DEPLOY.md)
- [ ] Setup monitoring

**Week 2: Contribute**
- [ ] Read [Missing Tests Analysis](guides/MISSING_TESTS_ANALYSIS.md)
- [ ] Write tests for features you use
- [ ] Submit pull requests

---

## ✅ Documentation Checklist

Before deploying:
- [ ] Read main [README.md](../README.md)
- [ ] Completed [Final Clean Setup](setup/FINAL_CLEAN_SETUP.md)
- [ ] Tested locally
- [ ] Health check passes
- [ ] Can register/login
- [ ] Can ask questions
- [ ] Reviewed [Production Deploy](setup/PRODUCTION_DEPLOY.md)

---

**Happy coding!** 🚀
