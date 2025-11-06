# Guia de Gerenciamento de Migrations com Rollback

## Introdução

Este documento explica como gerenciar e reverter (rollback) migrations do Django de forma segura no sistema bancário. As migrations do Django são **reversíveis por padrão** - quando você cria models usando `CreateModel`, o Django automaticamente gera operações reversas que permitem desfazer as mudanças no banco de dados.

## Migrations Existentes

O sistema possui duas migrations iniciais:

1. **`accounts/migrations/0001_initial.py`** - Cria os modelos:
   - User (modelo customizado de usuário)
   - BankAccountType (tipos de conta bancária)
   - UserBankAccount (contas bancárias dos usuários)
   - UserAddress (endereços dos usuários)

2. **`transactions/migrations/0001_initial.py`** - Cria o modelo:
   - Transaction (transações financeiras)
   - **Depende de**: `accounts.0001_initial`

## Comandos de Rollback

### Listar Status das Migrations

Para ver quais migrations estão aplicadas:

```bash
python manage.py showmigrations
```

Migrations aplicadas são marcadas com `[X]`, migrations não aplicadas com `[ ]`.

### Reverter para uma Migration Específica

Para reverter até uma migration específica (mantendo ela aplicada):

```bash
python manage.py migrate <app_name> <migration_name>
```

Exemplo - reverter transactions para uma migration anterior:
```bash
python manage.py migrate transactions 0001_initial
```

### Reverter Todas as Migrations de um App

Para reverter **todas** as migrations de um app:

```bash
python manage.py migrate <app_name> zero
```

Exemplo - reverter todas migrations de transactions:
```bash
python manage.py migrate transactions zero
```

### Ver SQL que Será Executado

Para visualizar o SQL que será executado durante o rollback (sem aplicá-lo):

```bash
python manage.py sqlmigrate <app_name> <migration_name>
```

## ⚠️ ORDEM CORRETA DE ROLLBACK

**IMPORTANTE**: Devido às dependências entre apps, você **DEVE** seguir esta ordem ao fazer rollback:

### 1️⃣ PRIMEIRO: Reverter `transactions`
```bash
python manage.py migrate transactions zero
```

### 2️⃣ DEPOIS: Reverter `accounts`
```bash
python manage.py migrate accounts zero
```

**Por quê?** A migration `transactions/0001_initial.py` depende de `accounts/0001_initial.py`. O Django não permite reverter um app se outro app ainda depende dele. Se você tentar reverter `accounts` primeiro, receberá um erro.

## 🚨 Avisos de Segurança: CASCADE DELETE

### O que é CASCADE DELETE?

Quando um modelo tem `on_delete=models.CASCADE`, deletar o registro pai automaticamente deleta todos os registros filhos relacionados.

### Relações CASCADE no Sistema

1. **Transaction → UserBankAccount (CASCADE)**
   - Localização: `transactions/models.py`, linha 11
   - Impacto: Deletar uma `UserBankAccount` deleta **todas as Transactions** relacionadas

2. **UserBankAccount → User (CASCADE)**
   - Localização: `accounts/models.py`, linha 73
   - Impacto: Deletar um `User` deleta sua `UserBankAccount` (e consequentemente todas suas Transactions)

3. **UserAddress → User (CASCADE)**
   - Localização: `accounts/models.py`, linha 116
   - Impacto: Deletar um `User` deleta seu `UserAddress`

4. **UserBankAccount → BankAccountType (CASCADE)**
   - Localização: `accounts/models.py`, linha 78
   - Impacto: Deletar um `BankAccountType` deleta todas as `UserBankAccount` que o utilizam

### ⚠️ Impacto do Rollback Completo

Se você reverter `accounts` para zero:
- ✗ Todas as tabelas (`User`, `UserBankAccount`, `UserAddress`, `BankAccountType`) serão **deletadas**
- ✗ Por efeito CASCADE, **todas as Transactions também serão deletadas**
- ✗ **TODOS OS DADOS DO SISTEMA SERÃO PERDIDOS**

## 🛡️ Backup Antes de Rollback

