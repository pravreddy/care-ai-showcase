-- =============================================================
-- Create separate databases for each app
-- Runs once on first PostgreSQL startup
-- =============================================================

-- Care AI database
CREATE DATABASE careai;

-- SignSimple (DocSign) database
CREATE DATABASE docsign_uk;

-- Postal messaging database (for the Django messaging app)
CREATE DATABASE postal_messaging;

-- Grant permissions to the shared user
GRANT ALL PRIVILEGES ON DATABASE careai TO avyangah;
GRANT ALL PRIVILEGES ON DATABASE docsign_uk TO avyangah;
GRANT ALL PRIVILEGES ON DATABASE postal_messaging TO avyangah;
