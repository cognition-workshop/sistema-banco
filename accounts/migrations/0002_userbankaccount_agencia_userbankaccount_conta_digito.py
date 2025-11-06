
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbankaccount',
            name='agencia',
            field=models.CharField(blank=True, help_text='Número da agência (4 dígitos)', max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='userbankaccount',
            name='conta_digito',
            field=models.CharField(blank=True, help_text='Dígito verificador da conta', max_length=2, null=True),
        ),
    ]
