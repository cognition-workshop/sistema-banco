from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType
from localization.models import AuditLog
from localization.services.audit_service import AuditService

User = get_user_model()


class AuditServiceTestCase(TestCase):
    """Testes para serviço de auditoria"""
    
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
            password='test123'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_registrar_operacao(self):
        """Testa registro de operação no audit log"""
        registro = AuditService.registrar_operacao(
            usuario=self.user,
            conta=self.account,
            tipo_operacao='DEPOSITO',
            valor=Decimal('100.00'),
            saldo_anterior=Decimal('900.00'),
            saldo_posterior=Decimal('1000.00'),
            descricao='Teste de depósito'
        )
        
        self.assertIsNotNone(registro.hash_registro)
        self.assertEqual(registro.usuario, self.user)
        self.assertEqual(registro.tipo_operacao, 'DEPOSITO')
    
    def test_verificar_integridade(self):
        """Testa verificação de integridade de registro"""
        registro = AuditService.registrar_operacao(
            usuario=self.user,
            conta=self.account,
            tipo_operacao='SAQUE',
            valor=Decimal('50.00'),
            saldo_anterior=Decimal('1000.00'),
            saldo_posterior=Decimal('950.00'),
            descricao='Teste de saque'
        )
        
        resultado = AuditService.verificar_integridade(registro.id)
        self.assertTrue(resultado['valido'])
    
    def test_encadeamento_audit_log(self):
        """Testa encadeamento de registros de audit log"""
        registro1 = AuditService.registrar_operacao(
            usuario=self.user,
            conta=self.account,
            tipo_operacao='DEPOSITO',
            valor=Decimal('100.00'),
            saldo_anterior=Decimal('900.00'),
            saldo_posterior=Decimal('1000.00'),
            descricao='Primeiro'
        )
        
        registro2 = AuditService.registrar_operacao(
            usuario=self.user,
            conta=self.account,
            tipo_operacao='SAQUE',
            valor=Decimal('50.00'),
            saldo_anterior=Decimal('1000.00'),
            saldo_posterior=Decimal('950.00'),
            descricao='Segundo'
        )
        
        self.assertEqual(registro2.hash_anterior, registro1.hash_registro)
