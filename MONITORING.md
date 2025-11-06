# Sistema Bancário - Monitoramento de Performance

## Visão Geral

Este documento descreve a implementação de monitoramento de performance no sistema bancário.

## Componentes Monitorados

### 1. Requisições Django
- **Middleware**: `core.middleware.PerformanceMonitoringMiddleware`
- **Logs**: `logs/django.log`
- **Métricas capturadas**:
  - Método HTTP
  - Path da requisição
  - Status code da resposta
  - Tempo de execução (ms)
  - Usuário autenticado

### 2. Transações Bancárias
- **Logs**: `logs/django.log`
- **Operações monitoradas**:
  - Depósitos (DepositMoneyView)
  - Saques (WithdrawMoneyView)
- **Métricas capturadas**:
  - Valor da transação
  - Número da conta
  - Saldo antes/depois

### 3. Tarefas Celery
- **Logs**: `logs/celery.log`
- **Tarefas monitoradas**:
  - `calculate_interest` (cálculo de juros mensais)
- **Métricas capturadas**:
  - Início/conclusão da tarefa
  - Número de contas processadas
  - Número de transações criadas
  - Tempo de execução
  - Erros/exceções

### 4. Queries de Banco de Dados
- **Logs**: `logs/database.log`
- **Configuração**: `django.db.backends` logger em DEBUG
- **Métricas capturadas**:
  - Queries SQL executadas
  - Tempo de execução das queries

## Estrutura de Logs

```
logs/
├── django.log      # Logs gerais do Django e transações
├── celery.log      # Logs das tarefas Celery
└── database.log    # Logs de queries SQL
```

## Configuração

A configuração de logging está em `banking_system/settings.py`:

- **Formato**: Logs estruturados com timestamp, nível, módulo e mensagem
- **Rotação**: Arquivos de log com limite de 10MB, mantendo 5 backups
- **Níveis**: INFO para operações normais, WARNING para requisições lentas, ERROR para falhas

## Visualização de Logs

### Durante Desenvolvimento

```bash
# Ver todos os logs do Django
tail -f logs/django.log

# Ver logs do Celery
tail -f logs/celery.log

# Ver queries SQL
tail -f logs/database.log

# Ver todos os logs simultaneamente
tail -f logs/*.log
```

## Monitoramento Adicional (Opcional)

### Flower - Dashboard Web para Celery

Flower é uma ferramenta de monitoramento em tempo real para Celery.

#### Instalação

```bash
pip install flower
```

#### Uso

```bash
# Iniciar Flower
celery -A banking_system flower

# Acessar dashboard
# http://localhost:5555
```

#### Recursos do Flower
- Visualização de tarefas em tempo real
- Histórico de execuções
- Estatísticas de workers
- Monitoramento de filas
- Controle de tarefas (retry, revoke, etc.)

## Métricas Importantes

### Performance de Requisições
- Requisições lentas (> 1 segundo) são marcadas como WARNING
- Status 4xx geram WARNING
- Status 5xx geram ERROR

### Tarefas Celery
- Falhas em tarefas geram ERROR com stack trace completo
- Sucesso gera INFO com métricas de execução

### Banco de Dados
- Todas as queries são logadas em modo DEBUG
- Útil para identificar queries N+1 ou queries lentas
