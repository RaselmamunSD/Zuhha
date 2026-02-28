from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Subscription, SubscriptionLog
from push_notification.tasks import send_whatsapp_notification


def send_test_notification(modeladmin, request, queryset):
    """
    Admin action to send test notifications to selected subscriptions.
    Queues notification tasks (WhatsApp/Email) for each selected subscriber.
    """
    whatsapp_count = 0
    email_count = 0
    failed_count = 0
    
    for subscription in queryset:
        try:
            if subscription.notification_method == 'whatsapp':
                if subscription.phone:
                    # Queue WhatsApp notification task
                    test_message = f"🔔 Test notification for {subscription.email}\n\nPrayers: {', '.join(subscription.selected_prayers or [])}\nReminder: {subscription.notification_minutes_before} minutes before"
                    send_whatsapp_notification.delay(
                        notification_id=subscription.id,
                        message=test_message
                    )
                    whatsapp_count += 1
                else:
                    failed_count += 1
                    
            elif subscription.notification_method == 'email':
                if subscription.email:
                    # Queue email notification (can be implemented in tasks)
                    # For now, log it
                    from django.core.mail import send_mail
                    from django.template.loader import render_to_string
                    
                    email_subject = "Test: Prayer Times Notification"
                    email_message = f"This is a test notification for your prayer times subscription.\n\nSelected Prayers: {', '.join(subscription.selected_prayers or [])}\nReminder: {subscription.notification_minutes_before} minutes before prayer time"
                    
                    send_mail(
                        email_subject,
                        email_message,
                        'noreply@salahtime.local',
                        [subscription.email],
                        fail_silently=True
                    )
                    email_count += 1
                else:
                    failed_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Error queuing notification for {subscription.email}: {e}")
    
    # Build success message
    message_parts = []
    if whatsapp_count > 0:
        message_parts.append(f"{whatsapp_count} WhatsApp notification(s) queued")
    if email_count > 0:
        message_parts.append(f"{email_count} email notification(s) queued")
    if failed_count > 0:
        message_parts.append(f"{failed_count} failed (missing phone/email)")
    
    if message_parts:
        modeladmin.message_user(
            request,
            f"Successfully queued notifications: {' | '.join(message_parts)}",
            messages.SUCCESS
        )
    else:
        modeladmin.message_user(
            request,
            "No notifications were queued.",
            messages.WARNING
        )


send_test_notification.short_description = "📤 Send Test Notification"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'phone', 'notification_method', 'subscription_type', 'city',
        'duration_days', 'notification_minutes_before', 'is_active',
        'activated_at', 'unsubscribed_at', 'created_at'
    ]
    list_filter = ['notification_method', 'subscription_type', 'is_active', 'city__country', 'city']
    search_fields = ['email', 'phone', 'activation_token']
    list_editable = ['is_active', 'subscription_type', 'notification_minutes_before']
    readonly_fields = ['activation_token', 'activated_at', 'unsubscribed_at', 'created_at', 'updated_at']
    filter_horizontal = ('selected_mosques',)
    actions = [send_test_notification]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email', 'phone')
        }),
        ('Subscription Details', {
            'fields': (
                'notification_method',
                'subscription_type',
                'city',
                'selected_mosques',
                'selected_prayers',
                'duration_days',
                'notification_minutes_before',
                'is_active'
            )
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

