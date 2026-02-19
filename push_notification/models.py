from django.db import models
from django.contrib.auth.models import User


class WhatsAppNotification(models.Model):
    """
    Model for storing WhatsApp numbers to send prayer time notifications.
    The WhatsApp Number will be given from Django Admin to push notifications.
    """
    NOTIFICATION_TYPES = [
        ('fajr', 'Fajr Prayer'),
        ('dhuhr', 'Dhuhr Prayer'),
        ('asr', 'Asr Prayer'),
        ('maghrib', 'Maghrib Prayer'),
        ('isha', 'Isha Prayer'),
        ('jumuah', 'Jumuah Prayer'),
        ('daily', 'Daily Prayer Times'),
        ('weekly', 'Weekly Summary'),
    ]
    
    LANGUAGES = [
        ('en', 'English'),
        ('bn', 'Bangla'),
        ('ar', 'Arabic'),
        ('ur', 'Urdu'),
    ]
    
    phone_number = models.CharField(max_length=20, unique=True, help_text="WhatsApp phone number with country code")
    country_code = models.CharField(max_length=5, default='+880', help_text="Country code")
    full_phone = models.CharField(max_length=25, blank=True, editable=False)
    
    # User association (optional - can be used without user account)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_notifications')
    
    # Notification preferences
    notification_types = models.JSONField(default=list, help_text="List of notification types to receive")
    language = models.CharField(max_length=10, choices=LANGUAGES, default='en')
    
    # City for prayer times (determines which prayer times to send)
    city = models.ForeignKey('locations.City', on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_subscriptions')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False, help_text="Whether the WhatsApp number is verified")
    verification_code = models.CharField(max_length=10, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timing preferences
    notification_minutes_before = models.IntegerField(default=10, help_text="Minutes before prayer to send notification")
    
    # Admin notes
    admin_notes = models.TextField(blank=True, help_text="Notes added by admin")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'WhatsApp Notification'
        verbose_name_plural = 'WhatsApp Notifications'
    
    def __str__(self):
        return f"WhatsApp: {self.phone_number}"
    
    def save(self, *args, **kwargs):
        # Combine country code and phone number
        if self.country_code and self.phone_number:
            self.full_phone = f"{self.country_code}{self.phone_number.lstrip('0')}"
        super().save(*args, **kwargs)


class WhatsAppNotificationLog(models.Model):
    """
    Log of sent WhatsApp notifications.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    whatsapp = models.ForeignKey(WhatsAppNotification, on_delete=models.CASCADE, related_name='notification_logs')
    message = models.TextField()
    prayer_name = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    twilio_sid = models.CharField(max_length=100, blank=True, help_text="Twilio message SID")
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'WhatsApp Notification Log'
        verbose_name_plural = 'WhatsApp Notification Logs'
    
    def __str__(self):
        return f"{self.whatsapp.phone_number} - {self.status} - {self.sent_at}"

