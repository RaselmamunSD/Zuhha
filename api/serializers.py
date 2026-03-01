from rest_framework import serializers
from prayer_times.models import PrayerTime
from .models import Location, UserPreference, SupportMessage

class PrayerTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerTime
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = '__all__'


class SupportMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'is_resolved', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_resolved', 'created_at', 'updated_at']
