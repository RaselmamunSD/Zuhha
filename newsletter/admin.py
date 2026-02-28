from django.contrib import admin
from django.utils.html import format_html
from .models import NewsletterSubscription, NewsletterLog


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'is_verified', 'prayer_updates', 'important_announcements', 'subscribed_at']
    list_filter = ['is_active', 'is_verified', 'prayer_updates', 'important_announcements', 'subscribed_at']
    search_fields = ['email']
    list_editable = ['is_active', 'prayer_updates', 'important_announcements']
    readonly_fields = ['verification_code', 'subscribed_at', 'unsubscribed_at', 'updated_at']
    fieldsets = (
        ('Email Information', {
            'fields': ('email', 'verification_code', 'is_verified')
        }),
        ('Subscription Status', {
            'fields': ('is_active', 'subscribed_at', 'unsubscribed_at')
        }),
        ('Preferences', {
            'fields': ('prayer_updates', 'important_announcements')
        }),
        ('Timestamps', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-subscribed_at']

    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_verified']

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscription(s) marked as active.')

    mark_as_active.short_description = "✓ Mark selected as active"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscription(s) marked as inactive.')

    mark_as_inactive.short_description = "✗ Mark selected as inactive"

    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} subscription(s) marked as verified.')

    mark_as_verified.short_description = "✓ Mark selected as verified"


@admin.register(NewsletterLog)
class NewsletterLogAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'subject', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['subscription__email', 'subject', 'message']
    readonly_fields = ['id', 'subscription', 'subject', 'message', 'created_at', 'sent_at', 'error_message']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        # Newsletter logs are created programmatically, not manually
        return False

