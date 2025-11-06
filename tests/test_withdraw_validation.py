import pytest
from decimal import Decimal
from django import forms
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL


@pytest.mark.django_db
class TestWithdrawValidation:
    
    def test_withdraw_equal_to_balance(self, user_account):
        """Saque igual ao saldo deve ser permitido"""
        form = WithdrawForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=user_account
        )
        assert form.is_valid()
        assert form.cleaned_data['amount'] == Decimal('100.00')
    
    def test_withdraw_less_than_balance(self, user_account):
        """Saque menor que o saldo deve ser permitido"""
        form = WithdrawForm(
            data={'amount': Decimal('50.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=user_account
        )
        assert form.is_valid()
    
    def test_withdraw_greater_than_balance_raises_error(self, user_account):
        """Saque maior que o saldo deve ser rejeitado com mensagem clara"""
        form = WithdrawForm(
            data={'amount': Decimal('100.01')},
            initial={'transaction_type': WITHDRAWAL},
            account=user_account
        )
        assert not form.is_valid()
        assert 'amount' in form.errors
        assert 'Fundos insuficientes' in str(form.errors['amount'])
    
    def test_withdraw_from_zero_balance(self, account_factory):
        """Qualquer saque de conta com saldo zero deve ser rejeitado"""
        account = account_factory(balance=Decimal('0.00'))
        form = WithdrawForm(
            data={'amount': Decimal('0.01')},
            initial={'transaction_type': WITHDRAWAL},
            account=account
        )
        assert not form.is_valid()
        assert 'Fundos insuficientes' in str(form.errors['amount'])
    
    def test_withdraw_one_cent_above_balance(self, user_account):
        """Saque de 1 centavo acima do saldo deve ser rejeitado"""
        user_account.balance = Decimal('100.00')
        user_account.save()
        
        form = WithdrawForm(
            data={'amount': Decimal('100.01')},
            initial={'transaction_type': WITHDRAWAL},
            account=user_account
        )
        assert not form.is_valid()
        assert 'Fundos insuficientes' in str(form.errors['amount'])
    
    @pytest.mark.parametrize('amount', [
        Decimal('0'),
        Decimal('0.00'),
        Decimal('-1.00'),
        Decimal('-10.50'),
    ])
    def test_invalid_amounts_rejected(self, user_account, amount):
        """Valores inválidos (<=0) devem ser rejeitados"""
        form = WithdrawForm(
            data={'amount': amount},
            initial={'transaction_type': WITHDRAWAL},
            account=user_account
        )
        assert not form.is_valid()
        assert 'amount' in form.errors
        assert 'Valor de saque inválido' in str(form.errors['amount'])
    
    def test_decimal_precision_boundary_cases(self, account_factory):
        """Testes de precisão com Decimal"""
        account = account_factory(balance=Decimal('99.99'))
    
        form = WithdrawForm(
            data={'amount': Decimal('99.99')},
            initial={'transaction_type': WITHDRAWAL},
            account=account
        )
        assert form.is_valid()
        
        form = WithdrawForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=account
        )
        assert not form.is_valid()
        assert 'Fundos insuficientes' in str(form.errors['amount'])
    
    def test_minimum_withdrawal_still_enforced(self, user_account):
        """Validação de valor mínimo deve continuar funcionando"""
        form = WithdrawForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=user_account
        )
        assert not form.is_valid()
        assert 'amount' in form.errors
        assert 'You can withdraw at least' in str(form.errors['amount'])
    
    def test_maximum_withdrawal_still_enforced(self, account_factory):
        """Validação de valor máximo deve continuar funcionando"""
        account = account_factory(balance=Decimal('10000.00'))
        form = WithdrawForm(
            data={'amount': Decimal('6000.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=account
        )
        assert not form.is_valid()
        assert 'amount' in form.errors
        assert 'You can withdraw at most' in str(form.errors['amount'])
