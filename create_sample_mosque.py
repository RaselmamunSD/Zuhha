"""
Script to create a sample mosque with prayer times for testing.
Run this script from Django shell or as a management command.
"""

import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from find_mosque.models import Mosque
from locations.models import City, Country

# Get or create Bangladesh and Dhaka
country, _ = Country.objects.get_or_create(
    name='Bangladesh',
    defaults={
        'code': 'BGD',
        'phone_code': '+880',
        'currency': 'BDT',
        'currency_symbol': '৳'
    }
)

city, _ = City.objects.get_or_create(
    name='Dhaka',
    country=country,
    defaults={
        'latitude': 23.8103,
        'longitude': 90.4125,
        'timezone': 'Asia/Dhaka',
        'elevation': 4,
        'is_capital': True
    }
)

# Create Gulshan Central Mosque with prayer times
mosque, created = Mosque.objects.update_or_create(
    name='Gulshan Central Mosque',
    defaults={
        'city': city,
        'address': 'Gulshan Avenue, Dhaka 1212, Bangladesh',
        'latitude': 23.7925,
        'longitude': 90.4078,
        'phone': '+880 2-8833391',
        'email': 'info@gulshanmosque.bd',
        'has_parking': True,
        'has_wudu_area': True,
        'has_women_facility': True,
        'has_jumuah': True,
        'has_quran_classes': True,
        'has_ramadan_iftar': True,
        'capacity': 500,
        
        # Prayer Times - Beginning (Azan)
        'fajr_beginning': time(5, 30),
        'sunrise': time(7, 12),
        'dhuhr_beginning': time(12, 15),
        'asr_beginning': time(15, 30),
        'maghrib_sunset': time(17, 58),
        'isha_beginning': time(19, 10),
        
        # Prayer Times - Jamaah
        'fajr_jamaah': time(5, 45),
        'dhuhr_jamaah': time(12, 30),
        'asr_jamaah': time(15, 45),
        'maghrib_jamaah': time(18, 3),
        'isha_jamaah': time(19, 25),
        'jumuah_khutbah': time(13, 0),
        
        'is_verified': True,
        'is_active': True,
    }
)

if created:
    print(f"✅ Created mosque: {mosque.name}")
else:
    print(f"✅ Updated mosque: {mosque.name}")

print(f"   ID: {mosque.id}")
print(f"   City: {mosque.city.name}")
print(f"   Fajr: {mosque.fajr_beginning} → {mosque.fajr_jamaah}")
print(f"   Dhuhr: {mosque.dhuhr_beginning} → {mosque.dhuhr_jamaah}")
print(f"   Asr: {mosque.asr_beginning} → {mosque.asr_jamaah}")
print(f"   Maghrib: {mosque.maghrib_sunset} → {mosque.maghrib_jamaah}")
print(f"   Isha: {mosque.isha_beginning} → {mosque.isha_jamaah}")
print("\n✅ Sample mosque data created successfully!")
