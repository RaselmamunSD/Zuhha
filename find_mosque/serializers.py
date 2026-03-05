import json
import io
import requests
from PIL import Image

from rest_framework import serializers
from django.core.files.base import ContentFile
from django.conf import settings
from .models import Mosque, MosqueImage, FavoriteMosque, MosqueMonthlyPrayerTime
from locations.models import City, Country


def build_image_url(request, image_url_path):
    """
    Build absolute URL for images using API_BASE_URL if available.
    Falls back to request.build_absolute_uri() if API_BASE_URL is not set.
    """
    api_base_url = getattr(settings, 'API_BASE_URL', None)
    if api_base_url:
        image_path = image_url_path.lstrip('/')
        return f"{api_base_url.rstrip('/')}/{image_path}"
    else:
        return request.build_absolute_uri(image_url_path)


class FileOrURLField(serializers.Field):
    """Custom field that accepts both file uploads and URL strings."""
    
    def to_internal_value(self, data):
        # If it's a string (URL), return as is
        if isinstance(data, str):
            return data.strip() if data.strip() else None
        
        # If it's a file object, validate and return
        if hasattr(data, 'read'):
            return data
        
        # If it's None or empty, return None
        if not data:
            return None
        
        self.fail('invalid', value=data)
    
    def to_representation(self, value):
        return value


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
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Mosque
        fields = [
            'id', 'name', 'contact_person', 'city', 'city_name', 'country_name', 'address', 'additional_info',
            'latitude', 'longitude', 'phone', 'email', 'website',
            'has_parking', 'has_wudu_area', 'has_women_facility',
            'has_jumuah', 'has_quran_classes', 'has_ramadan_iftar',
            'capacity', 
            'fajr_beginning', 'sunrise', 'dhuhr_beginning', 'asr_beginning', 
            'maghrib_sunset', 'isha_beginning',
            'fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah',
            'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah',
            'is_verified', 'is_active', 'created_by', 'images',
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
            'id', 'name', 'contact_person', 'city_name', 'country_name', 'address',
            'phone', 'email', 'latitude', 'longitude', 'has_jumuah', 'capacity',
            'is_verified', 'primary_image'
        ]
    
    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return build_image_url(self.context['request'], primary.image.url)
        first_image = obj.images.first()
        if first_image:
            return build_image_url(self.context['request'], first_image.image.url)
        return None


