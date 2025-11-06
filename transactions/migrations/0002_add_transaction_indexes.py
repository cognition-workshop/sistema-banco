from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-timestamp']},
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['account', '-timestamp'], name='transactions_account_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['timestamp'], name='transactions_ts_idx'),
        ),
    ]
