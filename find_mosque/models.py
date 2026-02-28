from django.db import models


class Mosque(models.Model):
    """
    Model for mosque/masjid information.
    """
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=120, blank=True)
    city = models.ForeignKey('locations.City', on_delete=models.CASCADE, related_name='mosques')
    address = models.TextField()
    additional_info = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Facilities
    has_parking = models.BooleanField(default=False)
    has_wudu_area = models.BooleanField(default=True)
    has_women_facility = models.BooleanField(default=False)
    has_jumuah = models.BooleanField(default=True)
    has_quran_classes = models.BooleanField(default=False)
    has_ramadan_iftar = models.BooleanField(default=False)
    
    # Capacity
    capacity = models.IntegerField(default=0, help_text="Capacity of the main prayer hall")
    
    # Prayer Times - Beginning (Azan/Start Time)
    fajr_beginning = models.TimeField(null=True, blank=True, help_text="Fajr beginning time")
    sunrise = models.TimeField(null=True, blank=True, help_text="Sunrise time")
    dhuhr_beginning = models.TimeField(null=True, blank=True, help_text="Dhuhr beginning time")
    asr_beginning = models.TimeField(null=True, blank=True, help_text="Asr beginning time")
    maghrib_sunset = models.TimeField(null=True, blank=True, help_text="Maghrib sunset time")
    isha_beginning = models.TimeField(null=True, blank=True, help_text="Isha beginning time")
    
    # Prayer Times - Jamaah (Congregation Time)
    fajr_jamaah = models.TimeField(null=True, blank=True, help_text="Fajr jamaah time")
    dhuhr_jamaah = models.TimeField(null=True, blank=True, help_text="Dhuhr jamaah time")
    asr_jamaah = models.TimeField(null=True, blank=True, help_text="Asr jamaah time")
    maghrib_jamaah = models.TimeField(null=True, blank=True, help_text="Maghrib jamaah time")
    isha_jamaah = models.TimeField(null=True, blank=True, help_text="Isha jamaah time")
    jumuah_khutbah = models.TimeField(null=True, blank=True, help_text="Jumuah khutbah time")
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Mosque'
        verbose_name_plural = 'Mosques'

    def __str__(self):
        return self.name


class MosqueImage(models.Model):
    """
    Model for mosque images.
    """
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='mosque_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']
        verbose_name = 'Mosque Image'
        verbose_name_plural = 'Mosque Images'

    def __str__(self):
        return f"{self.mosque.name} - Image"
