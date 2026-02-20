"""
Celery beat schedule for periodic push notifications.
"""
from celery import Celery
from celery.schedules import crontab

# Create the Celery app instance
app = Celery('salahtime')

# Configure beat schedule
app.conf.beat_schedule = {
    # Daily Fajr prayer notification (before Fajr)
    'send-fajr-notification': {
        'task': 'push_notification.tasks.send_prayer_notification',
        'schedule': crontab(hour=4, minute=30),  # 4:30 AM UTC
        'args': ('fajr', 1),  # city_id=1 (default)
    },
    
    # Daily Dhuhr prayer notification
    'send-dhuhr-notification': {
        'task': 'push_notification.tasks.send_prayer_notification',
        'schedule': crontab(hour=11, minute=30),  # 11:30 AM UTC
        'args': ('dhuhr', 1),
    },
    
    # Daily Asr prayer notification
    'send-asr-notification': {
        'task': 'push_notification.tasks.send_prayer_notification',
        'schedule': crontab(hour=14, minute=30),  # 2:30 PM UTC
        'args': ('asr', 1),
    },
    
    # Daily Maghrib prayer notification
    'send-maghrib-notification': {
        'task': 'push_notification.tasks.send_prayer_notification',
        'schedule': crontab(hour=17, minute=0),  # 5:00 PM UTC
        'args': ('maghrib', 1),
    },
    
    # Daily Isha prayer notification
    'send-isha-notification': {
        'task': 'push_notification.tasks.send_prayer_notification',
        'schedule': crontab(hour=19, minute=30),  # 7:30 PM UTC
        'args': ('isha', 1),
    },
    
    # Daily summary notification (evening)
    'send-daily-summary': {
        'task': 'push_notification.tasks.send_daily_summary',
        'schedule': crontab(hour=18, minute=0),  # 6:00 PM UTC
        'args': (1,),  # city_id=1
    },
    
    # Weekly summary (Friday evening)
    'send-weekly-summary': {
        'task': 'push_notification.tasks.send_weekly_summary',
        'schedule': crontab(hour=18, minute=0, day_of_week=5),  # Friday 6 PM UTC
        'args': (1,),
    },
    
    # Cleanup old logs (daily at 2 AM)
    'cleanup-old-logs': {
        'task': 'push_notification.tasks.cleanup_old_notification_logs',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC
    },
}

# Timezone
app.conf.timezone = 'UTC'

