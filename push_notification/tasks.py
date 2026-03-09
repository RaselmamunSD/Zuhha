"""
Celery tasks for push notifications.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def _send_whatsapp_via_twilio(to_phone, message):
    """
    Send a WhatsApp message using Twilio API.
    Returns (sid, error) tuple. error is None on success.
    """
    from django.conf import settings
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

    if not account_sid or not auth_token or account_sid == 'your_account_sid_here':
        logger.warning(f"[WhatsApp] Twilio not configured — logging only: {to_phone}: {message}")
        return None, 'twilio_not_configured'

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        # Ensure to_phone has whatsapp: prefix
        to_wa = to_phone if to_phone.startswith('whatsapp:') else f'whatsapp:{to_phone}'
        msg = client.messages.create(body=message, from_=from_number, to=to_wa)
        logger.info(f"[WhatsApp] Sent to {to_phone} — SID: {msg.sid}")
        return msg.sid, None
    except Exception as e:
        logger.error(f"[WhatsApp] Twilio error for {to_phone}: {e}")
        return None, str(e)


def _enqueue_task(task, *args, **kwargs):
    """
    Enqueue a Celery task; fall back to local execution if broker is unavailable.
    """
    try:
        task.delay(*args, **kwargs)
        return 'queued'
    except Exception as exc:
        logger.warning(
            "Celery broker unavailable for task %s. Running inline. Error: %s",
            getattr(task, 'name', str(task)),
            exc,
        )
        task.apply(args=args, kwargs=kwargs)
        return 'inline'


@shared_task(bind=True, max_retries=3)
def send_whatsapp_notification(self, notification_id, message, prayer_name=''):
    """
    Send WhatsApp notification to a WhatsAppNotification subscriber via Twilio.
    """
    from push_notification.models import WhatsAppNotification, WhatsAppNotificationLog

    try:
        notification = WhatsAppNotification.objects.get(id=notification_id)

        log = WhatsAppNotificationLog.objects.create(
            whatsapp=notification,
            message=message,
            prayer_name=prayer_name,
            status='pending'
        )

        sid, error = _send_whatsapp_via_twilio(notification.full_phone, message)

        if error == 'twilio_not_configured':
            log.status = 'sent'   # dev/no-config mode — treat as sent
        elif error:
            log.status = 'failed'
        else:
            log.status = 'sent'
            log.twilio_sid = sid

        log.save()
        return {'status': 'success' if not error else 'error', 'log_id': log.id}

    except WhatsAppNotification.DoesNotExist:
        logger.error(f"WhatsAppNotification {notification_id} not found")
        return {'status': 'error', 'message': 'Not found'}
    except Exception as exc:
        logger.error(f"send_whatsapp_notification error: {exc}")
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
            _enqueue_task(send_whatsapp_notification, subscriber.id, message, prayer_name)
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
        _enqueue_task(send_whatsapp_notification, subscriber.id, message, prayer_name)
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
            # Resolve today's prayer times: prefer MosqueMonthlyPrayerTime, fallback to static fields
            from find_mosque.models import MosqueMonthlyPrayerTime
            monthly = MosqueMonthlyPrayerTime.objects.filter(
                mosque=mosque,
                year=now_local.year,
                month=now_local.month,
                day=now_local.day,
            ).first()

            # Map prayer name → adhan time using monthly timetable or static mosque fields
            STATIC_FIELD_MAP = {
                'fajr': 'fajr_beginning',
                'dhuhr': 'dhuhr_beginning',
                'asr': 'asr_beginning',
                'maghrib': 'maghrib_sunset',  # correct field name on Mosque model
                'isha': 'isha_beginning',
            }
            MONTHLY_FIELD_MAP = {
                'fajr': 'fajr_adhan',
                'dhuhr': 'dhuhr_adhan',
                'asr': 'asr_adhan',
                'maghrib': 'maghrib_adhan',
                'isha': 'isha_adhan',
            }

            for prayer_name in requested_prayers:
                if prayer_name not in prayer_names:
                    continue

                # Try monthly timetable adhan time first
                if monthly:
                    prayer_time_value = getattr(monthly, MONTHLY_FIELD_MAP.get(prayer_name, ''), None)
                else:
                    prayer_time_value = None

                # Fallback to static mosque fields
                if not prayer_time_value:
                    prayer_time_value = getattr(mosque, STATIC_FIELD_MAP.get(prayer_name, ''), None)

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
                    _enqueue_task(
                        queue_whatsapp_for_subscription,
                        subscription.id,
                        mosque.id,
                        prayer_name,
                        message,
                    )
                elif subscription.notification_method == 'email' and subscription.email:
                    _enqueue_task(
                        queue_email_for_subscription,
                        subscription.id,
                        mosque.id,
                        prayer_name,
                        message,
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
    """Send WhatsApp message for a Subscription via Twilio."""
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

        # Format phone: ensure leading + for country code (e.g. +8801XXXXXXXXX)
        phone = subscription.phone.strip()
        if not phone.startswith('+'):
            phone = '+' + phone

        sid, error = _send_whatsapp_via_twilio(phone, message)

        if error == 'twilio_not_configured':
            log.status = 'sent'
            logger.info(f"[WhatsApp-Sub] {phone} → {message}")
        elif error:
            log.status = 'failed'
            logger.error(f"[WhatsApp-Sub] Failed to {phone}: {error}")
        else:
            log.status = 'sent'

        log.save()
        return {'status': 'success' if not error else 'error', 'log_id': log.id}

    except (Subscription.DoesNotExist, Mosque.DoesNotExist) as e:
        logger.error(f"queue_whatsapp_for_subscription: {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as exc:
        logger.error(f"queue_whatsapp_for_subscription error: {exc}")
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

        prayer_display = {
            'fajr': 'Fajr (Dawn)', 'dhuhr': 'Dhuhr (Midday)', 'asr': 'Asr (Afternoon)',
            'maghrib': 'Maghrib (Sunset)', 'isha': 'Isha (Night)', 'jumuah': "Jumu'ah (Friday)",
        }.get(prayer_name.lower(), prayer_name.title())

        # Extract time from message for subject
        prayer_time_str = message.split('Time   : ')[-1].split('\n')[0].strip() if 'Time   :' in message else ''
        subject = f"🕌 Prayer Reminder: {prayer_display} at {mosque.name} — {prayer_time_str}"

        log = SubscriptionLog.objects.create(
            subscription=subscription,
            subject=subject,
            message=message,
            prayer_name=prayer_name,
            status='pending'
        )

        email_body = _build_email_body(
            prayer_name,
            prayer_time_str,
            subscription.notification_minutes_before or 10,
            mosque.name,
        )

        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.email],
                fail_silently=False,
            )
            log.status = 'sent'
            logger.info(f"[Email] Sent to {subscription.email} — {subject}")
        except Exception as email_exc:
            logger.error(f"[Email] Failed to {subscription.email}: {email_exc}")
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
    Prepare English prayer notification message for WhatsApp and Email.
    """
    prayer_display = {
        'fajr': 'Fajr (Dawn)',
        'dhuhr': 'Dhuhr (Midday)',
        'asr': 'Asr (Afternoon)',
        'maghrib': 'Maghrib (Sunset)',
        'isha': 'Isha (Night)',
        'jumuah': 'Jumu\'ah (Friday)',
    }.get(prayer_name.lower(), prayer_name.title())

    # Convert 24h to 12h AM/PM
    try:
        h, m = map(int, prayer_time.split(':'))
        period = 'AM' if h < 12 else 'PM'
        h12 = h % 12 or 12
        time_display = f'{h12}:{m:02d} {period}'
    except Exception:
        time_display = prayer_time

    mosque_line = f'\nMosque : {mosque_name}' if mosque_name else ''
    # WhatsApp supports *bold* via asterisks
    return (
        f'🕌 *Prayer Reminder — Salahtime*\n'
        f'\n'
        f'Prayer : *{prayer_display}*{mosque_line}\n'
        f'Time   : *{time_display}*\n'
        f'Starting in *{minutes_before} minutes*\n'
        f'\n'
        f'May Allah accept your prayer. 🤲'
    )


