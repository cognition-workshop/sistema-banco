# Prompt Detalhado de Preparação para Produção - Sistema Bancário Online

## 1. Requisitos Iniciais do Projeto

### 1.1 Funcionalidades Principais do Sistema

Conforme documentado em `README.md` (linhas 6-17), o sistema bancário oferece as seguintes funcionalidades:

- Criar Conta Bancária
- Depositar e Sacar Dinheiro
- Suporte a Tipos de Conta Bancária (Conta Corrente, Conta Poupança)
- Cálculo de juros dependendo do tipo de conta
- Relatório de transações com filtro por período
- Visualização de saldo após cada transação no relatório
- Cálculo automático de juros mensais usando tarefas agendadas do Celery
- Cálculo de juros e atualização de saldo mais eficiente e preciso
- Capacidade de adicionar restrições de valor mínimo e máximo para transações
- Interface moderna com Tailwind CSS

### 1.2 Pré-requisitos Técnicos

Conforme `README.md` (linhas 20-28), o sistema requer:

- Python >= 3.7
- Redis Server
- Git
- pip
- Virtualenv (virtualenvwrapper recomendado)

**Dependências principais** (`README.md`, linhas 32-36):
- celery==4.4.7
- Django==3.2
- django-celery-beat==2.0.0
- python-dateutil==2.8.1
- redis==3.5.3

---

## 2. Tarefas Detalhadas - Seção Principal

### 2.1 Configurações de Segurança Críticas ⚠️ PRIORIDADE MÁXIMA

**Arquivo:** `banking_system/settings.py`

#### 2.1.1 Secret Key
**Referência:** `banking_system/settings.py` (linha 23)

**Problema Atual:**
```python
SECRET_KEY = 'po0172$69b@78ps4v^uhfxu6q--8ko7kpp7rbz420s_3w#sir%'
```

**Tarefas:**
- [ ] Remover o `SECRET_KEY` hardcoded do arquivo settings.py
- [ ] Gerar um novo SECRET_KEY seguro usando: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- [ ] Configurar SECRET_KEY como variável de ambiente
- [ ] Atualizar settings.py para ler o SECRET_KEY do ambiente:
  ```python
  import os
  SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
  if not SECRET_KEY:
      raise ValueError("DJANGO_SECRET_KEY environment variable must be set")
  ```

**Por que é necessário:** O SECRET_KEY é usado para assinaturas criptográficas em Django. Expor essa chave permite que atacantes forjem sessões, tokens CSRF, e comprometam a segurança da aplicação.

#### 2.1.2 DEBUG Mode
**Referência:** `banking_system/settings.py` (linha 26)

**Problema Atual:**
```python
DEBUG = True
```

**Tarefas:**
- [ ] Configurar `DEBUG = False` para ambiente de produção
- [ ] Implementar leitura condicional do ambiente:
  ```python
  DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
  ```
- [ ] Configurar página de erro 404 e 500 customizada
- [ ] Configurar logging adequado para capturar erros sem expor informações sensíveis

**Por que é necessário:** DEBUG=True expõe informações sensíveis como variáveis de ambiente, queries SQL, stack traces completos e estrutura do projeto para usuários finais, criando sérias vulnerabilidades de segurança.

#### 2.1.3 Allowed Hosts
**Referência:** `banking_system/settings.py` (linha 28)

**Problema Atual:**
```python
ALLOWED_HOSTS = []
```

**Tarefas:**
- [ ] Definir lista de domínios permitidos para produção
- [ ] Exemplo de implementação:
  ```python
  ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
  ```
- [ ] Validar que todos os domínios de produção (incluindo www e subdomínios) estão na lista
- [ ] Nunca usar '*' (wildcard) em produção

**Por que é necessário:** ALLOWED_HOSTS vazio com DEBUG=False causará erros 400 Bad Request. Esta configuração protege contra ataques de Host Header Injection.

---

### 2.2 Configuração do Banco de Dados

**Arquivo:** `banking_system/settings.py` (linhas 83-88)

**Configuração Atual:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Tarefas:**

#### 2.2.1 Migração para Banco de Dados de Produção
- [ ] Escolher banco de dados de produção (PostgreSQL recomendado ou MySQL)
- [ ] Instalar driver apropriado:
  - PostgreSQL: `psycopg2-binary`
  - MySQL: `mysqlclient`
