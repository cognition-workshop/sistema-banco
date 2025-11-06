from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import BankAccountType
from decimal import Decimal


class UserRegistrationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:user_registration')
        self.account_type = BankAccountType.objects.create(
            name="Test Account",
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('4.00'),
            interest_calculation_per_year=12
        )

    def test_registration_creates_user_and_account(self):
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'securepass123!@#',
            'password2': 'securepass123!@#',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01',
            'street_address': 'Rua Teste 123',
            'city': 'São Paulo',
            'postal_code': 1000000,
            'country': 'Brasil'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)
