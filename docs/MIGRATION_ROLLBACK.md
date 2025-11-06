# Sistema de Gerenciamento de Migrations com Rollback Seguro

## Visão Geral

Este sistema fornece ferramentas robustas para gerenciar migrations do Django com capacidade de rollback seguro, especialmente projetado para preservar a integridade de dados financeiros do sistema bancário.

## Características

- ✅ Rastreamento completo do histórico de migrations
- ✅ Rollback controlado com validações de segurança
- ✅ Backup automático antes de operações de rollback
- ✅ Validações específicas para dados bancários
- ✅ Modo dry-run para simular operações
- ✅ Compatível com SQLite (desenvolvimento) e PostgreSQL (produção)

## Comandos Disponíveis

### 1. Visualizar Histórico de Migrations

```bash
# Ver todas as migrations aplicadas
python manage.py migration_history

# Filtrar por app específica
python manage.py migration_history --app accounts

# Formato JSON
python manage.py migration_history --format json
```

### 2. Rollback Seguro de Migrations

```bash
# Modo dry-run (recomendado primeiro)
python manage.py safe_migrate_rollback accounts 0001

# Executar rollback com backup automático
python manage.py safe_migrate_rollback accounts 0001 --execute

# Rollback para estado inicial (zero)
python manage.py safe_migrate_rollback transactions zero --execute

# Forçar rollback ignorando avisos (use com EXTREMA cautela)
python manage.py safe_migrate_rollback accounts 0001 --execute --force

# Rollback sem backup (NÃO recomendado)
python manage.py safe_migrate_rollback accounts 0001 --execute --no-backup
```

### 3. Listar Backups Disponíveis

```bash
python manage.py list_backups
```

## Fluxo de Trabalho Recomendado

### Cenário 1: Rollback de uma Migration Problemática

1. **Verificar o histórico atual:**
   ```bash
   python manage.py migration_history
   ```

2. **Simular o rollback (dry-run):**
   ```bash
   python manage.py safe_migrate_rollback transactions 0001
   ```

3. **Revisar os avisos** exibidos pelo sistema

4. **Executar o rollback se seguro:**
   ```bash
   python manage.py safe_migrate_rollback transactions 0001 --execute
   ```

5. **Verificar o resultado:**
   ```bash
   python manage.py migration_history
   python manage.py showmigrations
   ```

### Cenário 2: Rollback Completo de uma App

```bash
# Simular primeiro
python manage.py safe_migrate_rollback transactions zero

# Se seguro, executar
python manage.py safe_migrate_rollback transactions zero --execute
```

## Validações de Segurança

O sistema executa as seguintes validações antes de permitir um rollback:

### Validações Gerais
- Verifica se existem dados nas tabelas afetadas
- Verifica dependências entre migrations de diferentes apps
- Verifica a integridade das foreign keys

### Validações Específicas do Sistema Bancário

#### Para App `transactions`:
- Conta o número de transações existentes
- Calcula o saldo total do sistema
- Avisa sobre possível perda de dados financeiros

#### Para App `accounts`:
- Conta o número de contas bancárias
- Conta o número de usuários
- Avisa sobre perda de dados de clientes

### Níveis de Aviso

- **⚠️  CRÍTICO**: Operação pode causar perda de dados financeiros
- **⚠️  Aviso**: Operação requer atenção mas pode ser segura

## Sistema de Backup

### Backup Automático

Por padrão, um backup completo é criado automaticamente antes de cada rollback. O backup inclui:

1. **data.json**: Todos os dados do banco em formato JSON
2. **db.sqlite3**: Cópia do arquivo do banco SQLite (se aplicável)
3. **metadata.json**: Informações sobre o backup

### Localização dos Backups

Os backups são armazenados em: `backups/`

Formato do nome: `backup_YYYYMMDD_HHMMSS_description/`

### Restauração Manual de Backup

Se necessário restaurar um backup:

```bash
# 1. Listar backups disponíveis
python manage.py list_backups

# 2. Parar o servidor se estiver rodando
# 3. Substituir o arquivo do banco
cp backups/backup_20231106_120000_*/db.sqlite3 db.sqlite3

# 4. Ou restaurar dados via loaddata
python manage.py loaddata backups/backup_20231106_120000_*/data.json
```

