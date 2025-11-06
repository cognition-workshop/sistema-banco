#!/bin/bash

set -e

echo "=== Sistema de Migração Segura ==="

source venv/bin/activate

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sqlite3"

mkdir -p $BACKUP_DIR

echo "1. Criando backup do banco de dados..."
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 $BACKUP_FILE
    echo "   ✓ Backup criado: $BACKUP_FILE"
else
    echo "   ⚠ Nenhum banco de dados encontrado para backup"
fi

echo "2. Verificando migrations pendentes..."
python manage.py showmigrations --plan

echo "3. Executando migrations..."
if python manage.py migrate; then
    echo "   ✓ Migrations executadas com sucesso!"
else
    echo "   ✗ Erro ao executar migrations!"
    
    if [ -f $BACKUP_FILE ]; then
        echo "4. Restaurando backup..."
        cp $BACKUP_FILE db.sqlite3
        echo "   ✓ Backup restaurado com sucesso"
    fi
    
    exit 1
fi

echo "=== Migração concluída com sucesso ==="
