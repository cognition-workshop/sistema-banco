# Guia de Gerenciamento de Migrações

Este documento descreve os procedimentos para criar, aplicar e reverter migrações de banco de dados no sistema bancário.

## Criando Migrações

### 1. Criar uma nova migração

Após fazer alterações nos models:

```bash
python manage.py makemigrations
```

Para uma app específica:

```bash
python manage.py makemigrations accounts
python manage.py makemigrations transactions
```

### 2. Revisar a migração

Sempre revise o arquivo de migração gerado antes de aplicar:

```bash
# Ver o SQL que será executado
python manage.py sqlmigrate accounts 0001

# Ver o status das migrações
python manage.py showmigrations
```

## Aplicando Migrações

### Procedimento Padrão

```bash
# 1. Fazer backup do banco de dados (OBRIGATÓRIO)
./scripts/backup_database.sh

# 2. Testar migrações em ambiente de desenvolvimento/staging
python manage.py migrate --plan
python manage.py migrate

# 3. Verificar que tudo está funcionando
python manage.py check

# 4. Executar testes
pytest
```

### Aplicar em Produção

```bash
# 1. Backup
./scripts/backup_database.sh production

# 2. Ativar modo de manutenção (se disponível)
# ./scripts/maintenance_mode.sh on

# 3. Aplicar migrações
python manage.py migrate --no-input

# 4. Verificar aplicação
python manage.py showmigrations | grep '\[ \]'

# 5. Desativar modo de manutenção
# ./scripts/maintenance_mode.sh off

# 6. Monitorar logs
tail -f logs/banking_system.log
```

## Revertendo Migrações

### Reverter uma migração específica

```bash
# Reverter para uma migração anterior
python manage.py migrate accounts 0003

# Reverter todas as migrações de uma app
python manage.py migrate accounts zero
```

### Procedimento de Rollback Completo

```bash
# 1. Identificar a migração problemática
python manage.py showmigrations

# 2. Restaurar backup
./scripts/restore_database.sh <backup_file>

# 3. Verificar estado do banco
python manage.py showmigrations

# 4. Se necessário, aplicar migrações até o ponto seguro
python manage.py migrate accounts 0003
```

## Scripts de Backup

### backup_database.sh

Localizado em `scripts/backup_database.sh`. Este script:
- Cria backup do banco de dados SQLite
- Comprime o arquivo
- Mantém os últimos 30 backups
- Utilização: `./scripts/backup_database.sh`

### restore_database.sh

Script para restaurar um backup:
```bash
#!/bin/bash
# Script para restaurar backup do banco de dados

if [ -z "$1" ]; then
    echo "Uso: ./restore_database.sh <arquivo_backup>"
    exit 1
fi

BACKUP_FILE=$1
DB_FILE="db.sqlite3"

# Fazer backup do banco atual antes de restaurar
cp $DB_FILE "${DB_FILE}.pre_restore_$(date +%Y%m%d_%H%M%S)"

# Descomprimir e restaurar
gunzip -c $BACKUP_FILE > $DB_FILE

echo "Banco de dados restaurado de: $BACKUP_FILE"
echo "Backup do estado anterior salvo"
```

## Testes de Migração

### Criar testes para migrações críticas

Exemplo de teste para migração de adição de campo:

```python
from django.test import TestCase
from django.core.management import call_command

class TestMigration0004(TestCase):
    """Testa a migração que adiciona campo novo_campo."""
    
    def test_migration_forward(self):
        call_command('migrate', 'accounts', '0003')
        call_command('migrate', 'accounts', '0004')
        
        from accounts.models import UserBankAccount
        account = UserBankAccount.objects.first()
        self.assertTrue(hasattr(account, 'novo_campo'))
    
    def test_migration_backward(self):
        call_command('migrate', 'accounts', '0004')
        call_command('migrate', 'accounts', '0003')
        
        from accounts.models import UserBankAccount
        account = UserBankAccount.objects.first()
        self.assertFalse(hasattr(account, 'novo_campo'))
```

## Melhores Práticas

1. **Sempre fazer backup antes de aplicar migrações**
2. **Testar migrações em ambiente de desenvolvimento primeiro**
3. **Revisar o código SQL gerado antes de aplicar**
4. **Manter migrações pequenas e focadas**
5. **Documentar migrações complexas**
6. **Testar o rollback antes de aplicar em produção**
7. **Nunca editar migrações já aplicadas em produção**
8. **Usar data migrations para transformações de dados**

## Checklist de Migração em Produção

- [ ] Backup do banco de dados criado
- [ ] Migração testada em staging
- [ ] Rollback testado em staging
- [ ] Notificação de manutenção enviada aos usuários
- [ ] Modo de manutenção ativado
- [ ] Migrações aplicadas
- [ ] Testes de smoke executados
- [ ] Modo de manutenção desativado
- [ ] Monitoramento de logs iniciado
- [ ] Confirmação de que sistema está funcionando

## Contato

Em caso de problemas com migrações, contatar a equipe de DevOps.
