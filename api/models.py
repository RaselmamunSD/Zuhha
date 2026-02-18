from django.db import models


class Location(models.Model):
    """
    General location model for quick lookups.
    """
    name = models.CharField(max_length=100)
    city = models.ForeignKey('locations.City', on_delete=models.CASCADE, null=True, blank=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_type = models.CharField(max_length=20, choices=[
        ('mosque', 'Mosque'),
        ('user_location', 'User Location'),
        ('other', 'Other'),
    ], default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    def __str__(self):
        return self.name


class UserPreference(models.Model):
    """
    User preferences for prayer times.
    """
    user = models.OneToOneField('users.UserProfile', on_delete=models.CASCADE, related_name='preferences')
    calculation_method = models.CharField(max_length=20, default='mw')
    juristic_method = models.CharField(max_length=10, default='shafii')
    notification_enabled = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"Preferences for {self.user.user.username}"

