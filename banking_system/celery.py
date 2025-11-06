from __future__ import absolute_import, unicode_literals

import os
import logging

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure, task_success

logger = logging.getLogger('celery')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking_system.settings')

app = Celery('banking_system')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'calculate_interest': {
        'task': 'calculate_interest',
        'schedule': crontab(0, 0, day_of_month='1'),
    }
}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, args=None,
    kwargs=None, traceback=None, einfo=None, **kw
):
    """Log task failures"""
    logger.error(
        f'Task {sender.name} (ID: {task_id}) failed with exception: {exception}',
        exc_info=einfo
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log task successes"""
    logger.info(f'Task {sender.name} completed successfully')
