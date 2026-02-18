from django.contrib import admin
from .models import Subscription, SubscriptionLog


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'subscription_type', 'city', 'is_active', 'activation_token', 'activated_at', 'unsubscribed_at', 'created_at']
    list_filter = ['subscription_type', 'is_active', 'city__country', 'city']
    search_fields = ['email', 'phone', 'activation_token']
    list_editable = ['is_active', 'subscription_type']
    readonly_fields = ['activation_token', 'activated_at', 'unsubscribed_at', 'created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email', 'phone')
        }),
        ('Subscription Details', {
            'fields': ('subscription_type', 'city', 'is_active')
        }),
        ('Activation', {
            'fields': ('activation_token', 'activated_at', 'unsubscribed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubscriptionLog)
class SubscriptionLogAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'subject', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['subscription__email', 'subject', 'message']
    readonly_fields = ['sent_at']
    ordering = ['-sent_at']

