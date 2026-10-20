"""
Celery application for the School Management System.
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_production')

app = Celery('core')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Periodic / beat schedule for school-level background analysis.
app.conf.beat_schedule = {
    'flag-at-risk-learners': {
        'task': 'ai.flag_at_risk_learners',
        'schedule': crontab(hour=2, minute=0),  # runs daily at 02:00 Nairobi time
        'options': {'expires': 60 * 60},
    },
}
