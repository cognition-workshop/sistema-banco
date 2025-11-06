import pytest
from django.urls import reverse
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL


@pytest.mark.django_db
class TestTransactionModel:
    def test_transaction_creation(self, transaction):
        assert transaction.amount == 100
        assert transaction.balance_after_transaction == 1100
        assert transaction.transaction_type == DEPOSIT
    
    def test_transaction_ordering(self, user_with_account):
        account = user_with_account.account
        t1 = Transaction.objects.create(
            account=account, amount=50, 
            balance_after_transaction=1050, transaction_type=DEPOSIT
        )
        t2 = Transaction.objects.create(
            account=account, amount=100,
            balance_after_transaction=1150, transaction_type=DEPOSIT
        )
        transactions = list(Transaction.objects.all())
        assert transactions[0].timestamp < transactions[1].timestamp


@pytest.mark.django_db
class TestTransactionViews:
    def test_transaction_report_view(self, client, user_with_account, transaction):
        response = client.get(reverse('transactions:transaction_report'))
        assert response.status_code == 200
    
    def test_deposit_view_get(self, client, bank_account_type):
        from django.contrib.auth import get_user_model
        from accounts.models import UserBankAccount, UserAddress
        User = get_user_model()
        demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demo123',
            first_name='Demo',
            last_name='User'
        )
        account = UserBankAccount.objects.create(
            user=demo_user,
            account_type=bank_account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
        UserAddress.objects.create(
            user=demo_user,
            street_address='123 Demo St',
            city='Demo City',
            postal_code=12345,
            country='Demo Country'
        )
        response = client.get(reverse('transactions:deposit_money'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestTransactionAPI:
    def test_list_transactions_unauthenticated(self, client):
        response = client.get('/api/transactions/')
        assert response.status_code == 403
    
    def test_list_transactions_authenticated(self, client, user_with_account, transaction):
        client.force_login(user_with_account)
        response = client.get('/api/transactions/')
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert len(data['results']) == 1
    
    def test_transaction_summary(self, client, user_with_account, transaction):
        client.force_login(user_with_account)
        response = client.get('/api/transactions/summary/')
        assert response.status_code == 200
        data = response.json()
        assert data['total_transactions'] == 1
        assert data['total_deposits'] == 1
        assert data['total_withdrawals'] == 0

# Create your tests here.
