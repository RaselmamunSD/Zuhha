from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class PrayerTime(models.Model):
    """
    Model representing prayer times for a specific date and location.
    """
    date = models.DateField(unique=True)
    fajr = models.TimeField()
    sunrise = models.TimeField()
    dhuhr = models.TimeField()
    asr = models.TimeField()
    maghrib = models.TimeField()
    isha = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Prayer Time'
        verbose_name_plural = 'Prayer Times'

    def __str__(self):
        return f"Prayer Times for {self.date}"


class MonthlyPrayerTime(models.Model):
    """
    Model representing monthly prayer times for a specific location.
    """
    city = models.ForeignKey('locations.City', on_delete=models.CASCADE, related_name='monthly_prayer_times')
    year = models.IntegerField(validators=[MinValueValidator(2020), MaxValueValidator(2100)])
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    day = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    fajr = models.TimeField()
    sunrise = models.TimeField()
    dhuhr = models.TimeField()
    asr = models.TimeField()
    maghrib = models.TimeField()
    isha = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['year', 'month', 'day']
        unique_together = ['city', 'year', 'month', 'day']
        verbose_name = 'Monthly Prayer Time'
        verbose_name_plural = 'Monthly Prayer Times'

    def __str__(self):
        return f"{self.city.name} - {self.year}-{self.month:02d}-{self.day:02d}"


class PrayerTimeAdjustment(models.Model):
    """
    Model for adjusting prayer times manually if needed.
    """
    prayer_name = models.CharField(max_length=20, choices=[
        ('fajr', 'Fajr'),
        ('sunrise', 'Sunrise'),
        ('dhuhr', 'Dhuhr'),
        ('asr', 'Asr'),
        ('maghrib', 'Maghrib'),
        ('isha', 'Isha'),
    ])
    adjustment_minutes = models.IntegerField(
        default=0,
        help_text="Minutes to add (positive) or subtract (negative) from calculated time"
    )
    city = models.ForeignKey('locations.City', on_delete=models.CASCADE, related_name='adjustments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prayer Time Adjustment'
        verbose_name_plural = 'Prayer Time Adjustments'

    def __str__(self):
        return f"{self.prayer_name}: {self.adjustment_minutes} min for {self.city.name}"
