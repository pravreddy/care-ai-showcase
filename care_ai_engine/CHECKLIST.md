# Testing & Database Fix Checklist

## 🚨 IMMEDIATE ACTION (Fix Production)

- [ ] Navigate to project: `cd /Users/praveen.r/Desktop/guhya_ai/care-ai/care_ai_engine`
- [ ] Make scripts executable: `chmod +x scripts/*.sh`
- [ ] Run fix: `./scripts/fix_database.sh`
- [ ] Test registration: Try creating a user via API
- [ ] Check logs: `docker logs careai-api --tail 50`
- [ ] Verify: Registration should now work without errors

**Estimated Time:** 2 minutes

---

## 📦 SETUP (First Time Only)

- [ ] Install test dependencies: `pip install -r requirements-test.txt`
- [ ] Create test database: `./scripts/manage_db.sh test-db`
- [ ] Run tests to verify: `pytest`
- [ ] Check coverage: `pytest --cov=app --cov-report=html`
- [ ] Open coverage report: `open htmlcov/index.html`

**Estimated Time:** 5 minutes

---

## 📚 LEARN THE SYSTEM

- [ ] Read `README_START_HERE.md` (5 min)
- [ ] Read `TESTING.md` (10 min)
- [ ] Read `DATABASE_MIGRATIONS.md` (10 min)
- [ ] Review test examples in `tests/` directory
- [ ] Understand fixtures in `tests/conftest.py`

**Estimated Time:** 30 minutes

---

## 🧪 DAILY DEVELOPMENT WORKFLOW

For each feature/fix:

- [ ] Pull latest code: `git pull`
- [ ] Create branch: `git checkout -b feature/my-feature`
- [ ] Write failing test first
- [ ] Implement the feature
- [ ] Run tests: `pytest`
- [ ] Fix any failures
- [ ] Run tests again until they pass
- [ ] Check coverage: `pytest --cov=app`
- [ ] Commit: `git commit -m "Add feature with tests"`
- [ ] Push: `git push`

**Estimated Time:** 5 minutes per feature (excluding implementation)

---

## 🗄️ DATABASE CHANGES

When you modify models:

- [ ] Update model in `app/models/database.py`
- [ ] Create migration: `alembic revision --autogenerate -m "description"`
- [ ] Review generated migration file
- [ ] Test on dev database: `alembic upgrade head`
- [ ] Run tests: `pytest`
- [ ] Test downgrade: `alembic downgrade -1`
- [ ] Test upgrade again: `alembic upgrade head`
- [ ] Commit migration file
- [ ] Apply to production: `alembic upgrade head`

**Estimated Time:** 10 minutes

---

## 🚀 PRE-DEPLOYMENT CHECKLIST

Before deploying to production:

- [ ] All tests pass locally: `pytest`
- [ ] Coverage is acceptable: `pytest --cov=app`
- [ ] No uncommitted changes: `git status`
- [ ] Migrations reviewed: `alembic history`
- [ ] Backup production database
- [ ] Apply migrations: `alembic upgrade head`
- [ ] Deploy code
- [ ] Check production logs
- [ ] Test critical paths
- [ ] Monitor for 15 minutes

**Estimated Time:** 20 minutes

---

## 🆘 TROUBLESHOOTING

### Tests Won't Run

- [ ] Check you're in correct directory: `pwd`
- [ ] Verify test dependencies: `pip list | grep pytest`
- [ ] Check test database: `psql -h localhost -U careai -l | grep careai_test`
- [ ] Recreate test database: `./scripts/manage_db.sh test-db`
- [ ] Check Python path: `export PYTHONPATH=$PWD`

### Migration Fails

- [ ] Check current revision: `alembic current`
- [ ] Check pending migrations: `alembic history`
- [ ] Check database connection: `psql -h localhost -U careai -d careai`
- [ ] Review migration file
- [ ] Check for conflicts: Look at table structure with `\d tablename`
- [ ] Manual fix if needed
- [ ] Mark as applied: `alembic stamp <revision>`

### Production Issues

- [ ] Check logs: `docker logs careai-api --tail 100`
- [ ] Check database state: `alembic current`
- [ ] Verify migrations: `alembic history`
- [ ] Check database connection
- [ ] Rollback if needed: `alembic downgrade -1`
- [ ] Apply fix
- [ ] Restart service: `docker-compose restart careai-api`
- [ ] Monitor logs

---

## 📊 WEEKLY MAINTENANCE

Every week:

- [ ] Run full test suite: `pytest`
- [ ] Check coverage trends: `pytest --cov=app`
- [ ] Review failing tests
- [ ] Update test dependencies if needed
- [ ] Review and clean up old migrations (if > 50)
- [ ] Backup test database
- [ ] Review test performance (should be < 30 seconds)

**Estimated Time:** 15 minutes

---

## 🎯 COVERAGE GOALS

Track your progress:

### Current Status (After Setup)
- [ ] Auth Service: ~100%
- [ ] Auth Endpoints: ~95%
- [ ] Overall: ~94%

### Short Term Goals (This Month)
- [ ] Add tests for voice notes service
- [ ] Add tests for partner routes
- [ ] Add tests for coupon service
- [ ] Target: 80% overall coverage

### Long Term Goals (Next 3 Months)
- [ ] 90% overall coverage
- [ ] All critical paths at 95%+
- [ ] Integration tests for all endpoints
- [ ] Performance tests
- [ ] Security tests

---

## 📝 NOTES & REMINDERS

### Remember
- ✅ Tests are not optional - they save time
- ✅ Write tests before fixing bugs
- ✅ Run tests before every commit
- ✅ Never skip migrations
- ✅ Always backup before production migrations

### Quick Reference
```bash
# Most used commands
pytest                          # Run all tests
pytest --cov=app               # With coverage
alembic upgrade head           # Apply migrations
alembic current                # Check version
./scripts/manage_db.sh test-db # Reset test DB
```

### Emergency Contacts
- Database issues: Check `DATABASE_MIGRATIONS.md`
- Test issues: Check `TESTING.md`
- General setup: Check `README_START_HERE.md`

---

## ✅ COMPLETION STATUS

### Immediate (Today)
- [ ] Production fixed
- [ ] Tests installed and running
- [ ] Documentation read

### This Week
- [ ] Tests integrated into workflow
- [ ] Pre-commit hook added
- [ ] Team trained on testing

### This Month
- [ ] CI/CD pipeline with tests
- [ ] 80% code coverage achieved
- [ ] All critical paths tested

---

## 📈 SUCCESS METRICS

Track these over time:

- **Test Count:** Start: 17 → Target: 50+
- **Coverage:** Start: 94% → Target: 85%+
- **Test Speed:** Target: < 30 seconds
- **Production Issues:** Target: Zero database issues
- **Deployment Confidence:** Target: 100%

---

**Last Updated:** February 12, 2026
**Next Review:** Check this weekly and update as needed

---

## 🎉 You're Ready!

You now have:
- ✅ Fixed production database
- ✅ Complete test infrastructure
- ✅ Management scripts
- ✅ Comprehensive documentation
- ✅ Clear workflow

**Start here:** `README_START_HERE.md`

Good luck! 🚀
