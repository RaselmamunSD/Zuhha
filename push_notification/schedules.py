"""
Celery beat schedule for periodic push notifications.
"""
from celery import Celery
from celery.schedules import crontab

# Create the Celery app instance
app = Celery('salahtime')

# Configure beat schedule
app.conf.beat_schedule = {
    # Run every minute and dispatch notifications due at that minute
    'dispatch-due-prayer-notifications': {
        'task': 'push_notification.tasks.dispatch_due_prayer_notifications',
        'schedule': crontab(minute='*'),
    },
    
    # Run every minute and dispatch subscription-based notifications
    'dispatch-subscription-notifications': {
        'task': 'push_notification.tasks.dispatch_subscription_notifications',
        'schedule': crontab(minute='*'),
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

