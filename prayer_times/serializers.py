from rest_framework import serializers
from .models import PrayerTime, MonthlyPrayerTime, PrayerTimeAdjustment


class PrayerTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerTime
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MonthlyPrayerTimeSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    country_name = serializers.CharField(source='city.country.name', read_only=True)
    
    class Meta:
        model = MonthlyPrayerTime
        fields = [
            'id', 'city', 'city_name', 'country_name', 'year', 'month', 'day',
            'fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PrayerTimeAdjustmentSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    class Meta:
        model = PrayerTimeAdjustment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