**SEMPRE faça backup do banco de dados antes de realizar rollback!**

### Usando o Script Automático

Use o script fornecido para criar um backup timestamped:

```bash
python backup_database.py
```

Isso criará um arquivo `db.sqlite3.backup.YYYYMMDD_HHMMSS` no diretório raiz.

### Restaurar de um Backup

Para restaurar o banco de dados de um backup:

```bash
cp db.sqlite3.backup.YYYYMMDD_HHMMSS db.sqlite3
```

### Backup Manual

Alternativamente, você pode copiar o arquivo manualmente:

```bash
cp db.sqlite3 db.sqlite3.backup
```

## 🔍 Verificar Impacto Antes do Rollback

Use o comando de verificação de segurança para ver quantos dados serão afetados:

```bash
python manage.py check_migration_safety <app_name>
```

Exemplos:
```bash
python manage.py check_migration_safety transactions
python manage.py check_migration_safety accounts
```

Este comando mostra:
- Quantos registros existem em cada tabela
- Avisos sobre perda de dados
- Impacto do CASCADE DELETE

## 📋 Exemplos Práticos

### Cenário 1: Reverter e Reaplicar Transactions

```bash
# 1. Fazer backup
python backup_database.py

# 2. Verificar impacto
python manage.py check_migration_safety transactions

# 3. Reverter transactions
python manage.py migrate transactions zero

# 4. Verificar status
python manage.py showmigrations

# 5. Reaplicar transactions
python manage.py migrate transactions

# 6. Verificar status final
python manage.py showmigrations
```

### Cenário 2: Rollback Completo do Sistema

```bash
# 1. Fazer backup
python backup_database.py

# 2. Verificar impacto total
python manage.py check_migration_safety accounts
python manage.py check_migration_safety transactions

# 3. Reverter na ordem correta
python manage.py migrate transactions zero
python manage.py migrate accounts zero

# 4. Verificar que tudo foi revertido
python manage.py showmigrations

# 5. Reaplicar tudo
python manage.py migrate

# 6. Recriar dados demo (opcional)
python create_demo_data.py
```

### Cenário 3: Teste Completo de Rollback

Execute o script de teste automatizado:

```bash
bash test_rollback.sh
```

Este script executa um ciclo completo:
1. Aplica todas migrations
2. Cria dados demo
3. Faz backup
4. Verifica dados
5. Reverte transactions
6. Reverte accounts
7. Reaplica tudo
8. Verifica status final

## 🔧 Solução de Problemas

### Erro: "Cannot reverse this migration"

**Causa**: Algumas operações não são reversíveis automaticamente (ex: `RunPython` sem `reverse_code`).

**Solução**: As migrations atuais (`0001_initial`) são totalmente reversíveis. Se você adicionar migrations customizadas no futuro, certifique-se de implementar a operação reversa.

### Erro: "Conflicting migrations detected"

**Causa**: Múltiplas migrations foram criadas para o mesmo app sem seguir ordem linear.

**Solução**: Use `python manage.py makemigrations --merge` para resolver conflitos.

### Erro ao Reverter Accounts (transactions ainda aplicadas)

**Erro**: `Cannot unapply accounts.0001_initial while transactions.0001_initial is applied`

**Solução**: Sempre reverta `transactions` primeiro, depois `accounts`.

## 📚 Recursos Adicionais

- [Documentação Django - Migrations](https://docs.djangoproject.com/en/3.2/topics/migrations/)
- [Documentação Django - Rollback](https://docs.djangoproject.com/en/3.2/ref/django-admin/#migrate)
- [Django CASCADE Delete](https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.CASCADE)

## ⚡ Comandos Rápidos

```bash
# Ver status
python manage.py showmigrations

# Backup
python backup_database.py

# Verificar segurança
python manage.py check_migration_safety accounts
python manage.py check_migration_safety transactions

# Rollback completo (ordem correta!)
python manage.py migrate transactions zero
python manage.py migrate accounts zero

# Reaplicar tudo
python manage.py migrate

# Teste automatizado
bash test_rollback.sh
```
