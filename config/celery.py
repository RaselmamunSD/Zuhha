"""
Celery configuration for Salahtime project.
"""
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('salahtime')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f'Request: {self.request!r}')


# Import beat schedule from push_notification app
try:
    from push_notification.schedules import app as schedule_app
    if hasattr(schedule_app, 'conf'):
        app.conf.beat_schedule = schedule_app.conf.beat_schedule
except ImportError:
    pass
