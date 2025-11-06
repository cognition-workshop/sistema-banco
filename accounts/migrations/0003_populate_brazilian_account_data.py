from django.db import migrations


def populate_brazilian_fields(apps, schema_editor):
    """
    Popula os campos agencia, conta e conta_digito para contas existentes
    """
    UserBankAccount = apps.get_model('accounts', 'UserBankAccount')
    
    def calcular_digito_verificador(agencia, conta):
        input_str = str(agencia) + str(conta)
        
        soma = 0
        multiplicador = 2
        
        for i in range(len(input_str) - 1, -1, -1):
            soma += multiplicador * int(input_str[i])
            multiplicador += 1
            if multiplicador > 9:
                multiplicador = 2
        
        digito = soma % 11
        if digito == 10:
            return 'X'
        
        return str(digito)
    
    for account in UserBankAccount.objects.all():
        if not account.agencia:
            account.agencia = "0001"
            account.conta = str(account.account_no)
            account.conta_digito = calcular_digito_verificador("0001", str(account.account_no))
            account.save()


def reverse_population(apps, schema_editor):
    """
    Remove os dados dos campos brasileiros se a migration for revertida
    """
    UserBankAccount = apps.get_model('accounts', 'UserBankAccount')
    UserBankAccount.objects.all().update(
        agencia=None,
        conta=None,
        conta_digito=None
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_brazilian_account_fields'),
    ]

    operations = [
        migrations.RunPython(populate_brazilian_fields, reverse_population),
    ]
