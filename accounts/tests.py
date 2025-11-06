import pytest
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
    
    def test_user_balance_property(self, user_with_account):
        assert user_with_account.balance == 1000
    
    def test_user_without_account_balance(self, user):
        assert user.balance == 0


@pytest.mark.django_db
class TestBankAccountType:
    def test_calculate_interest(self, bank_account_type):
        from decimal import Decimal
        interest = bank_account_type.calculate_interest(1000)
        assert interest > 0
        assert isinstance(interest, Decimal)


@pytest.mark.django_db  
class TestUserBankAccount:
    def test_account_creation(self, user_with_account):
        account = user_with_account.account
        assert account.balance == 1000
        assert account.user == user_with_account
    
    def test_get_interest_calculation_months(self, user_with_account):
        from datetime import date
        account = user_with_account.account
        account.interest_start_date = date(2024, 1, 1)
        account.save()
        months = account.get_interest_calculation_months()
        assert len(months) == 12


@pytest.mark.django_db
class TestAccountsAPI:
    def test_list_users_unauthenticated(self, client):
        response = client.get('/api/users/')
        assert response.status_code == 403
    
    def test_list_users_authenticated(self, client, user_with_account):
        client.force_login(user_with_account)
        response = client.get('/api/users/')
        assert response.status_code == 200
    
    def test_get_user_account(self, client, user_with_account):
        client.force_login(user_with_account)
        response = client.get(f'/api/users/{user_with_account.id}/account/')
        assert response.status_code == 200
        data = response.json()
        assert 'account_no' in data
        assert data['balance'] == '1000.00'

# Create your tests here.
