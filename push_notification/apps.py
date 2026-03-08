from django.apps import AppConfig


class PushNotificationConfig(AppConfig):
    name = 'push_notification'

    def ready(self):
        from django.contrib import admin
        from django_celery_beat.models import (
            ClockedSchedule,
            CrontabSchedule,
            IntervalSchedule,
            PeriodicTask,
            SolarSchedule,
        )
        for model in (ClockedSchedule, CrontabSchedule, IntervalSchedule, PeriodicTask, SolarSchedule):
            try:
                admin.site.unregister(model)
            except admin.sites.NotRegistered:
                pass
