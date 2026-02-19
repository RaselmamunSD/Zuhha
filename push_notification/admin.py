from django.contrib import admin
from .models import WhatsAppNotification, WhatsAppNotificationLog


@admin.register(WhatsAppNotification)
class WhatsAppNotificationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'country_code', 'full_phone', 'user', 'city', 'language', 'is_active', 'is_verified', 'notification_minutes_before', 'created_at']
    list_filter = ['is_active', 'is_verified', 'language', 'city__country', 'notification_types']
    search_fields = ['phone_number', 'full_phone', 'user__username', 'user__email', 'admin_notes']
    list_editable = ['is_active', 'is_verified', 'notification_minutes_before']
    readonly_fields = ['full_phone', 'created_at', 'updated_at', 'verified_at']
    
    fieldsets = (
        ('Phone Information', {
            'fields': ('phone_number', 'country_code', 'full_phone')
        }),
        ('User Association', {
            'fields': ('user',)
        }),
        ('Notification Settings', {
            'fields': ('notification_types', 'language', 'city', 'notification_minutes_before')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'verification_code', 'verified_at')
        }),
        ('Admin', {
            'fields': ('admin_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WhatsAppNotificationLog)
class WhatsAppNotificationLogAdmin(admin.ModelAdmin):
    list_display = ['whatsapp', 'prayer_name', 'status', 'sent_at', 'delivered_at']
    list_filter = ['status', 'prayer_name', 'sent_at']
    search_fields = ['whatsapp__phone_number', 'twilio_sid', 'error_message']
    readonly_fields = ['whatsapp', 'message', 'prayer_name', 'status', 'twilio_sid', 'error_message', 'sent_at', 'delivered_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

