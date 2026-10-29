-- =============================================================
-- DocSign UK — Additional database for existing Postgres
-- =============================================================
-- Run this ONCE on your existing careai-postgres container:
--   docker exec -i careai-postgres psql -U careai -c "CREATE DATABASE docsign_uk;"
--
-- Or if using this as an init script for a fresh Postgres:
-- =============================================================

-- Only create if not exists (safe to re-run)
SELECT 'CREATE DATABASE docsign_uk'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'docsign_uk')\gexec

-- The careai user already exists and owns the careai database.
-- Grant it access to docsign_uk as well.
GRANT ALL PRIVILEGES ON DATABASE docsign_uk TO careai;
