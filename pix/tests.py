from django.test import TestCase
from django.contrib.auth import get_user_model
from pix.models import ChavePix, TransacaoPix, TipoChavePix
from accounts.models import UserBankAccount, BankAccountType
from django.core.exceptions import ValidationError

User = get_user_model()


class PixKeyTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test',
            maximum_withdrawal_amount=1000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(email='test@test.com', password='test123')
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
    
    def test_create_pix_key(self):
        """Test creating a PIX key"""
        chave = ChavePix.objects.create(
            conta=self.account,
            tipo=TipoChavePix.EMAIL,
            valor='test@test.com'
        )
        self.assertTrue(chave.ativa)
    
    def test_pix_key_limit(self):
        """Test 5 PIX keys limit per account"""
        for i in range(5):
            ChavePix.objects.create(
                conta=self.account,
                tipo=TipoChavePix.EMAIL,
                valor=f'test{i}@test.com'
            )
        
        with self.assertRaises(ValidationError):
            chave = ChavePix(
                conta=self.account,
                tipo=TipoChavePix.EMAIL,
                valor='test6@test.com'
            )
            chave.save()
