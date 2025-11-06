from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType, VIEW_REPORTS
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class TransactionMonitoringViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=3.5,
            interest_calculation_per_year=12
        )
        
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[VIEW_REPORTS]
        )
        
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
        
        Transaction.objects.create(
            account=self.account,
            amount=500,
            balance_after_transaction=1500,
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=self.account,
            amount=200,
            balance_after_transaction=1300,
            transaction_type=WITHDRAWAL
        )
    
    def test_transaction_monitoring_requires_admin(self):
        self.client.login(username='user@example.com', password='testpass123')
        response = self.client.get('/transactions/admin-portal/transactions/')
        self.assertEqual(response.status_code, 302)
    
    def test_transaction_monitoring_requires_view_reports_permission(self):
        admin_no_perm = User.objects.create_user(
            email='admin_no_perm@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[]
        )
        self.client.login(username='admin_no_perm@example.com', password='testpass123')
        response = self.client.get('/transactions/admin-portal/transactions/')
        self.assertEqual(response.status_code, 403)
    
    def test_transaction_monitoring_loads_with_permission(self):
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get('/transactions/admin-portal/transactions/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transaction Monitoring')
    
    def test_transaction_monitoring_shows_transactions(self):
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get('/transactions/admin-portal/transactions/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user@example.com')
        self.assertEqual(len(response.context['transactions']), 2)
    
    def test_transaction_type_filter(self):
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get(f'/transactions/admin-portal/transactions/?transaction_type={DEPOSIT}')
        self.assertEqual(response.status_code, 200)
        transactions = response.context['transactions']
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].transaction_type, DEPOSIT)
    
    def test_amount_filters(self):
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get('/transactions/admin-portal/transactions/?min_amount=300')
        self.assertEqual(response.status_code, 200)
        transactions = response.context['transactions']
        self.assertEqual(len(transactions), 1)
        self.assertEqual(float(transactions[0].amount), 500.0)
    
    def test_csv_export(self):
        self.client.login(username='admin@example.com', password='testpass123')
        response = self.client.get('/transactions/admin-portal/transactions/export/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        content = response.content.decode('utf-8')
        self.assertIn('Timestamp', content)
        self.assertIn('user@example.com', content)
    
    def test_csv_export_requires_permission(self):
        admin_no_perm = User.objects.create_user(
            email='admin_no_perm@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[]
        )
        self.client.login(username='admin_no_perm@example.com', password='testpass123')
        response = self.client.get('/transactions/admin-portal/transactions/export/')
        self.assertEqual(response.status_code, 403)