- [ ] Configurar credenciais do banco via variáveis de ambiente
- [ ] Exemplo de configuração para PostgreSQL:
  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql',
          'NAME': os.environ.get('DB_NAME'),
          'USER': os.environ.get('DB_USER'),
          'PASSWORD': os.environ.get('DB_PASSWORD'),
          'HOST': os.environ.get('DB_HOST'),
          'PORT': os.environ.get('DB_PORT', '5432'),
      }
  }
  ```

#### 2.2.2 Configurações Adicionais de Banco de Dados
- [ ] Configurar connection pooling se usar PostgreSQL
- [ ] Definir `CONN_MAX_AGE` para reutilizar conexões:
  ```python
  'CONN_MAX_AGE': 600,  # 10 minutos
  ```
- [ ] Configurar backup automático do banco de dados
- [ ] Planejar estratégia de migração de dados do SQLite para o novo banco

**Por que é necessário:** SQLite não é adequado para ambientes de produção com múltiplos processos/threads concorrentes, não possui recursos avançados de segurança, backup e performance que PostgreSQL/MySQL oferecem.

---

### 2.3 Configuração do Celery e Redis

**Arquivo:** `banking_system/settings.py` (linhas 136-142)

**Configuração Atual:**
```python
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
```

**Tarefas:**

#### 2.3.1 Redis de Produção
- [ ] Configurar Redis com autenticação (senha)
- [ ] Atualizar URLs do broker e backend para usar variáveis de ambiente:
  ```python
  CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
  CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
  ```
- [ ] Formato com autenticação: `redis://:password@host:port/db`
- [ ] Considerar usar Redis em cluster ou Redis gerenciado (AWS ElastiCache, Azure Cache for Redis, etc.)
- [ ] Configurar SSL/TLS para conexão Redis se disponível
- [ ] Definir databases diferentes para broker e result backend (ex: /0 e /1)

#### 2.3.2 Configurações de Performance do Celery
- [ ] Configurar `CELERY_TASK_ALWAYS_EAGER = False` (nunca True em produção)
- [ ] Definir `CELERY_TASK_TRACK_STARTED = True` para melhor monitoramento
- [ ] Configurar timeout de tasks:
  ```python
  CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutos
  CELERY_TASK_TIME_LIMIT = 360  # 6 minutos
  ```
- [ ] Configurar rate limiting se necessário

**Por que é necessário:** Credenciais expostas (localhost sem senha) são inseguras. Redis de produção precisa de autenticação adequada e configurações otimizadas para lidar com cargas de trabalho reais.

---

### 2.4 Arquitetura de Processos

**Referência:** `README.md` (linhas 80-96)

**Configuração Atual:** O sistema requer execução manual de 4 processos separados:
1. Django development server: `python manage.py runserver`
2. Celery worker: `celery -A banking_system worker -l info`
3. Celery beat: `celery -A banking_system beat -l info`
4. Redis server: `redis-server`

**Tarefas:**

#### 2.4.1 Servidor de Aplicação WSGI
- [ ] Substituir `runserver` por servidor WSGI de produção (Gunicorn ou uWSGI)
- [ ] Instalar Gunicorn: `pip install gunicorn`
- [ ] Configurar número de workers: `gunicorn banking_system.wsgi:application --workers 4 --bind 0.0.0.0:8000`
- [ ] Fórmula recomendada de workers: `(2 x número_de_cores) + 1`

#### 2.4.2 Gerenciador de Processos
- [ ] Escolher gerenciador de processos: Supervisor ou systemd
- [ ] Criar arquivos de configuração para cada processo

**Exemplo com Supervisor:**

Arquivo: `/etc/supervisor/conf.d/banking_system.conf`
```ini
[program:banking_django]
command=/path/to/venv/bin/gunicorn banking_system.wsgi:application --workers 4 --bind 0.0.0.0:8000
directory=/path/to/banking-system
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/banking_system/django.log

[program:banking_celery_worker]
command=/path/to/venv/bin/celery -A banking_system worker -l info
directory=/path/to/banking-system
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/banking_system/celery_worker.log

[program:banking_celery_beat]
command=/path/to/venv/bin/celery -A banking_system beat -l info
directory=/path/to/banking-system
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/banking_system/celery_beat.log

[group:banking_system]
programs=banking_django,banking_celery_worker,banking_celery_beat
```

**Exemplo com systemd:**

