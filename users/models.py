from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile with additional preferences.
    """
    PRAYER_CALCULATION_METHODS = [
        ('mw', 'Muslim World League'),
        ('egypt', 'Egyptian General Authority'),
        ('karachi', 'University of Karachi'),
        ('kuwait', 'Kuwait'),
        ('qatar', 'Qatar'),
        ('singapore', 'Singapore'),
        ('turkey', 'Turkish Diyanet'),
        ('tehran', 'Institute of Geophysics - Tehran'),
        ('isna', 'Islamic Society of North America'),
    ]
    
    JURISTIC_METHODS = [
        ('shafii', 'Shafi\'i'),
        ('hanafi', 'Hanafi'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    # Location preferences
    current_city = models.ForeignKey('locations.City', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_profiles')
    
    # Prayer calculation preferences
    calculation_method = models.CharField(max_length=20, choices=PRAYER_CALCULATION_METHODS, default='mw')
    juristic_method = models.CharField(max_length=10, choices=JURISTIC_METHODS, default='shafii')
    high_latitude_adjustment = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('middle_of_night', 'Middle of Night'),
        ('seventy_one_minute', '71.7 Minutes'),
        ('seventy_five_minute', '75 Minutes'),
        ('angle_based', 'Angle-Based'),
    ], default='none')
    
    # Notification preferences
    fajr_notification = models.BooleanField(default=True)
    dhuhr_notification = models.BooleanField(default=True)
    asr_notification = models.BooleanField(default=True)
    maghrib_notification = models.BooleanField(default=True)
    isha_notification = models.BooleanField(default=True)
    notification_minutes_before = models.IntegerField(default=10, help_text="Minutes before prayer to send notification")
    
    # Account settings
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en')
    theme = models.CharField(max_length=20, default='light', choices=[('light', 'Light'), ('dark', 'Dark'), ('sepia', 'Sepia')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile instance when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile instance when User is saved."""
    instance.profile.save()


class UserLocation(models.Model):
    """
    Model to store saved locations for users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_locations')
    city = models.ForeignKey('locations.City', on_delete=models.CASCADE)
    label = models.CharField(max_length=50, blank=True, help_text="e.g., Home, Work, Mosque")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'User Location'
        verbose_name_plural = 'User Locations'

    def __str__(self):
        return f"{self.user.username} - {self.city.name}"
