from django.db import models
import uuid


class NewsletterSubscription(models.Model):
    """
    Model for storing newsletter email subscriptions.
    Users can subscribe to receive prayer time updates and announcements.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, help_text="Email address for newsletter")
    is_active = models.BooleanField(default=True, help_text="Whether the subscription is active")
    is_verified = models.BooleanField(default=False, help_text="Whether email has been verified")
    verification_code = models.CharField(max_length=50, blank=True, help_text="Code for email verification")
    
    # Preferences
    prayer_updates = models.BooleanField(default=True, help_text="Receive prayer time updates")
    important_announcements = models.BooleanField(default=True, help_text="Receive important announcements")
    
    # Timestamps
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscription'
        verbose_name_plural = 'Newsletter Subscriptions'

    def __str__(self):
        return self.email


class NewsletterLog(models.Model):
    """
    Log of newsletter emails sent.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(NewsletterSubscription, on_delete=models.CASCADE, related_name='newsletter_logs')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    error_message = models.TextField(blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter Log'
        verbose_name_plural = 'Newsletter Logs'

    def __str__(self):
        return f"{self.subject} - {self.subscription.email}"