## Compatibilidade com Bancos de Dados

### SQLite (Desenvolvimento)
- ✅ Totalmente suportado
- ✅ Backup de arquivo completo
- ✅ Rollback direto

### PostgreSQL (Produção)
- ✅ Suportado via Django ORM
- ✅ Backup via serialização JSON
- ⚠️  Recomenda-se usar ferramentas nativas de backup do PostgreSQL em produção

## Boas Práticas

### ✅ FAÇA

1. **Sempre execute dry-run primeiro**
   ```bash
   python manage.py safe_migrate_rollback app migration
   ```

2. **Mantenha backups atualizados**
   - Backups automáticos são criados, mas considere backups regulares adicionais

3. **Teste em ambiente de desenvolvimento**
   - Nunca teste rollbacks diretamente em produção

4. **Documente cada rollback**
   - Anote o motivo e o resultado de cada operação

5. **Verifique os avisos de segurança**
   - Leia todos os avisos cuidadosamente antes de prosseguir

### ❌ NÃO FAÇA

1. **Não use --force sem necessidade**
   - Use apenas quando você tem certeza absoluta

2. **Não faça rollback sem backup**
   - Evite a flag --no-backup em produção

3. **Não ignore avisos críticos**
   - Avisos sobre dados financeiros são críticos

4. **Não execute rollback durante uso ativo**
   - Garanta que nenhum usuário esteja usando o sistema

5. **Não confie apenas em backups automáticos**
   - Mantenha uma estratégia de backup adicional

## Exemplos de Uso

### Exemplo 1: Reverter Última Migration

```bash
# 1. Ver histórico
python manage.py migration_history --app transactions

# Saída exemplo:
# transactions    0002_add_transfer_type    2023-11-06 10:30:00
# transactions    0001_initial              2023-11-06 09:00:00

# 2. Simular rollback
python manage.py safe_migrate_rollback transactions 0001

# 3. Executar
python manage.py safe_migrate_rollback transactions 0001 --execute
```

### Exemplo 2: Rollback com Dados Existentes

```bash
python manage.py safe_migrate_rollback accounts 0001

# Saída exemplo:
# ⚠️  AVISOS ENCONTRADOS:
#   - Tabela 'accounts_user' contém 50 registros
#   - Tabela 'accounts_userbankaccount' contém 50 registros
#   - ⚠️  CRÍTICO: Sistema possui 50 contas bancárias e 50 usuários
#   - Outras apps dependem de migrations de 'accounts': transactions
#
# ❌ Rollback bloqueado por questões de segurança.
```

### Exemplo 3: Forçar Rollback (Cuidado!)

```bash
# Apenas use se você tem certeza absoluta
python manage.py safe_migrate_rollback accounts 0001 --execute --force
```

## Troubleshooting

### Erro: "App não encontrada"
**Problema**: Nome da app incorreto
**Solução**: Verifique o nome exato com `python manage.py migrate --list`

### Erro: "Migration não encontrada"
**Problema**: Nome da migration incorreto
**Solução**: Use `python manage.py migration_history --app nome_app`

### Backup Falhou
**Problema**: Permissões ou espaço em disco
**Solução**: Verifique permissões em `backups/` e espaço disponível

### Rollback Falhou Parcialmente
**Problema**: Erro durante rollback
**Solução**: 
1. Verifique o último backup criado
2. Restaure se necessário
3. Analise os logs de erro
4. Consulte a equipe de desenvolvimento

## Suporte e Contato

Para questões sobre o sistema de rollback:
- Consulte a documentação do Django: https://docs.djangoproject.com/en/3.2/topics/migrations/
- Revise o código dos comandos em: `core/management/commands/`
- Entre em contato com a equipe de desenvolvimento

## Changelog

- **v1.0.0** (2023-11-06): Implementação inicial
  - Comando migration_history
  - Comando safe_migrate_rollback
  - Sistema de backup automático
  - Validações de segurança para sistema bancário
