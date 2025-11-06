#!/bin/bash
set -e

echo "=== Executando verificações do Django ==="
python manage.py check

echo ""
echo "=== Executando linting com flake8 ==="
flake8 .

echo ""
echo "=== Verificando formatação com black ==="
black --check .

echo ""
echo "=== Executando testes ==="
python manage.py test

echo ""
echo "=== Executando pytest com cobertura ==="
pytest --cov=. --cov-report=html --cov-report=term

echo ""
echo "✓ Todos os testes passaram com sucesso!"
