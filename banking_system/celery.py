import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')

app = Celery('banking_system')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'calculate-interest': {
        'task': 'calculate_interest',
        'schedule': crontab(hour=0, minute=0, day_of_month='1'),
    },
}
