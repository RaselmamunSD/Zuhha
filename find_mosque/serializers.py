from rest_framework import serializers
from .models import Mosque, MosqueImage
from locations.models import City, Country


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
            'id', 'name', 'contact_person', 'city', 'city_name', 'country_name', 'address', 'additional_info',
            'latitude', 'longitude', 'phone', 'email', 'website',
            'has_parking', 'has_wudu_area', 'has_women_facility',
            'has_jumuah', 'has_quran_classes', 'has_ramadan_iftar',
            'capacity', 
            'fajr_beginning', 'sunrise', 'dhuhr_beginning', 'asr_beginning', 
            'maghrib_sunset', 'isha_beginning',
            'fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah',
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


class RegisterMosqueSerializer(serializers.Serializer):
    mosque_name = serializers.CharField(max_length=200)
    contact_person = serializers.CharField(max_length=120, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField()
    area = serializers.CharField(max_length=100)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    facilities = serializers.ListField(child=serializers.CharField(), required=False)
    additional_info = serializers.CharField(required=False, allow_blank=True)
    prayer_times = serializers.DictField(required=False)

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

        def time_or_none(value):
            return value if value not in ['', None] else None

        return Mosque.objects.create(
            name=validated_data['mosque_name'],
            contact_person=validated_data.get('contact_person', ''),
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

