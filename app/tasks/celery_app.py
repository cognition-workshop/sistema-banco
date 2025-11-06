from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

app = Celery('banking_system')

app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.timezone = 'UTC'

app.conf.beat_schedule = {
    'calculate_interest': {
        'task': 'app.tasks.interest.calculate_interest',
        'schedule': crontab(0, 0, day_of_month='1'),
    }
}

app.autodiscover_tasks(['app.tasks'])
