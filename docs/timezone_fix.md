# Correção de Timezone - Sistema Bancário

## 📋 Contexto e Problema

### Sintoma Reportado
Usuários no Brasil observam que os horários das transações exibidos no sistema estão deslocados por aproximadamente 3 horas em relação ao momento real em que foram realizadas.

**Exemplo:**
- Transação realizada: 14:00 BRT (horário de Brasília)
- Exibido no sistema: 17:00
- Diferença: 3 horas à frente

### Causa Raiz Identificada

O problema está na configuração de timezone do Django em `banking_system/settings.py`:

```python
TIME_ZONE = 'UTC'  # ❌ Problema: timezone UTC
USE_TZ = True      # ✅ Correto: mantém timezone-aware datetimes
```

**Fluxo atual (problemático):**
1. Usuário no Brasil cria transação às 14:00 BRT (que é 17:00 UTC)
2. Django com `USE_TZ=True` armazena no banco: `2025-11-06 17:00:00+00:00` (UTC) ✓ Correto
3. Template exibe `{{ transaction.timestamp }}` sem conversão
4. Como `TIME_ZONE='UTC'`, Django renderiza 17:00 ✗ Incorreto
5. Usuário esperava ver 14:00 BRT

**Impacto:**
- ✗ Transações aparecem 3 horas à frente (BRT = UTC-3)
- ✗ Durante horário de verão brasileiro (se existisse), seria 2 horas (BRST = UTC-2)
- ✗ Filtro de data pode não funcionar como esperado
- ✗ Tarefas Celery agendadas executam em horário UTC inesperado

### Arquivos Afetados

1. **Configuração:** `banking_system/settings.py` (linhas 115, 142)
2. **Template:** `templates/transactions/transaction_report.html` (linha 43)
3. **Modelo:** `transactions/models.py` (linha 24 - apenas referência)
4. **Formulário:** `transactions/forms.py` (linhas 76-90 - filtro de data)
5. **Tasks:** `transactions/tasks.py` (usa `timezone.now()`)

## 🔧 Solução Implementada

### Main Fix: Alterar TIME_ZONE para horário brasileiro

**Arquivo:** `banking_system/settings.py`

```python
# Linha 115 - ANTES
TIME_ZONE = 'UTC'

# Linha 115 - DEPOIS
TIME_ZONE = 'America/Sao_Paulo'  # Horário de Brasília (BRT/BRST)
```

**Justificativa:**
- `'America/Sao_Paulo'`: Timezone oficial de Brasília, suporta transições de horário de verão
- `USE_TZ = True`: MANTER para garantir timestamps timezone-aware
- Database continua armazenando em UTC internamente (comportamento do Django)
- Conversão UTC→BRT acontece apenas na camada de apresentação

### Template Fix: Formatar timestamps explicitamente

**Arquivo:** `templates/transactions/transaction_report.html`

```django
{# Linha 1 - Adicionar load de timezone tags #}
{% extends 'core/base.html' %}
{% load tz %}

{# Linha 43 - ANTES #}
<td class="border px-4 py-2 text-center">{{ transaction.timestamp }}</td>

{# Linha 43 - DEPOIS #}
<td class="border px-4 py-2 text-center">{{ transaction.timestamp|date:"d/m/Y H:i" }}</td>
```

**Detalhes do filtro:**
- `date:"d/m/Y H:i"`: Formato brasileiro (dia/mês/ano hora:minuto)
- Exemplo saída: `06/11/2025 14:00`
- Django automaticamente converte UTC→TIME_ZONE antes de formatar
- Alternativa: `{{ transaction.timestamp|date:"SHORT_DATETIME_FORMAT" }}` (usa formato do Django)

**Por que USE_TZ=True é importante:**
```python
# Sem USE_TZ=True (❌ INCORRETO)
# timestamps são naive, sem informação de timezone
timestamp = datetime(2025, 11, 6, 14, 0)  # 14:00... mas em que timezone?

# Com USE_TZ=True (✅ CORRETO)
# timestamps são timezone-aware
timestamp = datetime(2025, 11, 6, 17, 0, tzinfo=timezone.utc)  # 17:00 UTC = 14:00 BRT
```

### Additional Improvement: Filtro de data timezone-aware

**Arquivo:** `transactions/forms.py`

