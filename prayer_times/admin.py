from django.contrib import admin
from .models import PrayerTime, MonthlyPrayerTime, PrayerTimeAdjustment


@admin.register(PrayerTime)
class PrayerTimeAdmin(admin.ModelAdmin):
    list_display = ['date', 'fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha', 'created_at']
    list_filter = ['date']
    search_fields = ['date']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MonthlyPrayerTime)
class MonthlyPrayerTimeAdmin(admin.ModelAdmin):
    list_display = ['city', 'year', 'month', 'day', 'fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha', 'created_at']
    list_filter = ['year', 'month', 'city__country', 'city']
    search_fields = ['city__name']
    ordering = ['-year', '-month', '-day']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PrayerTimeAdjustment)
class PrayerTimeAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['prayer_name', 'adjustment_minutes', 'city', 'is_active', 'created_at']
    list_filter = ['prayer_name', 'is_active', 'city__country', 'city']
    search_fields = ['city__name']
    list_editable = ['adjustment_minutes', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