class RegisterMosqueSerializer(serializers.Serializer):
    mosque_name = serializers.CharField(max_length=200)
    contact_person = serializers.CharField(max_length=120, required=False, allow_blank=True)
    email = serializers.CharField(max_length=254, required=False, allow_blank=True)  # Changed from EmailField to CharField for flexibility
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField()
    area = serializers.CharField(max_length=100)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    facilities = serializers.ListField(child=serializers.CharField(), required=False)
    additional_info = serializers.CharField(required=False, allow_blank=True)
    prayer_times = serializers.DictField(required=False)
    prayer_timetable_image = FileOrURLField(required=False, allow_null=True)

    def validate_email(self, value):
        """Validate email if provided."""
        if value and '@' not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value

    def validate_facilities(self, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (TypeError, json.JSONDecodeError):
                return []
            return []
        return value

    def validate_prayer_times(self, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except (TypeError, json.JSONDecodeError):
                return {}
            return {}
        return value

    def _download_image_from_url(self, image_url):
        """Download image from URL and return a file-like object."""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Validate that the response is an image
            if 'image' not in response.headers.get('content-type', ''):
                return None
            
            # Open the image to validate it's a proper image file
            img = Image.open(io.BytesIO(response.content))
            
            # Get filename from URL or use a default
            filename = image_url.split('/')[-1] or 'prayer_timetable.png'
            
            # Create a file-like object
            img_file = ContentFile(response.content, name=filename)
            return img_file
        except Exception as e:
            print(f"Error downloading image from URL: {e}")
            return None

    def create(self, validated_data):
        country = Country.objects.filter(code='BGD').first() or Country.objects.filter(name__iexact='Bangladesh').first()
        if not country:
            country = Country.objects.create(
                name='Bangladesh',
                code='BGD',
                phone_code='+880',
                currency='BDT',
                currency_symbol='৳'
            )

        area_name = validated_data.get('area', 'Dhaka').strip() or 'Dhaka'
        latitude = validated_data.get('latitude')
        longitude = validated_data.get('longitude')

        if latitude is not None:
            latitude = round(float(latitude), 6)
        if longitude is not None:
            longitude = round(float(longitude), 6)

        city = City.objects.filter(name__iexact=area_name, country=country).first()
        if not city:
            city = City.objects.create(
                name=area_name,
                country=country,
                latitude=latitude if latitude is not None else 23.8103,
                longitude=longitude if longitude is not None else 90.4125,
                timezone='Asia/Dhaka'
            )

        facilities = validated_data.get('facilities', [])
        prayer_times = validated_data.get('prayer_times', {})
        prayer_timetable_image = validated_data.get('prayer_timetable_image')

        def time_or_none(value):
            return value if value not in ['', None] else None

        request = self.context.get('request')
        created_by = None
        if request and request.user and request.user.is_authenticated:
            created_by = request.user

        mosque = Mosque.objects.create(
            name=validated_data['mosque_name'],
            contact_person=validated_data.get('contact_person', ''),
            created_by=created_by,
            city=city,
            address=validated_data['address'],
            additional_info=validated_data.get('additional_info', ''),
            latitude=latitude,
            longitude=longitude,
            phone=validated_data['phone'],
            email=validated_data.get('email', ''),
            has_wudu_area='wudu' in facilities,
            has_parking='parking' in facilities,
            has_women_facility='ladies' in facilities,
            has_quran_classes='library' in facilities,
            fajr_beginning=time_or_none(prayer_times.get('fajr_beginning')),
            sunrise=time_or_none(prayer_times.get('sunrise')),
            dhuhr_beginning=time_or_none(prayer_times.get('dhuhr_beginning')),
            asr_beginning=time_or_none(prayer_times.get('asr_beginning')),
            maghrib_sunset=time_or_none(prayer_times.get('maghrib_sunset')),
            isha_beginning=time_or_none(prayer_times.get('isha_beginning')),
            fajr_jamaah=time_or_none(prayer_times.get('fajr_jamaah')),
            dhuhr_jamaah=time_or_none(prayer_times.get('dhuhr_jamaah')),
            asr_jamaah=time_or_none(prayer_times.get('asr_jamaah')),
            maghrib_jamaah=time_or_none(prayer_times.get('maghrib_jamaah')),
            isha_jamaah=time_or_none(prayer_times.get('isha_jamaah')),
            is_verified=False,
            is_active=True,
        )

        if prayer_timetable_image:
            image_file = None
            
            # Check if it's a string (URL) or a file object
            if isinstance(prayer_timetable_image, str):
                # It's a URL string, download it
                image_file = self._download_image_from_url(prayer_timetable_image)
            else:
                # It's already a file object
                image_file = prayer_timetable_image
            
            if image_file:
                MosqueImage.objects.create(
                    mosque=mosque,
                    image=image_file,
                    caption='Prayer timetable image',
                    is_primary=True,
                )

        return mosque


class FavoriteMosqueSerializer(serializers.ModelSerializer):
    """Serializer for user's favorite mosques."""
    mosque = MosqueListSerializer(read_only=True)
    mosque_id = serializers.PrimaryKeyRelatedField(
        source='mosque', queryset=Mosque.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = FavoriteMosque
        fields = ['id', 'user', 'mosque', 'mosque_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'mosque']


class ImamMosqueUpsertSerializer(serializers.ModelSerializer):
    primary_image_url = serializers.SerializerMethodField()

    def get_primary_image_url(self, obj):
        image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if not image:
            return None
        request = self.context.get('request')
        if request:
            return build_image_url(request, image.image.url)
        return image.image.url

    class Meta:
        model = Mosque
        fields = [
            'id',
            'name',
            'contact_person',
            'city',
            'address',
            'additional_info',
            'latitude',
            'longitude',
            'phone',
            'email',
            'website',
            'has_parking',
            'has_wudu_area',
            'has_women_facility',
            'has_jumuah',
            'has_quran_classes',
            'has_ramadan_iftar',
            'capacity',
            'fajr_beginning',
            'sunrise',
            'dhuhr_beginning',
            'asr_beginning',
            'maghrib_sunset',
            'isha_beginning',
            'fajr_jamaah',
            'dhuhr_jamaah',
            'asr_jamaah',
            'maghrib_jamaah',
            'isha_jamaah',
            'jumuah_khutbah',
            'is_active',
            'primary_image_url',
        ]


class MosqueMonthlyPrayerTimeSerializer(serializers.ModelSerializer):
    mosque_name = serializers.CharField(source='mosque.name', read_only=True)

    class Meta:
        model = MosqueMonthlyPrayerTime
        fields = [
            'id',
            'mosque',
            'mosque_name',
            'year',
            'month',
            'day',
            'fajr_adhan',
            'fajr_iqamah',
            'sunrise',
            'dhuhr_adhan',
            'dhuhr_iqamah',
            'asr_adhan',
            'asr_iqamah',
            'maghrib_adhan',
            'maghrib_iqamah',
            'isha_adhan',
            'isha_iqamah',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'mosque_name']
        extra_kwargs = {
            'mosque': {'required': False},
            'year': {'required': False},
            'month': {'required': False},
        }


class MosqueMonthlyPrayerTimeBulkSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2020, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    entries = MosqueMonthlyPrayerTimeSerializer(many=True)