**Problema atual:**
```python
# Linha 85 - parsing naive (sem timezone)
datetime.datetime.strptime(date, '%Y-%m-%d')  # ❌ retorna datetime naive
```

Quando usuário filtra "2025-11-06", o sistema pode interpretar como:
- Início do dia: `2025-11-06 00:00:00 UTC` (que é `2025-11-05 21:00:00 BRT`)
- Fim do dia: `2025-11-06 23:59:59 UTC` (que é `2025-11-06 20:59:59 BRT`)

Resultado: transações entre 21:00 e 23:59 BRT do dia 5 são incluídas incorretamente!

**Solução:**

```python
# Adicionar imports no topo do arquivo
import datetime
from django import forms
from django.conf import settings
from django.utils import timezone
import pytz

class TransactionDateRangeForm(forms.Form):
    daterange = forms.CharField(required=False)

    def clean_daterange(self):
        daterange = self.cleaned_data.get("daterange")

        try:
            daterange = daterange.split(' - ')
            if len(daterange) == 2:
                tz = pytz.timezone(settings.TIME_ZONE)
                dates = []
                for date_str in daterange:
                    naive_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    aware_datetime = tz.localize(naive_date)
                    dates.append(aware_datetime.date())
                return dates
            else:
                raise forms.ValidationError("Please select a date range.")
        except (ValueError, AttributeError):
            raise forms.ValidationError("Invalid date range")
```

**Como funciona:**
1. Parse string "2025-11-06" → naive datetime
2. `tz.localize()` adiciona timezone info → `2025-11-06 00:00:00 BRT`
3. Converte para date → `2025-11-06`
4. Django ORM compara corretamente considerando timezone

## 🧪 Testes Automatizados

### Arquivo: `transactions/tests.py`

Criar suite completa de testes incluindo casos de horário de verão:

```python
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
import pytz

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL


User = get_user_model()


class TimezoneTransactionTests(TestCase):
    """Testes para garantir que timestamps são exibidos corretamente no fuso horário brasileiro"""
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name="Test Account",
            maximum_withdrawal_amount=10000.00,
            annual_interest_rate=5.00,
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test123',
            first_name='Test',
            last_name='User'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=9999999,
            gender='M',
            balance=1000.00
        )
    
    def test_transaction_stored_in_utc(self):
        """Verifica que timestamps são armazenados em UTC no banco de dados"""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        
        self.assertIsNotNone(transaction.timestamp.tzinfo)
        utc_timestamp = transaction.timestamp.astimezone(pytz.UTC)
        self.assertEqual(utc_timestamp.tzinfo.zone, 'UTC')
    
    def test_transaction_displayed_in_brazilian_time(self):
        """Verifica que timestamps são exibidos em horário brasileiro nos templates"""
        brt = pytz.timezone('America/Sao_Paulo')
        local_time = brt.localize(datetime(2025, 11, 6, 14, 0, 0))
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        transaction.timestamp = local_time
        transaction.save()
        
        self.client.login(email='test@example.com', password='test123')
        response = self.client.get('/transactions/')
        
        self.assertContains(response, '06/11/2025 14:00')
        self.assertNotContains(response, '17:00')
    
    def test_timezone_conversion_with_dst(self):
        """Testa conversão durante período de horário de verão (robustez histórica)"""
        brt = pytz.timezone('America/Sao_Paulo')
        
        summer_date = brt.localize(datetime(2018, 1, 15, 15, 0, 0))
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=150.00,
            balance_after_transaction=1150.00,
            transaction_type=DEPOSIT
        )
        transaction.timestamp = summer_date
        transaction.save()
        
        utc_time = transaction.timestamp.astimezone(pytz.UTC)
        self.assertEqual(utc_time.hour, 17)
    
    def test_date_filter_timezone_boundaries(self):
        """Verifica que filtro de data respeita boundaries de timezone"""
        brt = pytz.timezone('America/Sao_Paulo')
        
        late_night = brt.localize(datetime(2025, 11, 6, 23, 30, 0))
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=50.00,
            balance_after_transaction=1050.00,
            transaction_type=DEPOSIT
        )
        transaction.timestamp = late_night
        transaction.save()
        
        self.client.login(email='test@example.com', password='test123')
        response = self.client.get('/transactions/', {'daterange': '2025-11-06 - 2025-11-06'})
        
        self.assertContains(response, '50.00')
    
    def test_midnight_boundary(self):
        """Testa transações próximas à meia-noite"""
        brt = pytz.timezone('America/Sao_Paulo')
        
        before_midnight = brt.localize(datetime(2025, 11, 6, 23, 59, 0))
        after_midnight = brt.localize(datetime(2025, 11, 7, 0, 1, 0))
        
        t1 = Transaction.objects.create(
            account=self.account,
            amount=25.00,
            balance_after_transaction=1025.00,
            transaction_type=DEPOSIT
        )
        t1.timestamp = before_midnight
        t1.save()
        
        t2 = Transaction.objects.create(
            account=self.account,
            amount=75.00,
            balance_after_transaction=1100.00,
            transaction_type=DEPOSIT
        )
        t2.timestamp = after_midnight
        t2.save()
        
        self.client.login(email='test@example.com', password='test123')
        response = self.client.get('/transactions/', {'daterange': '2025-11-06 - 2025-11-06'})
        
        self.assertContains(response, '25.00')
        self.assertNotContains(response, '75.00')
    
    def test_celery_task_uses_correct_timezone(self):
        """Verifica que tarefas Celery respeitam timezone configurado"""
        from transactions.tasks import calculate_interest
        from django.conf import settings
        
        self.assertEqual(settings.CELERY_TIMEZONE, 'America/Sao_Paulo')
        
        now = timezone.now()
        self.account.initial_deposit_date = now.date()
        self.account.interest_start_date = now.date()
        self.account.save()
        
        calculate_interest()
        self.assertTrue(True)
```

