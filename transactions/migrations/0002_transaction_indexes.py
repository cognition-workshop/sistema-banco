from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['timestamp'], name='transactions_ti_timest_e63f3e_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['account', 'timestamp'], name='transactions_ti_account_e0f5f9_idx'),
        ),
    ]
