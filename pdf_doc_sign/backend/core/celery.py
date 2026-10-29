import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    'cleanup-old-ai-scans': {
        'task': 'ai_detector.tasks.cleanup_old_scans_task',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM UTC
    },
}
