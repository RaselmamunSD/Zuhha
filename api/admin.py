from django.contrib import admin
from .models import Location, UserPreference, SupportMessage, SiteSettings
from unfold.admin import ModelAdmin

@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ['name', 'city', 'location_type', 'latitude', 'longitude', 'created_at']
    list_filter = ['location_type', 'city__country']
    search_fields = ['name', 'address', 'city__name']
    list_editable = ['location_type']


@admin.register(UserPreference)
class UserPreferenceAdmin(ModelAdmin):
    list_display = ['user', 'calculation_method', 'juristic_method', 'notification_enabled', 'language', 'created_at']
    list_filter = ['calculation_method', 'juristic_method', 'notification_enabled', 'language']
    search_fields = ['user__user__username']
    list_editable = ['calculation_method', 'juristic_method', 'notification_enabled', 'language']


@admin.register(SupportMessage)
class SupportMessageAdmin(ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_resolved']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at', 'updated_at']


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    fields = ['registration_whatsapp_number']
    list_display = ['registration_whatsapp_number']
    list_display_links = ['registration_whatsapp_number']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Ensure the singleton always exists before showing the list
        SiteSettings.get()
        return super().changelist_view(request, extra_context)

