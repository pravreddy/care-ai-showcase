# Database Migrations - Quick Reference

## 🚨 Fixing the Current Production Issue

Your production database is missing the `is_admin` column. Here's how to fix it:

### Quick Fix (Run this now)

```bash
cd care_ai_engine

# Make the script executable
chmod +x scripts/fix_database.sh

# Run the fix
./scripts/fix_database.sh
```

This will apply the migration that adds the missing `is_admin` column.

### Manual Fix (if script doesn't work)

1. Connect to your production database:
```bash
psql -h localhost -U careai -d careai
```

2. Add the missing column:
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
```

3. Verify:
```sql
\d users  -- Should show is_admin column
```

## Understanding the Issue

The error you saw:
```
sqlalchemy.exc.ProgrammingError: column users.is_admin does not exist
```

This happened because:
1. Your code (Python model) expects an `is_admin` column
2. Your database table doesn't have this column
3. Migrations were never run to sync the database with the code

## Database Management Commands

### Run Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply one migration at a time
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade <revision_id>
```

### Check Status
```bash
# Show current database version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

### Create New Migrations
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration (for manual SQL)
alembic revision -m "description of changes"
```

### Rollback
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all (dangerous!)
alembic downgrade base
```

### Reset Database (Development Only)
```bash
./scripts/manage_db.sh reset
```

## Migration Workflow

### When You Change Database Models

1. **Update your model** (e.g., `app/models/database.py`)
   ```python
   class User(Base):
       # ... existing fields ...
       new_field = Column(String(100), nullable=True)
   ```

2. **Create migration**
   ```bash
   alembic revision --autogenerate -m "add new_field to users"
   ```

3. **Review the generated migration**
   ```bash
   # Check the file in alembic/versions/
   cat alembic/versions/xxxx_add_new_field_to_users.py
   ```

4. **Test migration**
   ```bash
   # On development database
   alembic upgrade head
   ```

5. **Apply to production**
   ```bash
   # SSH to production server
   cd /path/to/care_ai_engine
   alembic upgrade head
   ```

## Production Deployment Checklist

Before deploying code changes that affect the database:

- [ ] Create migration locally
- [ ] Test migration on development database
- [ ] Review migration SQL
- [ ] Backup production database
- [ ] Run migration on production
- [ ] Verify migration succeeded
- [ ] Deploy code changes
- [ ] Monitor for errors

## Common Issues

### "Target database is not up to date"
**Solution**: Run `alembic upgrade head`

### "Can't locate revision identified by 'xxxx'"
**Solution**: Check that all migration files are present in `alembic/versions/`

### "Duplicate column name"
**Solution**: The migration was partially applied. Either:
- Rollback: `alembic downgrade -1`
- Or manually fix the database and mark migration as complete

### Migration fails halfway
**Solution**: 
1. Check database state
2. Fix manually if needed
3. Use `alembic stamp <revision>` to mark as complete

## Testing Migrations

Always test migrations before production:

```bash
# Create test database
./scripts/manage_db.sh test-db

# Test upgrade
DATABASE_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test" \
  alembic upgrade head

# Test downgrade
DATABASE_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test" \
  alembic downgrade -1

# Test upgrade again
DATABASE_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test" \
  alembic upgrade head
```

## Best Practices

1. **Always review auto-generated migrations** - Alembic isn't perfect
2. **Test migrations before production** - Use test database
3. **Backup before migrating production** - Always!
4. **Keep migrations small** - One logical change per migration
5. **Don't edit old migrations** - Create new ones to fix issues
6. **Version control migrations** - Commit them to git
7. **Document complex migrations** - Add comments explaining what and why

## Emergency Rollback

If a migration breaks production:

```bash
# 1. Rollback the migration
alembic downgrade -1

# 2. Restart the application with old code
docker-compose restart careai-api

# 3. Investigate the issue
# 4. Fix and test properly
# 5. Try again
```

## Getting Help

If you're stuck:

1. Check current database state: `alembic current`
2. Check migration history: `alembic history --verbose`
3. Look at the database: `psql -h localhost -U careai -d careai`
4. Check migration file: `cat alembic/versions/xxxx_*.py`

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Database Migration Best Practices](https://www.braintreepayments.com/blog/safe-database-migration/)
