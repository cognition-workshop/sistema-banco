import accounts.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cpf',
            field=models.CharField(
                help_text='CPF com 11 dígitos (apenas números)',
                max_length=11,
                unique=True,
                validators=[accounts.validators.validate_cpf]
            ),
        ),
    ]