def _build_email_body(prayer_name, prayer_time, minutes_before, mosque_name):
    """Build a clean plain-text email body."""
    prayer_display = {
        'fajr': 'Fajr (Dawn)',
        'dhuhr': 'Dhuhr (Midday)',
        'asr': 'Asr (Afternoon)',
        'maghrib': 'Maghrib (Sunset)',
        'isha': 'Isha (Night)',
        'jumuah': 'Jumu\'ah (Friday)',
    }.get(prayer_name.lower(), prayer_name.title())

    try:
        h, m = map(int, prayer_time.split(':'))
        period = 'AM' if h < 12 else 'PM'
        h12 = h % 12 or 12
        time_display = f'{h12}:{m:02d} {period}'
    except Exception:
        time_display = prayer_time

    return f"""Assalamu Alaikum,

This is your prayer reminder from Salahtime.

{'=' * 40}
  Prayer Reminder
{'=' * 40}
  Prayer  : {prayer_display}
  Mosque  : {mosque_name}
  Time    : {time_display}
  Starts in {minutes_before} minutes
{'=' * 40}

Please prepare for prayer.
May Allah accept from us. Ameen.

---
Salahtime — Prayer Time Notifications
To unsubscribe, reply with STOP.
"""


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
        
        _enqueue_task(send_whatsapp_notification, subscriber.id, message)
        messages_sent += 1
    
    return {
        'status': 'success',
        'city_id': city_id,
        'messages_queued': messages_sent
    }


@shared_task
def send_mosque_registration_email(mosque_id, image_url, admin_panel_url):
    """
    Send admin notification email after a new mosque registration.
    Runs in the background so the HTTP response is not blocked by SMTP.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from django.db.models import Q
    from django.contrib.auth import get_user_model
    from find_mosque.models import Mosque

    try:
        mosque = Mosque.objects.select_related('city').get(pk=mosque_id)
    except Mosque.DoesNotExist:
        logger.error(f"[MosqueRegistration] Mosque {mosque_id} not found")
        return

    subject = f"New Mosque Registration: {mosque.name}"
    message = f"""Assalamu Alaikum,

A new mosque has been registered and is awaiting your approval.

Mosque Details:
---------------
Name: {mosque.name}
Contact Person: {mosque.contact_person or 'N/A'}
Phone: {mosque.phone or 'N/A'}
Email: {mosque.email or 'N/A'}
Address: {mosque.address or 'N/A'}
City: {mosque.city.name if mosque.city else 'N/A'}

Additional Information:
{mosque.additional_info or 'None provided'}

Prayer Timetable Image:
{image_url or 'Not uploaded'}

Please review and approve this mosque registration.

Admin Panel: {admin_panel_url}

Jazakallahu Khairan"""

    User = get_user_model()
    admin_emails = list(
        User.objects.filter(
            Q(is_superuser=True) | Q(is_staff=True),
            email__isnull=False,
        )
        .exclude(email='')
        .values_list('email', flat=True)
        .distinct()
    )

    if admin_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )
        logger.info(f"[MosqueRegistration] Email sent to {admin_emails} for mosque '{mosque.name}'")
    else:
        logger.warning("[MosqueRegistration] No admin emails found — skipping notification")


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
        
        _enqueue_task(send_whatsapp_notification, subscriber.id, message)
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

