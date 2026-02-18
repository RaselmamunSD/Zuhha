from django.contrib import admin
from .models import Location, UserPreference


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'location_type', 'latitude', 'longitude', 'created_at']
    list_filter = ['location_type', 'city__country']
    search_fields = ['name', 'address', 'city__name']
    list_editable = ['location_type']


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'calculation_method', 'juristic_method', 'notification_enabled', 'language', 'created_at']
    list_filter = ['calculation_method', 'juristic_method', 'notification_enabled', 'language']
    search_fields = ['user__user__username']
    list_editable = ['calculation_method', 'juristic_method', 'notification_enabled', 'language']

