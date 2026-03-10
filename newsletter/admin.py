from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import NewsletterSubscription, NewsletterCampaign, NewsletterLog
from unfold.admin import ModelAdmin


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(ModelAdmin):
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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return not request.user.groups.filter(name='Imam').exists()

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


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(ModelAdmin):
    list_display = ['subject', 'status', 'total_sent', 'sent_at', 'created_at', 'send_button']
    list_filter = ['status', 'created_at']
    search_fields = ['subject', 'message']
    readonly_fields = ['id', 'status', 'total_sent', 'sent_at', 'created_at', 'updated_at', 'subscriber_count_display']
    fieldsets = (
        ('Campaign', {
            'fields': ('subject', 'message'),
        }),
        ('Status', {
            'fields': ('status', 'total_sent', 'sent_at', 'subscriber_count_display'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    ordering = ['-created_at']
    actions = ['send_campaign_action']

    def has_module_permission(self, request):
        return request.user.is_superuser

    def subscriber_count_display(self, obj):
        count = NewsletterSubscription.objects.filter(is_active=True).count()
        return format_html('<strong>{}</strong> active subscribers will receive this email.', count)
    subscriber_count_display.short_description = 'Recipients'

    def send_button(self, obj):
        if obj.status == 'sent':
            return format_html(
                '<span style="color:#10B981;font-weight:bold;">✓ Sent ({})</span>',
                obj.total_sent
            )
        return format_html(
            '<a class="button" href="{}/send/" style="background:#218E5B;color:white;padding:4px 12px;'
            'border-radius:4px;text-decoration:none;font-size:12px;">Send Now</a>',
            obj.pk
        )
    send_button.short_description = 'Action'
    send_button.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('<uuid:pk>/send/', self.admin_site.admin_view(self.send_campaign_view), name='newsletter_send_campaign'),
        ]
        return custom + urls

    def send_campaign_view(self, request, pk):
        """Admin view to immediately dispatch a campaign."""
        from django.shortcuts import redirect
        from newsletter.tasks import send_newsletter_campaign

        try:
            campaign = NewsletterCampaign.objects.get(pk=pk)
        except NewsletterCampaign.DoesNotExist:
            self.message_user(request, 'Campaign not found.', level=messages.ERROR)
            return redirect('..')

        if campaign.status == 'sent':
            self.message_user(request, f'Campaign "{campaign.subject}" was already sent.', level=messages.WARNING)
            return redirect('../../')

        count = NewsletterSubscription.objects.filter(is_active=True).count()
        if count == 0:
            self.message_user(request, 'No active subscribers found.', level=messages.WARNING)
            return redirect('../../')

        try:
            # Run synchronously so emails are sent immediately without needing Celery worker
            send_newsletter_campaign.apply(args=[str(campaign.pk)])
            self.message_user(
                request,
                f'✓ Campaign "{campaign.subject}" sent to {count} subscriber(s).',
                level=messages.SUCCESS,
            )
        except Exception as exc:
            self.message_user(
                request,
                f'✗ Failed to send campaign: {exc}',
                level=messages.ERROR,
            )

        return redirect('../../')

    def send_campaign_action(self, request, queryset):
        """Admin list action to send selected draft campaigns."""
        from newsletter.tasks import send_newsletter_campaign
        sent = 0
        for campaign in queryset.filter(status='draft'):
            try:
                send_newsletter_campaign.apply(args=[str(campaign.pk)])
                sent += 1
            except Exception as exc:
                self.message_user(request, f'Failed to send "{campaign.subject}": {exc}', level=messages.ERROR)
        if sent:
            self.message_user(request, f'{sent} campaign(s) dispatched.', level=messages.SUCCESS)
        else:
            self.message_user(request, 'No draft campaigns selected.', level=messages.WARNING)
    send_campaign_action.short_description = '📧 Send selected campaigns to all subscribers'


@admin.register(NewsletterLog)
class NewsletterLogAdmin(ModelAdmin):
    list_display = ['subscription', 'subject', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['subscription__email', 'subject', 'message']
    readonly_fields = ['id', 'subscription', 'subject', 'message', 'created_at', 'sent_at', 'error_message']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return not request.user.groups.filter(name='Imam').exists()


