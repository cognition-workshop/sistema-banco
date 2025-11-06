#!/bin/bash

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_FILE="db.sqlite3"
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sqlite3"

mkdir -p $BACKUP_DIR

cp $DB_FILE $BACKUP_FILE

gzip $BACKUP_FILE

echo "Backup criado: ${BACKUP_FILE}.gz"

ls -t ${BACKUP_DIR}/db_backup_*.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null

echo "Backups antigos removidos (mantidos últimos 30)"
