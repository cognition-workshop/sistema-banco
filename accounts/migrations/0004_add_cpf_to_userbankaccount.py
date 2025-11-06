from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_populate_brazilian_account_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbankaccount',
            name='cpf',
            field=models.CharField(blank=True, help_text='CPF no formato XXX.XXX.XXX-XX', max_length=14, null=True),
        ),
    ]