- [ ] Criar arquivos de serviço para cada processo em `/etc/systemd/system/`
- [ ] `banking-django.service`, `banking-celery-worker.service`, `banking-celery-beat.service`

#### 2.4.3 Servidor Web Reverso
- [ ] Configurar Nginx ou Apache como reverse proxy
- [ ] Configurar certificado SSL/TLS (Let's Encrypt)
- [ ] Configurar compressão gzip
- [ ] Configurar cache de arquivos estáticos
- [ ] Configurar rate limiting

**Por que é necessário:** Comandos manuais não são adequados para produção. Gerenciadores de processos garantem que os serviços sejam iniciados automaticamente, reiniciados em caso de falha, e gerenciados de forma centralizada.

---

### 2.5 Tarefas Agendadas

**Arquivo:** `banking_system/celery.py` (linhas 22-28)

**Configuração Atual:**
```python
app.conf.beat_schedule = {
    'calculate_interest': {
        'task': 'calculate_interest',
        'schedule': crontab(0, 0, day_of_month='1'),
    }
}
```

**Tarefas:**
- [ ] Verificar timezone de produção em `banking_system/settings.py` (linha 115): `TIME_ZONE = 'UTC'`
- [ ] Decidir se o timezone UTC é apropriado ou se deve ser alterado para o timezone local do banco
- [ ] Se alterar timezone, atualizar:
  ```python
  TIME_ZONE = 'America/Sao_Paulo'  # Exemplo para horário de Brasília
  USE_TZ = True  # Manter como True
  ```
- [ ] Garantir que `CELERY_TIMEZONE = TIME_ZONE` está configurado (já está na linha 142)
- [ ] Validar que a tarefa de cálculo de juros roda no primeiro dia de cada mês à meia-noite
- [ ] Implementar monitoramento para verificar execução bem-sucedida das tarefas agendadas
- [ ] Configurar alertas em caso de falha na execução das tarefas

**Por que é necessário:** Timezone incorreto pode fazer com que os juros sejam calculados em horários incorretos, causando problemas financeiros. O cálculo de juros no primeiro dia do mês é crítico para a operação bancária.

---

## 3. Configurações Críticas a Ajustar - Seção Secundária

### 3.1 Regras de Negócio Configuráveis

**Arquivo:** `banking_system/settings.py` (linhas 129-131)

**Configuração Atual:**
```python
ACCOUNT_NUMBER_START_FROM = 1000000000
MINIMUM_DEPOSIT_AMOUNT = 10
MINIMUM_WITHDRAWAL_AMOUNT = 10
```

**Tarefas:**
- [ ] Revisar valores das regras de negócio com stakeholders
- [ ] Validar se `MINIMUM_DEPOSIT_AMOUNT = 10` é adequado para produção
- [ ] Validar se `MINIMUM_WITHDRAWAL_AMOUNT = 10` é adequado para produção
- [ ] Validar se `ACCOUNT_NUMBER_START_FROM = 1000000000` é adequado
- [ ] Considerar se essas configurações devem vir de variáveis de ambiente
- [ ] Documentar as regras de negócio escolhidas
- [ ] Implementar sistema de auditoria para mudanças nessas configurações

**Por que é necessário:** Valores muito baixos ou altos podem não fazer sentido para operação real do banco. Essas configurações afetam diretamente as regras de negócio e devem ser validadas antes de ir para produção.

---

### 3.2 Bug Crítico Conhecido ⚠️ ALTA PRIORIDADE

**Arquivo:** `transactions/forms.py` (linhas 67-68)

**Bug Documentado:**
```python
# TODO: Add validation to prevent negative balances
# Bug: Users can currently withdraw more than their balance
```

**Problema:** O formulário de saque (`WithdrawForm`) não valida se o usuário tem saldo suficiente antes de permitir o saque, o que pode resultar em saldos negativos.

**Tarefas:**
- [ ] Implementar validação de saldo no método `clean_amount` da classe `WithdrawForm`
- [ ] Adicionar verificação:
  ```python
  def clean_amount(self):
      account = self.account
      min_withdraw_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
      max_withdraw_amount = account.account_type.maximum_withdrawal_amount
      balance = account.balance
      amount = self.cleaned_data.get('amount')
      
      if amount < min_withdraw_amount:
          raise forms.ValidationError(
              f'You can withdraw at least {min_withdraw_amount} $'
          )
      
      if amount > max_withdraw_amount:
          raise forms.ValidationError(
              f'You can withdraw at most {max_withdraw_amount} $'
          )
      
      # NOVA VALIDAÇÃO
      if amount > balance:
          raise forms.ValidationError(
              f'Insufficient funds. Your current balance is {balance} $'
          )
      
      return amount
  ```
- [ ] Criar testes unitários para validar a nova lógica
- [ ] Testar cenários edge case (saldo exatamente igual ao valor do saque, saldo zero, etc.)
- [ ] Considerar implementar validação adicional no nível do modelo (`UserBankAccount`)
- [ ] Implementar transaction lock para prevenir race conditions em saques concorrentes

**Por que é necessário:** Este é um bug crítico que pode causar sérios problemas financeiros. Permitir saldos negativos viola regras básicas de negócio bancário e pode resultar em perdas financeiras e problemas legais.

---

### 3.3 Modelo de Usuário Customizado

**Arquivo:** `accounts/models.py` (linhas 14-24) e `banking_system/settings.py` (linha 59)

**Configuração Atual:**
```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'

# accounts/models.py
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, null=False, blank=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
```

**Tarefas:**

#### 3.3.1 Configuração de Email
- [ ] Configurar backend de email para produção (SMTP, SendGrid, AWS SES, etc.)
- [ ] Adicionar configurações de email em settings.py:
  ```python
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  EMAIL_HOST = os.environ.get('EMAIL_HOST')
  EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
  EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
  DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
  ```
- [ ] Implementar sistema de recuperação de senha por email
- [ ] Implementar verificação de email após cadastro
- [ ] Testar envio de emails em ambiente de staging

#### 3.3.2 Validações Adicionais
- [ ] Implementar validação robusta de formato de email
- [ ] Considerar implementar autenticação de dois fatores (2FA)
- [ ] Implementar política de senha forte (já existe validação básica nas linhas 94-107 de settings.py)
- [ ] Considerar rate limiting para tentativas de login
- [ ] Implementar bloqueio de conta após múltiplas tentativas de login falhadas

**Por que é necessário:** Sistema de autenticação por email requer configuração adequada de envio de emails para funcionalidades como recuperação de senha. Sem isso, usuários podem perder acesso às suas contas.

---

### 3.4 Arquivos Estáticos

**Arquivo:** `banking_system/settings.py` (linha 127)

**Configuração Atual:**
```python
STATIC_URL = '/static/'
```

**Problema:** Falta configuração de `STATIC_ROOT` e estratégia de servir arquivos estáticos em produção.

**Tarefas:**

#### 3.4.1 Configuração de Arquivos Estáticos
- [ ] Adicionar `STATIC_ROOT` em settings.py:
  ```python
  STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
  ```
- [ ] Executar `python manage.py collectstatic` antes do deploy
- [ ] Adicionar diretório `staticfiles/` ao `.gitignore`

#### 3.4.2 Servidor Web para Arquivos Estáticos
- [ ] Configurar Nginx para servir arquivos estáticos diretamente
- [ ] Exemplo de configuração Nginx:
  ```nginx
  location /static/ {
      alias /path/to/banking-system/staticfiles/;
      expires 30d;
      add_header Cache-Control "public, immutable";
  }
  ```
- [ ] Considerar usar CDN para arquivos estáticos (CloudFront, Cloudflare, etc.)
- [ ] Configurar cache headers apropriados
- [ ] Considerar compressão de arquivos CSS/JS

#### 3.4.3 Arquivos de Media (se aplicável)
- [ ] Verificar se o sistema usa upload de arquivos
- [ ] Se sim, configurar `MEDIA_ROOT` e `MEDIA_URL`
- [ ] Configurar storage para arquivos de media (S3, Google Cloud Storage, etc.)
- [ ] Implementar validação de tipo e tamanho de arquivo
- [ ] Configurar antivírus scan para uploads

**Por que é necessário:** Django development server não deve servir arquivos estáticos em produção. Servidores web como Nginx são muito mais eficientes para essa tarefa. `collectstatic` agrupa todos os arquivos estáticos em um único diretório para facilitar o deploy.

---

## 4. Arquitetura do Sistema para Referência

A documentação completa da arquitetura do sistema está disponível na **wiki do repositório** (página ID: 3), incluindo:

- **Stack tecnológico completo:** Detalhamento de todas as tecnologias utilizadas (Django, Celery, Redis, PostgreSQL, etc.)
- **Fluxo de configuração:** Passo a passo de como configurar cada componente
- **Relacionamento entre componentes:** Como os diferentes serviços interagem entre si
- **Requisitos de deployment:** Lista completa de requisitos para ambientes de staging e produção

---

## 5. Checklist de Segurança Adicional

Além das tarefas acima, considere implementar:

- [ ] **HTTPS obrigatório:** Redirecionar todo tráfego HTTP para HTTPS
- [ ] **HSTS:** Configurar HTTP Strict Transport Security
  ```python
  SECURE_HSTS_SECONDS = 31536000  # 1 ano
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = True
  ```
- [ ] **Secure Cookies:**
  ```python
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  ```
- [ ] **Proteções adicionais:**
  ```python
  SECURE_BROWSER_XSS_FILTER = True
  SECURE_CONTENT_TYPE_NOSNIFF = True
  X_FRAME_OPTIONS = 'DENY'
  ```
- [ ] **CORS:** Se aplicável, configurar `django-cors-headers` apropriadamente
- [ ] **Rate Limiting:** Implementar rate limiting em endpoints críticos (login, registro, transações)
- [ ] **Logging e Monitoramento:**
  - Configurar logging estruturado
  - Integrar com ferramentas de monitoramento (Sentry, DataDog, etc.)
  - Configurar alertas para erros críticos
  - Implementar audit log para transações financeiras
- [ ] **Backup e Recovery:**
  - Configurar backup automático do banco de dados
  - Testar procedimento de restore
  - Documentar RTO (Recovery Time Objective) e RPO (Recovery Point Objective)

---

## 6. Checklist de Testes Antes do Deploy

- [ ] Todos os testes unitários passando
- [ ] Testes de integração executados com sucesso
- [ ] Testes de carga realizados
- [ ] Testes de segurança (penetration testing) concluídos
- [ ] Validação de todos os fluxos críticos:
  - [ ] Registro de usuário
  - [ ] Login/Logout
  - [ ] Criação de conta bancária
  - [ ] Depósito
  - [ ] Saque
  - [ ] Transferência (se aplicável)
  - [ ] Relatório de transações
  - [ ] Cálculo de juros automático
- [ ] Validação de emails funcionando
- [ ] Backup e restore testados
- [ ] Monitoramento e alertas configurados
- [ ] Documentação de deploy atualizada
- [ ] Runbook de incidentes preparado

---

## 7. Ordem de Prioridade de Implementação

1. **🔴 CRÍTICO - Segurança (Seção 2.1):**
   - SECRET_KEY
   - DEBUG = False
   - ALLOWED_HOSTS

2. **🔴 CRÍTICO - Bug de Saldo Negativo (Seção 3.2):**
   - Implementar validação de saldo

3. **🟠 ALTA - Infraestrutura (Seções 2.2, 2.3, 2.4):**
   - Banco de dados de produção
   - Redis/Celery com autenticação
   - Gerenciador de processos

4. **🟡 MÉDIA - Arquivos Estáticos e Tarefas Agendadas (Seções 2.5, 3.4):**
   - Configuração de STATIC_ROOT
   - Servidor web para arquivos estáticos
   - Validação de timezone

5. **🟢 BAIXA - Otimizações e Regras de Negócio (Seções 3.1, 3.3):**
   - Revisão de valores mínimos
   - Configuração de email
   - Features adicionais de segurança

---

## 8. Variáveis de Ambiente Necessárias

Criar arquivo `.env` (não committar no repositório) com as seguintes variáveis:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=banking_system_prod
DB_USER=banking_user
DB_PASSWORD=secure-password-here
DB_HOST=localhost
DB_PORT=5432

# Redis/Celery
CELERY_BROKER_URL=redis://:password@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:password@localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Business Rules (opcional)
MINIMUM_DEPOSIT_AMOUNT=10
MINIMUM_WITHDRAWAL_AMOUNT=10
```

---

## Conclusão

Este prompt detalha todas as tarefas necessárias para transformar o sistema bancário de um ambiente de desenvolvimento/demonstração para uma aplicação enterprise pronta para produção. Siga a ordem de prioridade sugerida, começando sempre pelos itens críticos de segurança. Cada tarefa inclui explicação do "por quê" e referências específicas aos arquivos do projeto para facilitar a implementação.

**Lembre-se:** Nunca faça deploy em produção sem antes testar todas as mudanças em um ambiente de staging que replique fielmente o ambiente de produção.
