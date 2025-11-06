#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <app_name> <migration_name>"
    exit 1
fi

python manage.py migrate $1 $2
