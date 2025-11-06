from decimal import Decimal
from datetime import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from localization.services.report_service import ReportService

User = get_user_model()


class ReportServiceTestCase(TestCase):
    """Testes para serviço de relatórios"""
    
    def setUp(self):
        """Setup para testes"""
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@test.com',
            password='test123',
            first_name='Test',
            last_name='User'
        )
        self.user.cpf = '12345678901'
        self.user.save()
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1001,
            gender='M',
            balance=Decimal('1000.00')
        )
        
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('100.00'),
            transaction_type=DEPOSIT,
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.get_current_timezone())
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('50.00'),
            transaction_type=WITHDRAWAL,
            timestamp=datetime(2024, 3, 20, tzinfo=timezone.get_current_timezone())
        )
    
    def test_gerar_relatorio_irpf(self):
        """Testa geração de relatório IRPF"""
        relatorio = ReportService.gerar_relatorio_irpf(self.user, 2024)
        
        self.assertEqual(relatorio['ano'], 2024)
        self.assertEqual(relatorio['usuario'], self.user)
        self.assertGreater(relatorio['quantidade_transacoes'], 0)
    
    def test_exportar_csv(self):
        """Testa exportação para CSV"""
        relatorio = ReportService.gerar_relatorio_irpf(self.user, 2024)
        csv_data = ReportService.exportar_csv(relatorio)
        
        self.assertIn('IRPF', csv_data)
        self.assertIn(self.user.cpf, csv_data)
    
    def test_exportar_pdf(self):
        """Testa exportação para PDF"""
        relatorio = ReportService.gerar_relatorio_irpf(self.user, 2024)
        pdf_data = ReportService.exportar_pdf(relatorio)
        
        self.assertIsNotNone(pdf_data)
        self.assertGreater(len(pdf_data), 0)
