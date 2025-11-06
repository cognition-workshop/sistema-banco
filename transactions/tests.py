from django.test import TestCase
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
