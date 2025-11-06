#!/bin/bash

DB_NAME="${DB_NAME:-banking_system}"
DB_USER="${DB_USER:-banking_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

if [ -z "$DB_PASSWORD" ]; then
    echo "PostgreSQL password not set. Please enter password for user '$DB_USER':"
    read -s DB_PASSWORD
    echo ""
fi

echo "Setting up PostgreSQL database for Banking System..."

sudo -u postgres psql << EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE ${DB_USER} SET client_encoding TO 'utf8';
ALTER ROLE ${DB_USER} SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${DB_USER} SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
EOF

echo "PostgreSQL database '${DB_NAME}' created successfully"
echo ""
echo "Database credentials:"
echo "  Database: ${DB_NAME}"
echo "  User: ${DB_USER}"
echo "  Host: ${DB_HOST}"
echo "  Port: ${DB_PORT}"
echo ""
echo "Set these environment variables before running Django:"
echo "  export DB_NAME='${DB_NAME}'"
echo "  export DB_USER='${DB_USER}'"
echo "  export DB_PASSWORD='your_password'"
echo "  export DB_HOST='${DB_HOST}'"
echo "  export DB_PORT='${DB_PORT}'"
echo ""
echo "You can now run: python manage.py migrate"
