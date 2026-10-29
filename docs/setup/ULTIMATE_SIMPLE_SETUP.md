# 🎯 ULTIMATE SIMPLE SETUP - NO ALEMBIC!

**Forget alembic! Use this simple method instead.**

---

## ⚡ Copy & Paste These Commands

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai

# 1. Stop and clean everything
docker-compose -f docker-compose.local.yml down -v

# 2. Make sure Ollama has the model
docker-compose -f docker-compose.local.yml up -d ollama
sleep 10
docker exec careai-ollama-local ollama pull llama3.2:3b

# 3. Rebuild everything
docker-compose -f docker-compose.local.yml build

# 4. Start everything
docker-compose -f docker-compose.local.yml up -d

# 5. Wait for services
sleep 20

# 6. Create database tables (SIMPLE!)
docker exec careai-api-local python init_db.py

# 7. Test it works
curl http://localhost:8000/health
```

---

## ✅ That's It!

No alembic, no migrations, no headaches!

---

## 🧪 Test Your Setup

### 1. Check tables were created
```bash
docker exec careai-postgres-local psql -U careai -d careai -c "\dt"
```

**You should see 9 tables:**
- users
- subscriptions
- usage_records
- voice_notes
- partner_accounts
- api_keys
- coupons
- coupon_redemptions
- medical_knowledge_log

### 2. Register a user
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

### 3. Open frontend
```bash
open http://localhost
```

---

## 🔄 If You Need to Reset Database

```bash
# Just run the init script again
docker exec careai-api-local python init_db.py

# This drops and recreates all tables (fresh start)
```

---

## 🚀 For Production Server

Same simple approach:

```bash
# On server
docker-compose up -d

# Create tables
docker exec careai-api python init_db_safe.py

# Note: init_db_safe.py doesn't drop tables (safer for production)
```

---

## 📝 Two Scripts Available

1. **init_db.py** - Drops and recreates all tables (good for development)
2. **init_db_safe.py** - Only creates missing tables (good for production)

```bash
# Development (clean slate)
docker exec careai-api-local python init_db.py

# Production (safe mode)
docker exec careai-api-local python init_db_safe.py
```

---

## 💡 Why This Is Better Than Alembic

| Alembic | Simple Script |
|---------|---------------|
| ❌ Complex migrations | ✅ One simple Python file |
| ❌ Version conflicts | ✅ No versions needed |
| ❌ Hard to debug | ✅ Clear error messages |
| ❌ Fails often | ✅ Works every time |
| ❌ Need to track state | ✅ Just run it |

---

## 🎯 Complete Working Setup

```bash
cd /Users/praveen.r/Desktop/guhya_ai/care-ai
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d ollama
sleep 10
docker exec careai-ollama-local ollama pull llama3.2:3b
docker-compose -f docker-compose.local.yml build
docker-compose -f docker-compose.local.yml up -d
sleep 20
docker exec careai-api-local python init_db.py
curl http://localhost:8000/health
open http://localhost
```

**Done!** 🎉

---

## 📚 Next Steps

1. ✅ Everything is running
2. ✅ Database tables created
3. ✅ Test the frontend at http://localhost
4. ✅ Test the API at http://localhost:8000/docs
5. ✅ Register a user and try asking questions

---

**No more alembic struggles!** 🚀