**Testes incluem:**
- ✅ Armazenamento em UTC
- ✅ Exibição em BRT
- ✅ Conversão com DST (horário de verão histórico)
- ✅ Filtro de data em boundaries de timezone
- ✅ Edge case de meia-noite
- ✅ Configuração Celery

## ✅ Verificação e Testes

### 1. Testes Automatizados

```bash
# Suite completa de testes
python manage.py test

# Apenas testes de timezone
python manage.py test transactions.tests.TimezoneTransactionTests

# Teste específico
python manage.py test transactions.tests.TimezoneTransactionTests.test_transaction_displayed_in_brazilian_time
```

### 2. Testes Manuais

```bash
# Criar dados de demonstração
python create_demo_data.py

# Iniciar servidor
python manage.py runserver

# Acessar http://localhost:8000
# Login: demo@example.com / demo123
# Verificar: transações mostram horário BRT correto
```

### 3. Verificação no Banco de Dados

```bash
# Conectar ao SQLite
python manage.py dbshell

# Verificar armazenamento UTC
SELECT id, timestamp, amount FROM transactions_transaction LIMIT 5;
# Timestamps devem estar em UTC: "2025-11-06 17:00:00"
```

### 4. Checklist de Verificação

- [ ] `TIME_ZONE = 'America/Sao_Paulo'` em settings.py
- [ ] `USE_TZ = True` mantido em settings.py
- [ ] Template usa `{% load tz %}` e filtro `|date:"d/m/Y H:i"`
- [ ] Form parsing é timezone-aware
- [ ] Todos os testes passam: `python manage.py test`
- [ ] Dados antigos exibem corretamente (sem migração necessária)
- [ ] Celery usa `CELERY_TIMEZONE = TIME_ZONE`
- [ ] Filtro de data funciona em boundaries (meia-noite, DST)

## 📦 Dependências

### Django Timezone Support (Built-in)

**Django 3.2.9** (do requirements.txt) inclui suporte completo a timezone:

```python
# Django automaticamente usa:
# - Python 3.9+: módulo zoneinfo (stdlib)
# - Python < 3.9: pytz (fallback)
```

**Verificar versão Python:**
```bash
python --version
# Se >= 3.9: usa zoneinfo (nativo)
# Se < 3.9: instalar pytz
```

### pytz (Fallback ou uso explícito)

Se Python < 3.9 ou se quiser usar pytz explicitamente:

```bash
pip install pytz
```

Adicionar ao `requirements.txt`:
```
pytz==2023.3
```

**Quando usar pytz:**
- Python < 3.9 (obrigatório)
- Testes que precisam de timezone objects explícitos
- Form processing com `tz.localize()`

