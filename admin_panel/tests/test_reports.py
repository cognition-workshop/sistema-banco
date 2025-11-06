from django.test import TestCase
from django.contrib.auth import get_user_model
from admin_panel.reports import ReportGenerator, REPORTLAB_AVAILABLE
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from unittest.mock import patch
import unittest

User = get_user_model()


class ReportGeneratorTest(TestCase):
    
    def setUp(self):
        self.patcher = patch('admin_panel.signals.detect_fraud_for_transaction.delay')
        self.mock_delay = self.patcher.start()
        
        self.generator = ReportGenerator()
        
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
        
        self.transaction = Transaction.objects.create(
            account=self.account,
            amount=500,
            balance_after_transaction=1500,
            transaction_type=1
        )
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_generate_transaction_csv(self):
        transactions = Transaction.objects.all()
        csv_data = self.generator.generate_transaction_csv(transactions)
        
        self.assertIsInstance(csv_data, str)
        self.assertIn('ID', csv_data)
        self.assertIn('Account Number', csv_data)
    
    @unittest.skipUnless(REPORTLAB_AVAILABLE, "reportlab not installed")
    def test_generate_transaction_pdf(self):
        transactions = Transaction.objects.all()
        pdf_data = self.generator.generate_transaction_pdf(transactions)
        
        self.assertIsInstance(pdf_data, bytes)
        self.assertGreater(len(pdf_data), 0)
    
    @unittest.skipIf(REPORTLAB_AVAILABLE, "reportlab is installed")
    def test_generate_transaction_pdf_without_reportlab(self):
        transactions = Transaction.objects.all()
        with self.assertRaises(ImportError) as context:
            self.generator.generate_transaction_pdf(transactions)
        self.assertIn("reportlab is not installed", str(context.exception))
