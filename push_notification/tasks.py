"""
Celery tasks for push notifications.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_whatsapp_notification(self, notification_id, message):
    """
    Send WhatsApp notification to a subscriber.
    
    Args:
        notification_id: ID of the WhatsAppNotification model
        message: Message content to send
    """
    from push_notification.models import WhatsAppNotification, WhatsAppNotificationLog
    
    try:
        notification = WhatsAppNotification.objects.get(id=notification_id)
        
        # Create log entry
        log = WhatsAppNotificationLog.objects.create(
            whatsapp=notification,
            message=message,
            status='pending'
        )
        
        # TODO: Integrate with Twilio or WhatsApp Business API
        # For now, we'll simulate sending
        logger.info(f"Sending WhatsApp to {notification.full_phone}: {message}")
        
        # Simulate successful send
        log.status = 'sent'
        log.save()
        
        return {'status': 'success', 'log_id': log.id}
        
    except WhatsAppNotification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {'status': 'error', 'message': 'Notification not found'}
    except Exception as exc:
        logger.error(f"Error sending notification: {exc}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def send_prayer_notification(self, prayer_name, city_id):
    """
    Send prayer time notifications to all subscribers for a specific city and prayer.
    
    Args:
        prayer_name: Name of the prayer (fajr, dhuhr, asr, maghrib, isha)
        city_id: ID of the city
    """
    from push_notification.models import WhatsAppNotification
    from prayer_times.models import MonthlyPrayerTime
    from datetime import datetime
    
    # Get prayer time for the city
    today = datetime.now()
    try:
        prayer_time = MonthlyPrayerTime.objects.get(
            city_id=city_id,
            year=today.year,
            month=today.month,
            day=today.day
        )
    except MonthlyPrayerTime.DoesNotExist:
        logger.warning(f"Prayer times not found for city {city_id} on {today.date()}")
        return {'status': 'error', 'message': 'Prayer times not found'}
    
    # Get prayer time
    prayer_time_value = getattr(prayer_time, prayer_name, None)
    if not prayer_time_value:
        return {'status': 'error', 'message': 'Invalid prayer name'}
    
    # Get all active subscribers for this city who want this prayer type
    subscribers = WhatsAppNotification.objects.filter(
        city_id=city_id,
        is_active=True,
        is_verified=True
    )
    
    # Filter by notification type
    subscribers = subscribers.filter(
        notification_types__contains=[prayer_name]
    )
    
    # Prepare message templates
    messages_sent = 0
    for subscriber in subscribers:
        message = prepare_prayer_message(
            subscriber.language,
            prayer_name,
            prayer_time_value.strftime('%H:%M'),
            subscriber.notification_minutes_before
        )
        
        # Queue the notification task
        send_whatsapp_notification.delay(subscriber.id, message)
        messages_sent += 1
    
    return {
        'status': 'success',
        'prayer': prayer_name,
        'city_id': city_id,
        'messages_queued': messages_sent
    }


@shared_task(bind=True)
def send_daily_summary(self, city_id):
    """
    Send daily prayer times summary to all subscribers.
    
    Args:
        city_id: ID of the city
    """
    from push_notification.models import WhatsAppNotification
    from prayer_times.models import MonthlyPrayerTime
    from datetime import datetime
    
    today = datetime.now()
    
    try:
        prayer_times = MonthlyPrayerTime.objects.get(
            city_id=city_id,
            year=today.year,
            month=today.month,
            day=today.day
        )
    except MonthlyPrayerTime.DoesNotExist:
        logger.warning(f"Prayer times not found for city {city_id}")
        return {'status': 'error', 'message': 'Prayer times not found'}
    
    # Get all active subscribers for this city
    subscribers = WhatsAppNotification.objects.filter(
        city_id=city_id,
        is_active=True,
        is_verified=True,
        notification_types__contains=['daily']
    )
    
    messages_sent = 0
    for subscriber in subscribers:
        message = prepare_daily_summary_message(
            subscriber.language,
            prayer_times
        )
        
        send_whatsapp_notification.delay(subscriber.id, message)
        messages_sent += 1
    
    return {
        'status': 'success',
        'city_id': city_id,
        'messages_queued': messages_sent
    }


@shared_task
def cleanup_old_notification_logs():
    """
    Cleanup old notification logs (older than 30 days).
    """
    from push_notification.models import WhatsAppNotificationLog
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = WhatsAppNotificationLog.objects.filter(
        sent_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old notification logs")
    return {'status': 'success', 'deleted_count': deleted_count}


@shared_task(bind=True)
def send_weekly_summary(self, city_id):
    """
    Send weekly prayer times summary to all subscribers.
    
    Args:
        city_id: ID of the city
    """
    from push_notification.models import WhatsAppNotification
    from prayer_times.models import MonthlyPrayerTime
    from datetime import datetime, timedelta
    
    # Get the start and end of the week
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get all prayer times for the week
    prayer_times = MonthlyPrayerTime.objects.filter(
        city_id=city_id,
        year=start_of_week.year,
        month__gte=start_of_week.month,
        month__lte=end_of_week.month,
        day__gte=start_of_week.day,
        day__lte=end_of_week.day
    ).order_by('month', 'day')
    
    if not prayer_times.exists():
        logger.warning(f"Prayer times not found for city {city_id} this week")
        return {'status': 'error', 'message': 'Prayer times not found'}
    
    # Get all active subscribers for this city
    subscribers = WhatsAppNotification.objects.filter(
        city_id=city_id,
        is_active=True,
        is_verified=True,
        notification_types__contains=['weekly']
    )
    
    messages_sent = 0
    for subscriber in subscribers:
        message = prepare_weekly_summary_message(
            subscriber.language,
            prayer_times
        )
        
        send_whatsapp_notification.delay(subscriber.id, message)
        messages_sent += 1
    
    return {
        'status': 'success',
        'city_id': city_id,
        'messages_queued': messages_sent
    }


def prepare_prayer_message(language, prayer_name, prayer_time, minutes_before):
    """
    Prepare localized prayer notification message.
    """
    translations = {
        'en': {
            'fajr': 'Fajr',
            'dhuhr': 'Dhuhr',
            'asr': 'Asr',
            'maghrib': 'Maghrib',
            'isha': 'Isha',
            'message': f"{prayer_name.title()} prayer in {minutes_before} minutes at {prayer_time}"
        },
        'bn': {
            'fajr': 'ফজর',
            'dhuhr': 'যোহর',
            'asr': 'আছর',
            'maghrib': 'মাগরিব',
            'isha': 'এশা',
            'message': f"{minutes_before} মিনিট পরে {prayer_name.title()} নামাজ {prayer_time} তে"
        },
        'ar': {
            'fajr': 'الفجر',
            'dhuhr': 'الظهر',
            'asr': 'العصر',
            'maghrib': 'المغرب',
            'isha': 'العشاء',
            'message': f"صلاة {prayer_name.title()} بعد {minutes_before} دقيقة في الساعة {prayer_time}"
        }
    }
    
    trans = translations.get(language, translations['en'])
    prayer_local = trans.get(prayer_name, prayer_name)
    
    return f"🕋 {prayer_local} prayer in {minutes_before} minutes at {prayer_time}"


def prepare_daily_summary_message(language, prayer_times):
    """
    Prepare localized daily summary message.
    """
    message = "📅 Today's Prayer Times:\n\n"
    message += f"🌅 Fajr: {prayer_times.fajr}\n"
    message += f"☀️ Dhuhr: {prayer_times.dhuhr}\n"
    message += f"🌤️ Asr: {prayer_times.asr}\n"
    message += f"🌅 Maghrib: {prayer_times.maghrib}\n"
    message += f"🌙 Isha: {prayer_times.isha}\n\n"
    message += " JazakAllah Khair! 🙏"
    
    return message


def prepare_weekly_summary_message(language, prayer_times_list):
    """
    Prepare localized weekly summary message.
    """
    message = "📅 Weekly Prayer Times Summary:\n\n"
    
    for pt in prayer_times_list[:7]:  # First 7 days
        date_str = f"{pt.year}-{pt.month:02d}-{pt.day:02d}"
        message += f"{date_str}:\n"
        message += f"  Fajr: {pt.fajr} | Dhuhr: {pt.dhuhr}\n"
        message += f"  Asr: {pt.asr} | Maghrib: {pt.maghrib} | Isha: {pt.isha}\n\n"
    
    message += " JazakAllah Khair! 🙏"
    
    return message

