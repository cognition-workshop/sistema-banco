# Pipeline CI/CD

## Visão Geral
Este projeto possui um pipeline de CI/CD completo implementado via GitHub Actions.

## Jobs do Pipeline

### 1. Tests
- Executa a suite de testes do Django
- Usa Redis como serviço
- Roda migrações antes dos testes
- Comando: `python manage.py test`

### 2. Lint
- Verifica qualidade do código com flake8
- Verifica formatação com black
- Executa Django check
- Configurado com `continue-on-error: true` para não bloquear o pipeline

### 3. Deploy
- Job manual (workflow_dispatch)
- Fornece instruções de deployment
- Requer aprovação manual
- Só executa após tests e lint passarem

## Executando Localmente

### Testes
```bash
python manage.py test
```

### Linting
```bash
# Django check
python manage.py check

# Flake8
flake8 . --count --show-source --statistics

# Black (verificação)
black --check .

# Black (aplicar formatação)
black .
```

### Pylint (opcional)
```bash
pylint accounts/ transactions/ core/ banking_system/
```

## Deployment Local com Docker

Para testar o deployment localmente:

```bash
docker-compose up --build
```

Acesse: http://localhost:8000

### Serviços Docker Compose
- **web**: Aplicação Django na porta 8000
- **redis**: Redis server na porta 6379
- **celery_worker**: Celery worker para processar tarefas assíncronas
- **celery_beat**: Celery beat scheduler para tarefas periódicas

## Configuração de Produção

Antes de fazer deploy em produção, configure:

### Variáveis de Ambiente
- `SECRET_KEY`: Gerar nova chave secreta
- `DEBUG`: Definir como `False`
- `ALLOWED_HOSTS`: Adicionar domínios permitidos
- `REDIS_URL`: URL do Redis em produção

### Banco de Dados
- **Desenvolvimento**: SQLite (atual)
- **Produção recomendada**: PostgreSQL ou MySQL

### Exemplo de configuração
```python
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'default-insecure-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
```

## Estrutura do CI/CD

```
.github/workflows/ci-cd.yml  # Workflow principal
├── tests                     # Job de testes
│   ├── Setup Python 3.9
│   ├── Install dependencies
│   ├── Run migrations
│   └── Run tests
├── lint                      # Job de linting
│   ├── Setup Python 3.9
│   ├── Install dependencies
│   ├── Django check
│   ├── Flake8
│   └── Black
└── deploy                    # Job de deploy (manual)
    └── Deployment instructions
```

## Triggers do Workflow

- **Push**: Branches `feature/time8_producao`, `main`, `master`
- **Pull Request**: Para as mesmas branches
- **Manual**: Via workflow_dispatch

## Ferramentas de Qualidade de Código

### Flake8
- Verificação de estilo PEP 8
- Complexidade ciclomática
- Configuração em `.flake8`

### Black
- Formatador de código automático
- Configuração em `pyproject.toml`
- Linha máxima: 120 caracteres

### Pylint
- Análise estática avançada
- Detecta bugs potenciais
- Verifica padrões de código

## Notas Importantes

1. **Testes Vazios**: Os arquivos de teste estão no formato padrão do Django mas sem implementação. O pipeline executará com sucesso mesmo assim.

2. **Linting Leniente**: As configurações de linting são intencionalmente lenientes para não bloquear o CI devido ao código legado.

3. **Redis Necessário**: O projeto requer Redis rodando para testes que envolvem Celery.

4. **SQLite em Produção**: Não recomendado. Use PostgreSQL ou MySQL para ambientes de produção.

## Troubleshooting

### Testes falhando
- Verificar se Redis está rodando
- Verificar migrações aplicadas
- Verificar dependências instaladas

### Linting falhando
- Executar `black .` para formatar código
- Revisar mensagens do flake8 e corrigir issues

### Docker Compose falhando
- Verificar se portas 8000 e 6379 estão livres
- Verificar se Docker daemon está rodando
- Limpar volumes antigos: `docker-compose down -v`
