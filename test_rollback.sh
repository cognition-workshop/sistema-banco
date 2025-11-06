#!/bin/bash
set -e

echo "=========================================="
echo "TESTE DE ROLLBACK DE MIGRATIONS"
echo "=========================================="
echo ""

echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate
echo "✓ Ambiente virtual ativado"
echo ""

echo "📋 Passo 1: Status atual das migrations"
echo "----------------------------------------"
python manage.py showmigrations
echo ""

echo "📋 Passo 2: Aplicando todas as migrations"
echo "----------------------------------------"
python manage.py migrate
echo "✓ Migrations aplicadas"
echo ""

echo "📋 Passo 3: Criando dados de demonstração"
echo "----------------------------------------"
python create_demo_data.py
echo ""

echo "📋 Passo 4: Verificando dados antes do rollback"
echo "----------------------------------------"
echo "Verificando app transactions:"
python manage.py check_migration_safety transactions
echo ""
echo "Verificando app accounts:"
python manage.py check_migration_safety accounts
echo ""

echo "📋 Passo 5: Criando backup do banco de dados"
echo "----------------------------------------"
python backup_database.py
echo ""

echo "📋 Passo 6: Revertendo migrations do app transactions"
echo "----------------------------------------"
echo "⚠️  Revertendo transactions para zero..."
python manage.py migrate transactions zero
echo "✓ Migrations do transactions revertidas"
echo ""

echo "📋 Passo 7: Status após reverter transactions"
echo "----------------------------------------"
python manage.py showmigrations
echo ""

echo "📋 Passo 8: Revertendo migrations do app accounts"
echo "----------------------------------------"
echo "⚠️  Revertendo accounts para zero..."
python manage.py migrate accounts zero
echo "✓ Migrations do accounts revertidas"
echo ""

echo "📋 Passo 9: Status com todas migrations revertidas"
echo "----------------------------------------"
python manage.py showmigrations
echo ""

echo "📋 Passo 10: Reaplicando todas as migrations"
echo "----------------------------------------"
python manage.py migrate
echo "✓ Todas migrations reaplicadas"
echo ""

echo "📋 Passo 11: Status final"
echo "----------------------------------------"
python manage.py showmigrations
echo ""

echo "📋 Passo 12: Restaurar dados do backup (opcional)"
echo "----------------------------------------"
LATEST_BACKUP=$(ls -t db.sqlite3.backup.* 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "Backup mais recente encontrado: $LATEST_BACKUP"
    echo "Para restaurar, execute: cp $LATEST_BACKUP db.sqlite3"
    echo ""
    read -p "Deseja restaurar o backup agora? (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        cp "$LATEST_BACKUP" db.sqlite3
        echo "✓ Banco de dados restaurado do backup"
        python manage.py migrate
        echo "✓ Migrations reaplicadas após restauração"
    else
        echo "Backup não restaurado"
    fi
else
    echo "Nenhum backup encontrado"
fi
echo ""

echo "=========================================="
echo "✅ TESTE COMPLETO!"
echo "=========================================="
echo ""
echo "📝 Resumo:"
echo "  • Migrations aplicadas e revertidas com sucesso"
echo "  • Ordem correta de rollback verificada (transactions → accounts)"
echo "  • Backup criado e pode ser restaurado"
echo "  • Sistema está pronto para uso"
echo ""
