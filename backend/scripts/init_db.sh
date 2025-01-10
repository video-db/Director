#!/bin/bash
# scripts/init_db.sh

# Get database type from environment variable, default to sqlite
DB_TYPE=${DB_TYPE:-sqlite}

if [ "$DB_TYPE" = "sqlite" ]; then
    echo "Initializing SQLite database..."
    [ ! -f director.db ] && python director/db/sqlite/initialize.py || echo "SQLite database already initialized."
elif [ "$DB_TYPE" = "postgres" ]; then
    echo "Initializing PostgreSQL database..."
    python director/db/postgres/initialize.py
else
    echo "Unknown database type: $DB_TYPE"
    exit 1
fi