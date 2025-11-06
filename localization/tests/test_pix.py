from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType
from localization.models import ChavePIX, TransacaoPIX
from localization.services.pix_service import PIXService

User = get_user_model()


class PIXServiceTestCase(TestCase):
    """Testes para serviço PIX"""
    
    def setUp(self):
        """Setup para testes"""
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='test123'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='test123'
        )
        
        self.account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1001,
            gender='M',
            balance=Decimal('1000.00')
        )
        self.account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.account_type,
            account_no=1002,
            gender='F',
            balance=Decimal('500.00')
        )
        
        self.chave_pix = ChavePIX.objects.create(
            usuario=self.user2,
            tipo='EMAIL',
            chave='user2@test.com'
        )
    
    def test_cadastrar_chave_pix(self):
        """Testa cadastro de chave PIX"""
        chave = PIXService.cadastrar_chave(
            usuario=self.user1,
            tipo='CPF',
            chave='12345678901'
        )
        self.assertEqual(chave.usuario, self.user1)
        self.assertEqual(chave.tipo, 'CPF')
        self.assertTrue(chave.ativa)
    
    def test_transferencia_pix_sucesso(self):
        """Testa transferência PIX bem-sucedida"""
        valor = Decimal('100.00')
        saldo_inicial_origem = self.account1.balance
        saldo_inicial_destino = self.account2.balance
        
        transacao = PIXService.realizar_transferencia(
            conta_origem=self.account1,
            chave_destino=self.chave_pix.chave,
            valor=valor,
            descricao='Teste'
        )
        
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()
        
        self.assertEqual(transacao.status, 'CONCLUIDA')
        self.assertEqual(self.account1.balance, saldo_inicial_origem - valor)
        self.assertEqual(self.account2.balance, saldo_inicial_destino + valor)
    
    def test_transferencia_pix_saldo_insuficiente(self):
        """Testa transferência PIX com saldo insuficiente"""
        with self.assertRaises(Exception):
            PIXService.realizar_transferencia(
                conta_origem=self.account1,
                chave_destino=self.chave_pix.chave,
                valor=Decimal('2000.00'),
                descricao='Teste'
            )
    
    def test_gerar_qr_code(self):
        """Testa geração de QR Code PIX"""
        resultado = PIXService.gerar_qr_code(
            chave_pix='test@test.com',
            valor=Decimal('50.00'),
            descricao='Teste QR'
        )
        self.assertIn('qr_code', resultado)
        self.assertIn('payload', resultado)
        self.assertIn('PIX:', resultado['payload'])
