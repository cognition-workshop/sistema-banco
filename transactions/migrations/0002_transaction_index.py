from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['account', 'timestamp'],
                name='trans_acc_time_idx'
            ),
        ),
    ]
