"""
Management command to manually dispatch prayer notifications.
Use for testing without Celery.

Usage:
    python manage.py dispatch_notifications            # dispatch now
    python manage.py dispatch_notifications --status  # show subscription status
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Manually dispatch prayer notifications (for testing)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show notification system status only (no dispatch)',
        )

    def handle(self, *args, **options):
        self.stdout.write('\n=== Salahtime Notification System ===\n')

        # --- Status checks ---
        self._check_email_config()
        self._check_whatsapp_config()
        self._check_subscriptions()
        self._check_celery()

        if options['status']:
            return

        # --- Dispatch ---
        self.stdout.write('\n--- Dispatching notifications now ---')
        from push_notification.tasks import dispatch_subscription_notifications
        result = dispatch_subscription_notifications.apply()
        self.stdout.write(self.style.SUCCESS(f'Subscription result: {result.result}'))

        from push_notification.tasks import dispatch_due_prayer_notifications
        result2 = dispatch_due_prayer_notifications.apply()
        self.stdout.write(self.style.SUCCESS(f'WhatsApp result: {result2.result}'))

    def _check_whatsapp_config(self):
        from django.conf import settings
        self.stdout.write('\n[WhatsApp / Twilio Config]')
        sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        from_num = getattr(settings, 'TWILIO_WHATSAPP_FROM', '')
        configured = sid and token and sid != 'your_account_sid_here'
        self.stdout.write(f'  Account SID : {"✓ SET" if sid and sid != "your_account_sid_here" else "✗ NOT SET"}')
        self.stdout.write(f'  Auth Token  : {"✓ SET" if token else "✗ NOT SET"}')
        self.stdout.write(f'  From Number : {from_num}')
        if configured:
            self.stdout.write(self.style.SUCCESS('  ✓ Twilio WhatsApp configured'))
        else:
            self.stdout.write(self.style.WARNING(
                '  ⚠ Twilio not configured — WhatsApp messages will only be logged\n'
                '  Fix: Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN in .env\n'
                '  Get credentials: https://console.twilio.com'
            ))

    def _check_email_config(self):
        from django.conf import settings
        self.stdout.write('\n[Email Config]')
        backend = settings.EMAIL_BACKEND
        host = settings.EMAIL_HOST
        user = settings.EMAIL_HOST_USER
        pwd = bool(settings.EMAIL_HOST_PASSWORD)
        self.stdout.write(f'  Backend : {backend}')
        self.stdout.write(f'  Host    : {host}')
        self.stdout.write(f'  User    : {user}')
        self.stdout.write(f'  Password: {"✓ SET" if pwd else "✗ NOT SET"}')

        is_console = 'console' in backend
        if is_console:
            self.stdout.write(self.style.WARNING(
                '  ⚠ Console backend — emails print to terminal only!\n'
                '  Fix: Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in .env'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ SMTP backend configured'))
            if not pwd:
                self.stdout.write(self.style.ERROR(
                    '  ✗ EMAIL_HOST_PASSWORD not set! Emails will fail.'
                ))

    def _check_subscriptions(self):
        from subscribe.models import Subscription
        self.stdout.write('\n[Subscriptions]')
        total = Subscription.objects.count()
        active = Subscription.objects.filter(is_active=True).count()
        with_mosque = Subscription.objects.filter(
            is_active=True, selected_mosques__isnull=False
        ).distinct().count()
        with_prayers = Subscription.objects.filter(
            is_active=True
        ).exclude(selected_prayers=[]).count()

        self.stdout.write(f'  Total active   : {active}/{total}')
        self.stdout.write(f'  With mosque    : {with_mosque}')
        self.stdout.write(f'  With prayers   : {with_prayers}')

        if active == 0:
            self.stdout.write(self.style.WARNING('  ⚠ No active subscriptions found'))
        if with_mosque == 0:
            self.stdout.write(self.style.WARNING(
                '  ⚠ No subscriptions have a mosque selected — notifications will not fire!'
            ))
        if with_prayers == 0:
            self.stdout.write(self.style.WARNING(
                '  ⚠ No subscriptions have prayers selected — notifications will not fire!'
            ))

        # Show prayer times check
        now = timezone.localtime()
        self.stdout.write(f'  Current time   : {now.strftime("%H:%M")} (local)')

        # Check which prayers are due within 30 min
        from find_mosque.models import Mosque
        from datetime import timedelta
        prayer_fields = ['fajr_beginning', 'dhuhr_beginning', 'asr_beginning',
                         'maghrib_sunset', 'isha_beginning']
        prayer_names = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
        due_soon = []
        for mosque in Mosque.objects.filter(is_active=True)[:10]:
            for field, name in zip(prayer_fields, prayer_names):
                pt = getattr(mosque, field, None)
                if not pt:
                    continue
                prayer_dt = timezone.make_aware(
                    timezone.datetime.combine(now.date(), pt),
                    timezone.get_current_timezone()
                )
                diff = (prayer_dt - now).total_seconds() / 60
                if 0 < diff <= 30:
                    due_soon.append(f'{mosque.name} → {name} at {pt.strftime("%H:%M")} ({int(diff)} min)')

        if due_soon:
            self.stdout.write(self.style.SUCCESS(f'\n  Prayers due within 30 min:'))
            for d in due_soon:
                self.stdout.write(f'    ✓ {d}')
        else:
            self.stdout.write('  No prayers due within 30 min right now')

    def _check_celery(self):
        from django.conf import settings
        self.stdout.write('\n[Celery]')
        broker = settings.CELERY_BROKER_URL
        self.stdout.write(f'  Broker : {broker}')
        if not broker:
            self.stdout.write(self.style.ERROR(
                '  ✗ CELERY_BROKER_URL not set!\n'
                '  Fix: Add CELERY_BROKER_URL=redis://localhost:6379/0 to .env'
            ))
            return

        try:
            import redis
            r = redis.from_url(broker)
            r.ping()
            self.stdout.write(self.style.SUCCESS('  ✓ Redis reachable'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Redis not reachable: {e}'))
            return

        # Check worker
        try:
            from config.celery import app as celery_app
            inspect = celery_app.control.inspect(timeout=2)
            active = inspect.active()
            if active:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Celery worker running: {list(active.keys())}'))
            else:
                self.stdout.write(self.style.ERROR(
                    '  ✗ Celery worker NOT running!\n'
                    '  Start it: celery -A config worker -l info'
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Cannot connect to Celery worker: {e}'))

        self.stdout.write(self.style.WARNING(
            '\n  To start Celery services:\n'
            '  Worker: celery -A config worker -l info\n'
            '  Beat  : celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler'
        ))
