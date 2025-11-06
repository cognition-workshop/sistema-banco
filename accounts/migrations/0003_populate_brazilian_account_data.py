from django.db import migrations


def populate_account_fields(apps, schema_editor):
    """Populate agencia and conta_digito for existing accounts"""
    UserBankAccount = apps.get_model('accounts', 'UserBankAccount')
    
    def calcular_digito_verificador(agencia, conta):
        numero_completo = str(agencia) + str(conta)
        soma = 0
        multiplicador = 2
        
        for digito in reversed(numero_completo):
            soma += int(digito) * multiplicador
            multiplicador = multiplicador + 1 if multiplicador < 9 else 2
        
        resto = soma % 11
        digito = 11 - resto
        
        if digito >= 10:
            return 'X'
        return str(digito)
    
    for account in UserBankAccount.objects.filter(agencia__isnull=True):
        account.agencia = '0001'
        account.conta_digito = calcular_digito_verificador('0001', account.account_no)
        account.save()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_userbankaccount_agencia_userbankaccount_conta_digito'),
    ]
    
    operations = [
        migrations.RunPython(populate_account_fields, reverse_code=migrations.RunPython.noop),
    ]
