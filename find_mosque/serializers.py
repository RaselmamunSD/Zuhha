from rest_framework import serializers
from .models import Mosque, MosqueImage


class MosqueImageSerializer(serializers.ModelSerializer):
    """Serializer for MosqueImage model."""
    
    class Meta:
        model = MosqueImage
        fields = ['id', 'image', 'caption', 'is_primary', 'created_at']
        read_only_fields = ['created_at']


class MosqueSerializer(serializers.ModelSerializer):
    """Serializer for Mosque model."""
    city_name = serializers.CharField(source='city.name', read_only=True)
    country_name = serializers.CharField(source='city.country.name', read_only=True)
    images = MosqueImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Mosque
        fields = [
            'id', 'name', 'city', 'city_name', 'country_name', 'address',
            'latitude', 'longitude', 'phone', 'email', 'website',
            'has_parking', 'has_wudu_area', 'has_women_facility',
            'has_jumuah', 'has_quran_classes', 'has_ramadan_iftar',
            'capacity', 'fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah',
            'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah',
            'is_verified', 'is_active', 'images',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_verified', 'created_at', 'updated_at']


class MosqueListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views."""
    city_name = serializers.CharField(source='city.name', read_only=True)
    country_name = serializers.CharField(source='city.country.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Mosque
        fields = [
            'id', 'name', 'city_name', 'country_name', 'address',
            'latitude', 'longitude', 'has_jumuah', 'capacity',
            'is_verified', 'primary_image'
        ]
    
    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return self.context['request'].build_absolute_uri(primary.image.url)
        first_image = obj.images.first()
        if first_image:
            return self.context['request'].build_absolute_uri(first_image.image.url)
        return None

