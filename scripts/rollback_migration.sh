#!/bin/bash

# Migration rollback script for Django applications
# Usage: ./rollback_migration.sh <app_name> <migration_number>
# Example: ./rollback_migration.sh accounts 0001

set -e

APP=$1
MIGRATION=$2

if [ -z "$APP" ] || [ -z "$MIGRATION" ]; then
    echo "Usage: $0 <app_name> <migration_number>"
    echo "Example: $0 accounts 0001"
    exit 1
fi

echo "Rolling back $APP to migration $MIGRATION..."
python manage.py migrate $APP $MIGRATION

echo "Current migration status for $APP:"
python manage.py showmigrations $APP

echo "Rollback completed successfully!"
