#!/bin/bash

# Care AI Database Management Script
# Usage: ./manage_db.sh [command]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

DB_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai"
TEST_DB_URL="postgresql+asyncpg://careai:careai_secret@localhost:5432/careai_test"

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if alembic is installed
check_alembic() {
    if ! command -v alembic &> /dev/null; then
        echo_error "Alembic is not installed. Install it with: pip install alembic"
        exit 1
    fi
}

# Create migration
create_migration() {
    check_alembic
    if [ -z "$1" ]; then
        echo_error "Please provide a migration message"
        echo "Usage: ./manage_db.sh create 'your migration message'"
        exit 1
    fi
    
    echo_info "Creating new migration: $1"
    alembic revision --autogenerate -m "$1"
    echo_info "Migration created successfully!"
}

# Run migrations
upgrade() {
    check_alembic
    echo_info "Running database migrations..."
    alembic upgrade head
    echo_info "Migrations completed successfully!"
}

# Downgrade one revision
downgrade() {
    check_alembic
    echo_warning "Downgrading database by one revision..."
    alembic downgrade -1
    echo_info "Downgrade completed!"
}

# Show current revision
current() {
    check_alembic
    echo_info "Current database revision:"
    alembic current
}

# Show migration history
history() {
    check_alembic
    echo_info "Migration history:"
    alembic history
}

# Reset database (drop and recreate)
reset() {
    check_alembic
    echo_warning "This will DROP all tables and recreate them!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo_info "Downgrading to base..."
        alembic downgrade base
        echo_info "Upgrading to head..."
        alembic upgrade head
        echo_info "Database reset complete!"
    else
        echo_info "Reset cancelled"
    fi
}

# Create test database
create_test_db() {
    echo_info "Creating test database..."
    PGPASSWORD=careai_secret psql -h localhost -U careai -d postgres -c "DROP DATABASE IF EXISTS careai_test;"
    PGPASSWORD=careai_secret psql -h localhost -U careai -d postgres -c "CREATE DATABASE careai_test;"
    echo_info "Test database created!"
}

# Setup test database with migrations
setup_test_db() {
    create_test_db
    echo_info "Running migrations on test database..."
    DATABASE_URL=$TEST_DB_URL alembic upgrade head
    echo_info "Test database ready!"
}

# Show help
show_help() {
    cat << EOF
Care AI Database Management Script

Usage: ./manage_db.sh [command] [options]

Commands:
    create <message>    Create a new migration with the given message
    upgrade            Apply all pending migrations
    downgrade          Downgrade by one revision
    current            Show current database revision
    history            Show migration history
    reset              Reset database (drop all tables and recreate)
    test-db            Create and setup test database
    help               Show this help message

Examples:
    ./manage_db.sh create "add user preferences table"
    ./manage_db.sh upgrade
    ./manage_db.sh current
    ./manage_db.sh test-db

EOF
}

# Main command handler
case "${1:-help}" in
    create)
        create_migration "$2"
        ;;
    upgrade)
        upgrade
        ;;
    downgrade)
        downgrade
        ;;
    current)
        current
        ;;
    history)
        history
        ;;
    reset)
        reset
        ;;
    test-db)
        setup_test_db
        ;;
    help)
        show_help
        ;;
    *)
        echo_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
