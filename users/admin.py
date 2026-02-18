from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, UserLocation


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'current_city', 'calculation_method', 'juristic_method', 'is_verified', 'email_verified', 'language', 'theme', 'fajr_notification', 'dhuhr_notification', 'asr_notification', 'maghrib_notification', 'isha_notification', 'notification_minutes_before']
    list_filter = ['calculation_method', 'juristic_method', 'high_latitude_adjustment', 'is_verified', 'email_verified', 'language', 'theme', 'fajr_notification', 'dhuhr_notification', 'asr_notification', 'maghrib_notification', 'isha_notification']
    search_fields = ['user__username', 'user__email', 'phone', 'current_city__name']
    list_editable = ['fajr_notification', 'dhuhr_notification', 'asr_notification', 'maghrib_notification', 'isha_notification', 'notification_minutes_before']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User', {
            'fields': ('user', 'phone', 'date_of_birth', 'profile_image')
        }),
        ('Location', {
            'fields': ('current_city',)
        }),
        ('Prayer Calculation', {
            'fields': ('calculation_method', 'juristic_method', 'high_latitude_adjustment')
        }),
        ('Notification Preferences', {
            'fields': ('fajr_notification', 'dhuhr_notification', 'asr_notification', 'maghrib_notification', 'isha_notification', 'notification_minutes_before')
        }),
        ('Account Settings', {
            'fields': ('is_verified', 'email_verified', 'language', 'theme')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'label', 'is_default', 'created_at']
    list_filter = ['is_default', 'city__country']
    search_fields = ['user__username', 'city__name', 'label']
    list_editable = ['is_default', 'label']

