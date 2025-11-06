# Guia de Gerenciamento de Migrations

Este documento descreve o processo de gerenciamento de migrations do sistema bancário com backup e rollback automático.

## Script de Gerenciamento

O script `scripts/manage_migrations.py` fornece funcionalidades para:
- Criar backups automáticos do banco de dados
- Validar migrations antes de aplicar
- Aplicar migrations com segurança
- Fazer rollback em caso de erro

## Uso

### Aplicar Migrations (com backup automático)

```bash
python scripts/manage_migrations.py apply
```

Este comando irá:
1. Validar que não há migrations não criadas
2. Criar um backup do banco de dados
3. Aplicar as migrations
4. Em caso de erro, fazer rollback automático

### Criar Backup Manual

```bash
python scripts/manage_migrations.py backup
```

### Validar Migrations

```bash
python scripts/manage_migrations.py validate
```

### Listar Backups Disponíveis

```bash
python scripts/manage_migrations.py list
```

## Processo de Rollback Manual

Se precisar fazer rollback manual para um backup específico:

### Para SQLite

```bash
cp backups/db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
```

### Para PostgreSQL

```bash
psql -U usuario -d nome_banco -f backups/db_backup_YYYYMMDD_HHMMSS.sql
```

## Boas Práticas

1. **Sempre faça backup antes de migrations em produção**
   ```bash
   python scripts/manage_migrations.py backup
   ```

2. **Teste migrations em ambiente de staging primeiro**

3. **Mantenha backups dos últimos 30 dias**
   - O script automaticamente cria backups com timestamp
   - Configure rotação automática de backups antigos

4. **Documente migrations críticas**
   - Para cada migration que modifica dados existentes
   - Documente o processo de rollback específico

## Migrations Críticas

### Migration: Adicionar campo CPF ao User

**Arquivo**: `accounts/migrations/000X_add_cpf_to_user.py`

**Descrição**: Adiciona campo CPF ao modelo User

**Rollback**: 
```bash
python manage.py migrate accounts 000Y
```

**Impacto**: Adiciona nova coluna na tabela de usuários. Não afeta dados existentes.

## Troubleshooting

### Erro: "No changes detected"

Verifique se você fez alterações nos models e execute:
```bash
python manage.py makemigrations
```

### Erro: "Table already exists"

Pode ser necessário fazer fake migration:
```bash
python manage.py migrate --fake accounts 000X
```

### Erro ao restaurar backup PostgreSQL

Verifique credenciais e permissões:
```bash
psql -U usuario -d postgres -c "SELECT 1"
```
