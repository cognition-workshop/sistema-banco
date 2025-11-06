from django.core.management.base import BaseCommand
from accounts.models import User
import random


class Command(BaseCommand):
    help = 'Populate fake CPFs for existing users'

    def handle(self, *args, **options):
        users_without_cpf = User.objects.filter(cpf__isnull=True)
        
        for user in users_without_cpf:
            cpf = self.generate_valid_cpf()
            user.cpf = cpf
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated user {user.email} with CPF'))
    
    def generate_valid_cpf(self):
        cpf = [random.randint(0, 9) for _ in range(9)]
        
        soma = sum(cpf[i] * (10 - i) for i in range(9))
        resto = soma % 11
        cpf.append(0 if resto < 2 else 11 - resto)
        
        soma = sum(cpf[i] * (11 - i) for i in range(10))
        resto = soma % 11
        cpf.append(0 if resto < 2 else 11 - resto)
        
        return ''.join(map(str, cpf))