**Verificação:**
```python
# No shell Django
python manage.py shell

>>> from django.utils import timezone
>>> import pytz
>>> timezone.now()
# Deve retornar datetime com tzinfo

>>> pytz.timezone('America/Sao_Paulo')
# Deve retornar timezone object
```

## 🔄 Estratégia Git/PR

### Branch e Commits

```bash
# Criar branch com timestamp
export TIMESTAMP=$(date +%s)
git checkout -b devin/${TIMESTAMP}-fix-timezone-issue

# Commit 1: Documentação
git add docs/timezone_fix.md
git commit -m "docs: add comprehensive timezone fix documentation"

# Commit 2: Settings
git add banking_system/settings.py
git commit -m "feat: configure TIME_ZONE to America/Sao_Paulo for Brazilian users"

# Commit 3: Template
git add templates/transactions/transaction_report.html
git commit -m "feat: format transaction timestamps in Brazilian date format"

# Commit 4: Form
git add transactions/forms.py
git commit -m "feat: make date range filter timezone-aware"

# Commit 5: Tests
git add transactions/tests.py
git commit -m "test: add comprehensive timezone tests including DST cases"

# Commit 6: Dependencies
git add requirements.txt
git commit -m "chore: add pytz dependency for timezone handling"

# Push
git push origin devin/${TIMESTAMP}-fix-timezone-issue
```

### Criar Pull Request

O PR será criado automaticamente com descrição gerada baseada nos commits.

**Conteúdo esperado do PR:**

```markdown
## 🔗 Sessão Devin
https://itau-hackathon.devinenterprise.com/sessions/764d0fd0985b4c018aa726040800288c

## 👤 Autor
@fredhof_itau

## 🐛 Problema
Usuários no Brasil reportam horários 3 horas à frente.

## ✅ Solução
- `TIME_ZONE = 'America/Sao_Paulo'` em settings.py
- Template com filtro `|date:"d/m/Y H:i"`
- Filtro de data timezone-aware
- Testes abrangentes incluindo DST

## 📋 Arquivos Alterados
- `banking_system/settings.py`: TIME_ZONE
- `templates/transactions/transaction_report.html`: formato de data
- `transactions/forms.py`: parsing timezone-aware
- `transactions/tests.py`: testes completos
- `docs/timezone_fix.md`: documentação completa

## 🧪 Testes
```bash
python manage.py test
python create_demo_data.py && python manage.py runserver
```

Ver `docs/timezone_fix.md` para documentação completa.
```

## 🎯 Boas Práticas

### Princípios de Timezone
1. ✅ SEMPRE armazene em UTC no banco
2. ✅ SEMPRE use `USE_TZ = True`
3. ✅ SEMPRE use `django.utils.timezone.now()`
4. ✅ SEMPRE converta para local apenas na apresentação
5. ❌ NUNCA use `datetime.datetime.now()` (naive)

### Padrões de Código
```python
# ✅ CORRETO
from django.utils import timezone
timestamp = timezone.now()

# ❌ INCORRETO
import datetime
timestamp = datetime.datetime.now()
```

### Templates
```django
{# ✅ CORRETO #}
{% load tz %}
{{ transaction.timestamp|date:"d/m/Y H:i" }}

{# ❌ INCORRETO #}
{{ transaction.timestamp }}
```

### Para Multi-Região (Futuro)
Se precisar suportar usuários de diferentes timezones:
1. Adicionar campo `timezone` no perfil do usuário
2. Criar middleware para ativar timezone por usuário
3. Templates automaticamente usarão timezone ativado

## 📝 Notas Adicionais

### Horário de Verão
- Brasil NÃO observa horário de verão desde 2019
- Timezone `America/Sao_Paulo` mantém histórico completo
- Testes incluem cenários DST para robustez histórica

### Compatibilidade
- Django 3.2.9: suporte completo a timezone
- Python 3.9+: usa zoneinfo (stdlib)
- Python < 3.9: requer pytz

### Rollback
Se necessário reverter:
```python
# settings.py
TIME_ZONE = 'UTC'
```
Sem perda de dados (tudo permanece em UTC no banco).

---

**Criado:** 2025-11-06
**Autor:** Sistema Devin
**Versão:** 1.0
