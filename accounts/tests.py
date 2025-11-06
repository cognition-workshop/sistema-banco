import pytest
from django.test import Client
from django.urls import reverse
from decimal import Decimal
from .models import User, BankAccountType, UserBankAccount, UserAddress


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert str(user) == 'test@example.com'
    
    def test_user_balance_property(self):
        user = User.objects.create_user(email='test@example.com', password='test123')
        account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1234567890,
            gender='M',
            balance=Decimal('1000.00')
        )
        assert user.balance == Decimal('1000.00')


@pytest.mark.django_db
class TestBankAccountType:
    def test_calculate_interest(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        principal = Decimal('1000.00')
        interest = account_type.calculate_interest(principal)
        assert interest > 0
        assert isinstance(interest, Decimal)


@pytest.mark.django_db
class TestUserRegistrationView:
    def test_registration_page_loads(self):
        client = Client()
        response = client.get(reverse('accounts:user_registration'))
        assert response.status_code == 200
        assert 'registration_form' in response.context
    
    def test_registration_redirects_if_authenticated(self):
        user = User.objects.create_user(email='test@example.com', password='test123')
        client = Client()
        client.force_login(user)
        response = client.get(reverse('accounts:user_registration'))
        assert response.status_code == 302
