import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='balance_before_transaction',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Account balance before this transaction', max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(blank=True, help_text='User who performed this transaction (null for system operations like interest)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='performed_transactions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='transaction',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, help_text='IP address from which the transaction was initiated', null=True),
        ),
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['timestamp'], 'permissions': [('cannot_delete_transaction', 'Cannot delete transactions')]},
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['timestamp'], name='transaction_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user'], name='transaction_user_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['account', 'timestamp'], name='transaction_account_timesta_idx'),
        ),
    ]
