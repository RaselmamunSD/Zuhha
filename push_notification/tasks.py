"""
Celery tasks for push notifications.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_whatsapp_notification(self, notification_id, message, prayer_name=''):
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
            prayer_name=prayer_name,
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


def _is_notification_due(now_local, prayer_time, minutes_before):
    prayer_datetime = timezone.make_aware(
        timezone.datetime.combine(now_local.date(), prayer_time),
        timezone.get_current_timezone()
    )
    due_datetime = prayer_datetime - timedelta(minutes=minutes_before)
    return due_datetime.replace(second=0, microsecond=0) == now_local.replace(second=0, microsecond=0)


def _already_sent_for_window(subscriber_id, prayer_name, window_start, window_end):
    from push_notification.models import WhatsAppNotificationLog

    return WhatsAppNotificationLog.objects.filter(
        whatsapp_id=subscriber_id,
        prayer_name=prayer_name,
        sent_at__gte=window_start,
        sent_at__lt=window_end,
        status__in=['pending', 'sent', 'delivered', 'read']
    ).exists()


@shared_task(bind=True)
def dispatch_due_prayer_notifications(self):
    """
    Dispatch prayer notifications that are due at current minute.

    Runs every minute and respects each subscriber's
    notification_minutes_before preference (10/20/30).
    """
    from push_notification.models import WhatsAppNotification
    from prayer_times.models import MonthlyPrayerTime

    now_local = timezone.localtime()
    prayer_names = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']

    subscribers = WhatsAppNotification.objects.filter(
        is_active=True,
        city__isnull=False,
    ).exclude(notification_types=[])

    if not subscribers.exists():
        return {'status': 'success', 'messages_queued': 0, 'reason': 'no_active_subscribers'}

    city_ids = subscribers.values_list('city_id', flat=True).distinct()
    prayer_time_map = {
        pt.city_id: pt
        for pt in MonthlyPrayerTime.objects.filter(
            city_id__in=city_ids,
            year=now_local.year,
            month=now_local.month,
            day=now_local.day,
        )
    }

    messages_queued = 0
    window_start = now_local.replace(second=0, microsecond=0)
    window_end = window_start + timedelta(minutes=1)

    for subscriber in subscribers:
        if not subscriber.city_id:
            continue

        prayer_times = prayer_time_map.get(subscriber.city_id)
        if not prayer_times:
            continue

        requested_prayers = [p for p in subscriber.notification_types if p in prayer_names]
        if not requested_prayers:
            continue

        minutes_before = subscriber.notification_minutes_before or 10
        if minutes_before not in [10, 20, 30]:
            minutes_before = 10

        for prayer_name in requested_prayers:
            prayer_time_value = getattr(prayer_times, prayer_name, None)
            if not prayer_time_value:
                continue

            if not _is_notification_due(now_local, prayer_time_value, minutes_before):
                continue

            if _already_sent_for_window(subscriber.id, prayer_name, window_start, window_end):
                continue

            message = prepare_prayer_message(
                subscriber.language,
                prayer_name,
                prayer_time_value.strftime('%H:%M'),
                minutes_before,
            )
            send_whatsapp_notification.delay(subscriber.id, message, prayer_name)
            messages_queued += 1

    return {
        'status': 'success',
        'checked_at': now_local.isoformat(),
        'messages_queued': messages_queued,
    }


@shared_task(bind=True)
def send_prayer_notification(self, prayer_name, city_id, minutes_before=None):
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
    )

    if minutes_before in [10, 20, 30]:
        subscribers = subscribers.filter(notification_minutes_before=minutes_before)
    
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
        send_whatsapp_notification.delay(subscriber.id, message, prayer_name)
        messages_sent += 1
    
    return {
        'status': 'success',
        'prayer': prayer_name,
        'city_id': city_id,
        'messages_queued': messages_sent
    }


@shared_task(bind=True)
def dispatch_subscription_notifications(self):
    """
    Dispatch notifications for all active subscriptions based on their
    selected mosques and prayer preferences.

    Runs every minute and respects each subscription's
    notification_minutes_before preference (10/20/30).

    Sends via WhatsApp or Email based on notification_method.
    """
    from subscribe.models import Subscription

    now_local = timezone.localtime()
    prayer_names = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']

    subscriptions = Subscription.objects.filter(
        is_active=True,
    ).prefetch_related('selected_mosques')

    if not subscriptions.exists():
        return {
            'status': 'success',
            'notifications_queued': 0,
            'reason': 'no_active_subscriptions'
        }

    notifications_queued = 0
    window_start = now_local.replace(second=0, microsecond=0)
    window_end = window_start + timedelta(minutes=1)

    for subscription in subscriptions:
        mosques = subscription.selected_mosques.all()
        if not mosques.exists():
            continue

        requested_prayers = subscription.selected_prayers or []
        if not requested_prayers:
            continue

        minutes_before = subscription.notification_minutes_before or 10
        if minutes_before not in [10, 20, 30]:
            minutes_before = 10

        for mosque in mosques:
            for prayer_name in requested_prayers:
                if prayer_name not in prayer_names:
                    continue

                prayer_time_value = getattr(mosque, f'{prayer_name}_beginning', None)
                if not prayer_time_value:
                    continue

                if not _is_notification_due(now_local, prayer_time_value, minutes_before):
                    continue

                if _already_sent_for_subscription(
                    subscription.id, mosque.id, prayer_name, window_start, window_end
                ):
                    continue

                message = prepare_subscription_prayer_message(
                    'en',
                    prayer_name,
                    prayer_time_value.strftime('%H:%M'),
                    minutes_before,
                    mosque.name
                )

                if subscription.notification_method == 'whatsapp' and subscription.phone:
                    queue_whatsapp_for_subscription.delay(
                        subscription.id, mosque.id, prayer_name, message
                    )
                elif subscription.notification_method == 'email' and subscription.email:
                    queue_email_for_subscription.delay(
                        subscription.id, mosque.id, prayer_name, message
                    )

                notifications_queued += 1

    return {
        'status': 'success',
        'checked_at': now_local.isoformat(),
        'notifications_queued': notifications_queued,
    }


def _already_sent_for_subscription(subscription_id, mosque_id, prayer_name, window_start, window_end):
    """Check if notification already sent in the given time window."""
    from subscribe.models import SubscriptionLog

    return SubscriptionLog.objects.filter(
        subscription_id=subscription_id,
        prayer_name=prayer_name,
        sent_at__gte=window_start,
        sent_at__lt=window_end,
        status__in=['sent', 'pending']
    ).exists()


@shared_task(bind=True, max_retries=3)
def queue_whatsapp_for_subscription(self, subscription_id, mosque_id, prayer_name, message):
    """Queue WhatsApp message for a subscription."""
    from subscribe.models import Subscription, SubscriptionLog
    from find_mosque.models import Mosque

    try:
        subscription = Subscription.objects.get(id=subscription_id)
        mosque = Mosque.objects.get(id=mosque_id)

        log = SubscriptionLog.objects.create(
            subscription=subscription,
            subject=f"{mosque.name} - {prayer_name.title()} Prayer",
            message=message,
            prayer_name=prayer_name,
            status='pending'
        )

        logger.info(
            f"Queuing WhatsApp to {subscription.phone} for {mosque.name} - {prayer_name}: {message}"
        )

        log.status = 'sent'
        log.save()

        return {'status': 'success', 'log_id': log.id}

    except (Subscription.DoesNotExist, Mosque.DoesNotExist) as e:
        logger.error(f"Subscription or Mosque not found: {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as exc:
        logger.error(f"Error queueing WhatsApp: {exc}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def queue_email_for_subscription(self, subscription_id, mosque_id, prayer_name, message):
    """Queue email message for a subscription."""
    from subscribe.models import Subscription, SubscriptionLog
    from find_mosque.models import Mosque
    from django.core.mail import send_mail
    from django.conf import settings

    try:
        subscription = Subscription.objects.get(id=subscription_id)
        mosque = Mosque.objects.get(id=mosque_id)

        subject = f"🕌 {mosque.name} - {prayer_name.title()} Prayer Alert"

        log = SubscriptionLog.objects.create(
            subscription=subscription,
            subject=subject,
            message=message,
            prayer_name=prayer_name,
            status='pending'
        )

        email_body = f"""Assalamu Alaikum,

Prayer Alert from Salahtime:

Mosque: {mosque.name}
Prayer: {prayer_name.upper()}
Time: {message.split('at ')[-1]}

{message}

May Allah accept from us.

---
Salahtime Team
(salahtime.local)
"""

        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.email],
                fail_silently=False,
            )
            log.status = 'sent'
        except Exception as email_exc:
            logger.error(f"Failed to send email to {subscription.email}: {email_exc}")
            log.status = 'failed'
        finally:
            log.save()

        return {'status': 'success', 'log_id': log.id}

    except (Subscription.DoesNotExist, Mosque.DoesNotExist) as e:
        logger.error(f"Subscription or Mosque not found: {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as exc:
        logger.error(f"Error queueing email: {exc}")
        self.retry(exc=exc, countdown=60)


def prepare_subscription_prayer_message(language, prayer_name, prayer_time, minutes_before, mosque_name=None):
    """
    Prepare localized prayer notification message for subscription.
    """
    mosque_suffix = f" at {mosque_name}" if mosque_name else ""
    return f"🕋 {prayer_name.title()} prayer{mosque_suffix} in {minutes_before} minutes at {prayer_time}"


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

