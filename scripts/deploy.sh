#!/bin/bash
set -e

echo "=== Iniciando processo de deploy ==="

CURRENT_BRANCH=$(git branch --show-current)
echo "Branch atual: $CURRENT_BRANCH"

echo "=== Atualizando código ==="
git pull origin $CURRENT_BRANCH

echo "=== Instalando dependências ==="
pip install -r requirements.txt

echo "=== Aplicando migrations com backup ==="
python scripts/manage_migrations.py apply

echo "=== Coletando arquivos estáticos ==="
python manage.py collectstatic --noinput

echo "=== Verificando sistema ==="
python manage.py check --deploy

echo "=== Reiniciando serviços ==="

echo "✓ Deploy concluído com sucesso!"
