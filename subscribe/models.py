from django.db import models
from django.contrib.auth.models import User


class Subscription(models.Model):
    """
    Model for email/notification subscriptions.
    """
    NOTIFICATION_METHODS = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
    ]

    SUBSCRIPTION_TYPES = [
        ('daily', 'Daily Prayer Times'),
        ('weekly', 'Weekly Summary'),
        ('monthly', 'Monthly Calendar'),
        ('events', 'Islamic Events'),
        ('all', 'All Notifications'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    notification_method = models.CharField(max_length=20, choices=NOTIFICATION_METHODS, default='whatsapp')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES, default='daily')
    city = models.ForeignKey('locations.City', on_delete=models.CASCADE, null=True, blank=True, related_name='subscriptions')
    selected_mosques = models.ManyToManyField('find_mosque.Mosque', blank=True, related_name='subscriptions')
    duration_days = models.PositiveSmallIntegerField(default=30)
    notification_minutes_before = models.PositiveSmallIntegerField(default=10)
    selected_prayers = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    activation_token = models.CharField(max_length=100, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.email} - {self.subscription_type}"


class SubscriptionLog(models.Model):
    """
    Log of sent notifications/emails.
    """
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='logs')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    prayer_name = models.CharField(max_length=20, blank=True, help_text="Prayer name (fajr, dhuhr, asr, maghrib, isha)")
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ], default='pending')

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Subscription Log'
        verbose_name_plural = 'Subscription Logs'

    def __str__(self):
        return f"{self.subscription.email} - {self.sent_at}"
