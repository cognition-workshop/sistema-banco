import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from transactions.constants import WITHDRAWAL
from transactions.models import Transaction

User = get_user_model()


@pytest.mark.django_db
class TestWithdrawView:
    
    def test_successful_withdrawal(self, client, demo_account):
        """Saque válido deve atualizar o saldo corretamente"""
        initial_balance = demo_account.balance
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': Decimal('50.00'),
            'transaction_type': WITHDRAWAL
        })
        
        demo_account.refresh_from_db()
        assert demo_account.balance == initial_balance - Decimal('50.00')
        assert response.status_code == 302
    
    def test_withdrawal_equal_to_balance(self, client, demo_account):
        """Saque igual ao saldo deve zerar o saldo"""
        initial_balance = demo_account.balance
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': initial_balance,
            'transaction_type': WITHDRAWAL
        })
        
        demo_account.refresh_from_db()
        assert demo_account.balance == Decimal('0.00')
        assert response.status_code == 302
    
    def test_withdrawal_above_balance_rejected(self, client, demo_account):
        """Tentativa de saque acima do saldo deve ser rejeitada"""
        initial_balance = demo_account.balance
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': Decimal('150.00'),
            'transaction_type': WITHDRAWAL
        })
        
        demo_account.refresh_from_db()
        assert demo_account.balance == initial_balance
        assert response.status_code == 200
        assert 'Fundos insuficientes' in response.content.decode('utf-8')
    
    def test_invalid_amount_rejected(self, client, demo_account):
        """Valor inválido deve ser rejeitado"""
        initial_balance = demo_account.balance
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': Decimal('0'),
            'transaction_type': WITHDRAWAL
        })
        
        demo_account.refresh_from_db()
        assert demo_account.balance == initial_balance
        assert response.status_code == 200
        assert 'Valor de saque inválido' in response.content.decode('utf-8')
    
    def test_negative_amount_rejected(self, client, demo_account):
        """Valor negativo deve ser rejeitado"""
        initial_balance = demo_account.balance
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': Decimal('-10.00'),
            'transaction_type': WITHDRAWAL
        })
        
        demo_account.refresh_from_db()
        assert demo_account.balance == initial_balance
        assert response.status_code == 200
        assert 'Valor de saque inválido' in response.content.decode('utf-8')
    
    def test_withdrawal_updates_transaction_record(self, client, demo_account):
        """Saque deve criar registro de transação"""
        initial_count = Transaction.objects.filter(
            account=demo_account,
            transaction_type=WITHDRAWAL
        ).count()
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': Decimal('30.00'),
            'transaction_type': WITHDRAWAL
        })
        
        transactions = Transaction.objects.filter(
            account=demo_account,
            transaction_type=WITHDRAWAL
        )
        assert transactions.count() == initial_count + 1
        assert transactions.last().amount == Decimal('30.00')
    
    def test_failed_withdrawal_does_not_create_transaction(self, client, demo_account):
        """Saque rejeitado não deve criar registro de transação"""
        initial_count = Transaction.objects.filter(
            account=demo_account
        ).count()
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': Decimal('200.00'),
            'transaction_type': WITHDRAWAL
        })
        
        final_count = Transaction.objects.filter(
            account=demo_account
        ).count()
        assert final_count == initial_count
    
    def test_withdrawal_boundary_one_cent_above_balance(self, client, demo_account):
        """Saque de 1 centavo acima do saldo deve ser rejeitado"""
        initial_balance = demo_account.balance
        
        response = client.post(reverse('transactions:withdraw_money'), {
            'amount': initial_balance + Decimal('0.01'),
            'transaction_type': WITHDRAWAL
        })
        
        demo_account.refresh_from_db()
        assert demo_account.balance == initial_balance
        assert response.status_code == 200
        assert 'Fundos insuficientes' in response.content.decode('utf-8')
